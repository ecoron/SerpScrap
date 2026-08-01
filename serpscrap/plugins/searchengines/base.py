"""Small, transport-independent contract shared by search-engine plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from html import unescape
from typing import Any
from urllib.parse import urlencode, urljoin, urlparse

import lxml.html


@dataclass(frozen=True, slots=True)
class EngineResult:
    """One normalized result emitted by one engine and one SERP page."""

    url: str
    title: str | None
    snippet: str | None
    rank: int
    result_type: str = "results"
    visible_link: str | None = None
    domain: str | None = None
    source: str | None = None
    date: str | None = None
    extras: dict[str, Any] = field(default_factory=dict, compare=False)

    def to_dict(self, *, query: str, engine: str, country_code: str, page: int) -> dict[str, Any]:
        parsed = urlparse(self.url)
        return {
            "query_num_results_total": "",
            "query_num_results_page": 0,
            "query_page_number": page,
            "query": query,
            "serp_rank": self.rank,
            "serp_type": self.result_type,
            "serp_url": self.url,
            "serp_rating": self.extras.get("rating"),
            "serp_title": self.title,
            "serp_domain": self.domain or parsed.hostname,
            "serp_visible_link": self.visible_link,
            "serp_snippet": self.snippet,
            "serp_sitelinks": self.extras.get("sitelinks"),
            "serp_source": self.source,
            "serp_date": self.date,
            "serp_price": self.extras.get("price"),
            "serp_merchant": self.extras.get("merchant"),
            "serp_duration": self.extras.get("duration"),
            "serp_image_url": self.extras.get("image_url"),
            "serp_thumbnail_url": self.extras.get("thumbnail_url"),
            "screenshot": None,
            "search_engine": engine,
            "country_code": country_code,
        }


@dataclass(frozen=True, slots=True)
class EnginePage:
    """Captured HTML plus the response URL used by a plugin."""

    url: str
    html: str
    query: str
    engine: str
    country_code: str
    page: int


class SearchEnginePlugin(ABC):
    """Trusted in-tree plugin boundary for one search engine."""

    plugin_version = "1"
    search_types: tuple[str, ...] = ("normal",)
    supported_countries: frozenset[str] = frozenset()
    market_share: float | None = None
    provider_family: str | None = None
    readiness: str = "enabled"
    disable_reason: str | None = None
    fixture_version: str = "1"
    terms_review_date: str | None = None

    @property
    @abstractmethod
    def engine_id(self) -> str:
        """Stable lowercase registry identifier."""

    @property
    @abstractmethod
    def search_url(self) -> str:
        """Human-readable baseline URL template."""

    @abstractmethod
    def build_url(self, query: str, page: int, country_code: str, search_type: str) -> str:
        """Build one deterministic, encoded SERP URL."""

    @abstractmethod
    def parse(self, html: str, *, query: str, page: int, search_type: str) -> list[EngineResult]:
        """Parse organic results without network or persistence side effects."""

    def classify(self, url: str, html: str) -> str | None:
        """Return an observable failure state, or ``None`` for a parseable page."""

        lowered = f"{url}\n{html}".lower()
        if any(token in lowered for token in ("captcha", "unusual traffic", "access denied")):
            return "blocked"
        if any(token in lowered for token in ("consent required", "cookie consent", "your privacy")):
            return "consent_required"
        if any(token in lowered for token in ("too many requests", "rate limit", "429")):
            return "rate_limited"
        return None

    @property
    def enabled(self) -> bool:
        return self.readiness == "enabled"

    def metadata(self) -> dict[str, Any]:
        """Return stable operational metadata without importing a transport."""
        return {
            "engine_id": self.engine_id,
            "plugin_version": self.plugin_version,
            "readiness": self.readiness,
            "disable_reason": self.disable_reason,
            "fixture_version": self.fixture_version,
            "supported_countries": sorted(self.supported_countries),
            "search_types": list(self.search_types),
            "provider_family": self.provider_family,
            "market_share": self.market_share,
            "terms_review_date": self.terms_review_date,
        }


def _clean_text(value: str | None) -> str | None:
    if not value:
        return None
    text = " ".join(unescape(value).split())
    return text or None


class GenericHtmlPlugin(SearchEnginePlugin):
    """Conservative parser for server-rendered organic-card SERPs."""

    card_selectors: tuple[str, ...] = ("article", "li.result", "li.b_algo", "div.result")
    title_selectors: tuple[str, ...] = ("h2", "h3", "[role='heading']")
    snippet_selectors: tuple[str, ...] = (".snippet", ".b_caption p", ".result__snippet", "p")

    def build_url(self, query: str, page: int, country_code: str, search_type: str) -> str:
        if search_type not in self.search_types:
            raise ValueError(f"{self.engine_id} does not support search type {search_type!r}")
        return self._build_url(query, page, country_code)

    @abstractmethod
    def _build_url(self, query: str, page: int, country_code: str) -> str:
        """Provider-specific URL implementation."""

    def parse(self, html: str, *, query: str, page: int, search_type: str) -> list[EngineResult]:
        if search_type not in self.search_types:
            raise ValueError(f"{self.engine_id} does not support search type {search_type!r}")
        if not html:
            return []
        dom = lxml.html.fromstring(html)
        results: list[EngineResult] = []
        seen: set[str] = set()
        for selector in self.card_selectors:
            cards = dom.cssselect(selector)
            if not cards:
                continue
            for card in cards:
                heading = next(
                    (item for title_selector in self.title_selectors for item in card.cssselect(title_selector)),
                    None,
                )
                anchors = card.cssselect("a[href]")
                if heading is not None:
                    heading_anchors = heading.xpath("ancestor::a[1]")
                    if heading_anchors:
                        anchors = heading_anchors + anchors
                href = next((anchor.get("href") for anchor in anchors if anchor.get("href")), None)
                if not href or href.startswith(("#", "javascript:")):
                    continue
                href = urljoin(self.search_url.split("{", 1)[0], href)
                parsed = urlparse(href)
                if parsed.scheme not in {"http", "https"} or href in seen:
                    continue
                title = _clean_text(heading.text_content() if heading is not None else None)
                if not title:
                    continue
                snippet_node = next(
                    (item for snippet_selector in self.snippet_selectors for item in card.cssselect(snippet_selector)),
                    None,
                )
                snippet = _clean_text(snippet_node.text_content() if snippet_node is not None else None)
                seen.add(href)
                results.append(
                    EngineResult(
                        url=href,
                        title=title,
                        snippet=snippet,
                        visible_link=_clean_text(parsed.netloc + parsed.path),
                        domain=parsed.hostname,
                        rank=len(results) + 1,
                    )
                )
            if results:
                break
        return results

    @staticmethod
    def query_url(base: str, query: str, **params: Any) -> str:
        values = {key: value for key, value in params.items() if value is not None}
        values = {"q": query, **values}
        return f"{base}?{urlencode(values)}"
