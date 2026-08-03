"""Application service and canonical result assembly."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Protocol

from serpscrap.models import FailureRecord, SearchReport, SearchRequest
from serpscrap.result_normalizer import normalize_result_url, relevance_for_rank


class SearchRunner(Protocol):
    """Infrastructure boundary implemented by the legacy-compatible core."""

    def run(self, config: dict[str, Any]) -> Any: ...


def _as_utc(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class SearchApplication:
    """Run a search and expose no ORM or browser values at its boundary."""

    def __init__(
        self,
        runner: SearchRunner | None = None,
        url_scraper_factory: Callable[[dict[str, Any]], Any] | None = None,
    ) -> None:
        self._legacy_default = runner is None
        if runner is None:
            from scrapcore.core import Core

            runner = Core()
        if url_scraper_factory is None:
            from serpscrap.urlscrape import UrlScrape

            url_scraper_factory = UrlScrape
        self.runner = runner
        self.url_scraper_factory = url_scraper_factory

    def execute(self, request: SearchRequest) -> SearchReport:
        config = request.to_config()
        configured_engines = tuple(config.get("search_engines") or ("google",))
        if self._legacy_default and configured_engines != ("google",):
            from serpscrap.plugins.searchengines.multi import MultiEngineRunner

            return MultiEngineRunner().execute(request)
        search = self.runner.run(config)
        query_order = {query: index for index, query in enumerate(request.queries)}
        serps = sorted(
            search.serps,
            key=lambda serp: (
                query_order.get(serp.query, len(query_order)),
                int(serp.page_number or 0),
                str(serp.search_engine_name or ""),
            ),
        )

        results: list[dict[str, Any]] = []
        related: list[dict[str, Any]] = []
        failures: list[FailureRecord] = []
        for serp in serps:
            if serp.status != "successful":
                category, separator, message = str(serp.status or "failure").partition(": ")
                failures.append(
                    FailureRecord(
                        query=serp.query,
                        search_engine=serp.search_engine_name,
                        page_number=int(serp.page_number or 0),
                        url=getattr(serp, "failure_url", None),
                        category=category,
                        message=message if separator else category,
                        retryable=bool(getattr(serp, "failure_retryable", False)),
                        correlation_id=getattr(serp, "correlation_id", None),
                        attempt_count=int(getattr(serp, "attempt_count", 1)),
                    )
                )
                continue

            for keyword in sorted(
                serp.related_keywords, key=lambda item: (int(item.rank or 0), item.keyword or "")
            ):
                related.append({"keyword": keyword.keyword, "rank": keyword.rank})
            for link in sorted(
                serp.links,
                key=lambda item: (str(item.link_type or ""), int(item.rank or 0), item.link or ""),
            ):
                url_info = normalize_result_url(link.link, link.link_type)
                results.append(
                    {
                        "query_num_results_total": serp.num_results_for_query or "",
                        "query_num_results_page": int(serp.num_results or 0),
                        "query_page_number": int(serp.page_number or 0),
                        "query": serp.query,
                        "serp_rank": int(link.rank or 0),
                        "serp_type": link.link_type,
                        "serp_url": url_info["canonical_url"],
                        "canonical_url": url_info["canonical_url"],
                        "source_url": url_info["source_url"],
                        "result_kind": url_info["result_kind"],
                        "relevance": relevance_for_rank(int(link.rank or 0)),
                        "serp_rating": link.rating,
                        "serp_title": link.title,
                        "serp_domain": link.domain,
                        "serp_visible_link": link.visible_link,
                        "serp_snippet": link.snippet,
                        "serp_sitelinks": link.sitelinks,
                        "serp_source": getattr(link, "source", None),
                        "serp_date": getattr(link, "published_at", None),
                        "serp_price": getattr(link, "price", None),
                        "serp_merchant": getattr(link, "merchant", None),
                        "serp_duration": getattr(link, "duration", None),
                        "serp_image_url": getattr(link, "image_url", None),
                        "serp_thumbnail_url": getattr(link, "thumbnail_url", None),
                        "screenshot": getattr(serp, "screenshot", None),
                        "search_engine": str(serp.search_engine_name or "google"),
                        "country_code": str(config.get("country_code", "DE")).upper(),
                    }
                )

        for message in getattr(search, "persistence_failures", []):
            failures.append(
                FailureRecord(
                    query="",
                    search_engine="",
                    page_number=0,
                    url=None,
                    category="persistence",
                    message=message,
                    retryable=True,
                )
            )

        if config.get("scrape_urls"):
            url_scraper = self.url_scraper_factory(config)
            for row in results:
                if row["serp_url"]:
                    row.update(url_scraper.scrap_url(row["serp_url"]))

        return SearchReport(
            results=results,
            related_keywords=related,
            failures=failures,
            started_at=_as_utc(search.started_searching),
            stopped_at=_as_utc(search.stopped_searching),
        )
