"""Comfortable public SerpScrap API."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from serpscrap.application import SearchApplication
from serpscrap.config import Config
from serpscrap.models import SearchReport, SearchRequest
from serpscrap.output import JsonResultWriter, normalize_json_path
from serpscrap.urlscrape import UrlScrape


class SerpScrap:
    """Run independent searches and return JSON-compatible dictionaries."""

    def __init__(
        self,
        application: SearchApplication | None = None,
        writer: JsonResultWriter | None = None,
    ) -> None:
        self.application = application or SearchApplication()
        self.writer = writer or JsonResultWriter()
        self.serp_query: list[str] | None = None
        self.config: dict[str, Any] | None = None
        self.results: list[dict[str, Any]] = []
        self.related: list[dict[str, Any]] = []
        self.last_report: SearchReport | None = None

    def search(
        self,
        keywords: str | Iterable[str],
        *,
        config: Config | Mapping[str, Any] | None = None,
        pages: int | None = None,
        workers: int | None = None,
        visible: bool | None = None,
        screenshots: bool | None = None,
        scrape_urls: bool | None = None,
        output: str | Path | None = None,
        overwrite: bool = False,
        **options: Any,
    ) -> list[dict[str, Any]]:
        """Execute one search request with no mandatory initialization step."""

        friendly_options = dict(options)
        if pages is not None:
            friendly_options["num_pages_for_keyword"] = pages
        if workers is not None:
            friendly_options["num_workers"] = workers
        if visible is not None:
            friendly_options["chrome_headless"] = not visible
        if screenshots is not None:
            friendly_options["screenshot"] = screenshots
        if scrape_urls is not None:
            friendly_options["scrape_urls"] = scrape_urls

        target = normalize_json_path(output) if output is not None else None
        if target is not None and target.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing result file: {target}")
        request = SearchRequest.create(keywords, config=config, **friendly_options)
        report = self.application.execute(request)
        self.last_report = report
        self.results = report.results
        self.related = report.related_keywords
        if target is not None:
            self.writer.write(target, self.results, overwrite=overwrite)
        return self.results

    def save_json(
        self,
        file_path: str | Path,
        results: Iterable[Mapping[str, Any]] | None = None,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Save provided or most recent results as an atomic JSON array."""

        return self.writer.write(
            file_path,
            self.results if results is None else results,
            overwrite=overwrite,
        )

    def init(
        self,
        config: Config | Mapping[str, Any] | None = None,
        keywords: str | Iterable[str] | None = None,
    ) -> None:
        """Compatibility adapter for the Phase 1 ``init``/``run`` lifecycle."""

        if keywords is None:
            raise ValueError("No keywords given")
        request = SearchRequest.create(keywords, config=config)
        self.config = request.to_config()
        self.serp_query = list(request.queries)

    def run(self) -> list[dict[str, Any]]:
        """Run a request prepared by ``init`` (Phase 1 compatibility)."""

        if self.config is None or self.serp_query is None:
            raise RuntimeError("Call init() before run(), or use search() directly")
        return self.search(self.serp_query, config=self.config)

    def scrap_serps(self) -> list[dict[str, Any]]:
        """Compatibility alias returning the same canonical result list."""

        return self.run()

    def scrap(self):
        """Compatibility hook returning the Phase 1 ORM graph."""

        if self.config is None or self.serp_query is None:
            raise RuntimeError("Call init() before scrap()")
        config = dict(self.config)
        config["keywords"] = list(self.serp_query)
        return self.application.runner.run(config)

    def scrap_url(self, url: str) -> dict[str, Any]:
        if self.config is None:
            self.config = Config().get()
        return UrlScrape(self.config).scrap_url(url)

    def get_related(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self.related]

    def get_failures(self) -> list[dict[str, Any]]:
        """Return structured failures from the most recent request."""

        if self.last_report is None:
            return []
        return [failure.to_dict() for failure in self.last_report.failures]
