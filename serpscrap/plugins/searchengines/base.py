"""Small, transport-independent contract shared by search-engine plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from html import unescape
from typing import Any, ClassVar
from urllib.parse import urlencode, urljoin, urlparse

import lxml.html
from lxml import etree


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
    visible_text: str | None = None


@dataclass(frozen=True, slots=True)
class BrowserInteraction:
    """Declarative homepage-to-SERP contract for one provider."""

    homepage_url: str
    search_input_selectors: tuple[str, ...]
    submit_selectors: tuple[str, ...]
    serp_ready_selectors: tuple[str, ...]
    organic_card_selectors: tuple[str, ...]
    observed_at: str | None = None
    verification_status: str = "candidate"
    dismiss_selectors: tuple[str, ...] = ()
    consent_button_selectors: tuple[str, ...] = ()
    consent_manage_selectors: tuple[str, ...] = ()
    consent_reject_labels: tuple[str, ...] = (
        "reject",
        "reject all",
        "ablehnen",
        "alle ablehnen",
        "necessary",
        "notwendig",
        "nur notwendige",
        "nicht essenzielle cookies ablehnen",
        "non-essential cookies",
        "refuse",
    )
    consent_accept_labels: tuple[str, ...] = (
        "accept",
        "accept all",
        "alle akzeptieren",
        "akzeptieren",
        "agree",
        "agree all",
        "zustimmen",
        "allow all",
    )

    def metadata(self) -> dict[str, Any]:
        return {
            "homepage_url": self.homepage_url,
            "search_input_selectors": list(self.search_input_selectors),
            "submit_selectors": list(self.submit_selectors),
            "serp_ready_selectors": list(self.serp_ready_selectors),
            "organic_card_selectors": list(self.organic_card_selectors),
            "observed_at": self.observed_at,
            "verification_status": self.verification_status,
            "dismiss_selectors": list(self.dismiss_selectors),
            "consent_button_selectors": list(self.consent_button_selectors),
            "consent_manage_selectors": list(self.consent_manage_selectors),
            "consent_reject_labels": list(self.consent_reject_labels),
            "consent_accept_labels": list(self.consent_accept_labels),
        }


@dataclass(frozen=True, slots=True)
class PluginCapabilities:
    """Validated, transport-independent capabilities of a plugin."""

    search_types: tuple[str, ...]
    pagination: str
    transport: str
    supported_countries: frozenset[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "search_types": list(self.search_types),
            "pagination": self.pagination,
            "transport": self.transport,
            "supported_countries": sorted(self.supported_countries),
        }


class SearchEnginePlugin(ABC):
    """Trusted, side-effect-free boundary for one search engine.

    Provider implementations should normally only define identity, URL
    construction, parsing, and declarative class attributes. Shared execution
    services own transport lifecycle, retries, persistence, and fusion.
    """

    contract_version: ClassVar[str] = "1"
    plugin_version = "1"
    display_name: str | None = None
    search_types: tuple[str, ...] = ("normal",)
    pagination_strategy: str = "provider"
    transport: str = "browser"
    authentication: str = "none"
    supported_countries: frozenset[str] = frozenset()
    market_share: float | None = None
    provider_family: str | None = None
    readiness: str = "enabled"
    disable_reason: str | None = None
    fixture_version: str = "1"
    terms_review_date: str | None = None
    browser_interaction: BrowserInteraction | None = None
    homepage_block_markers: tuple[str, ...] = ()
    homepage_consent_markers: tuple[str, ...] = ()
    homepage_block_selectors: tuple[str, ...] = ()
    homepage_consent_selectors: tuple[str, ...] = ()
    blocked_visible_markers: tuple[str, ...] = (
        "captcha", "unusual traffic", "access denied", "verify you are human", "automated queries"
    )
    rate_limited_visible_markers: tuple[str, ...] = ("too many requests", "rate limit", "429")
    consent_visible_markers: tuple[str, ...] = (
        "consent required", "cookie consent", "privacy choices", "manage privacy settings",
        "accept all", "reject all",
    )
    empty_visible_markers: tuple[str, ...] = ()

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

    def classify(self, url: str, html: str, *, visible_text: str | None = None) -> str | None:
        """Return an observable failure state, or ``None`` for a parseable page."""

        rendered = visible_text if visible_text is not None else self.visible_text_from_html(html)
        lowered = f"{url}\n{rendered}".lower()
        if any(token in lowered for token in self.blocked_visible_markers):
            return "blocked"
        if any(token in lowered for token in self.rate_limited_visible_markers):
            return "rate_limited"
        if any(token in lowered for token in self.consent_visible_markers):
            return "consent_required"
        return None

    def classify_homepage(
        self,
        url: str,
        *,
        html: str = "",
        visible_text: str = "",
    ) -> str | None:
        """Classify an access-control page before searching for the input."""

        lowered = f"{url}\n{visible_text}".lower()
        if any(token in lowered for token in self.homepage_block_markers):
            return "blocked"
        if any(token in lowered for token in self.homepage_consent_markers):
            return "consent_required"
        if html:
            try:
                dom = lxml.html.fromstring(html)
                if any(dom.cssselect(selector) for selector in self.homepage_block_selectors):
                    return "blocked"
                if any(dom.cssselect(selector) for selector in self.homepage_consent_selectors):
                    return "consent_required"
            except (TypeError, ValueError, etree.ParserError):
                pass
        return self.classify(url, "", visible_text=visible_text)

    def classify_empty(self, url: str, html: str, *, visible_text: str | None = None) -> bool:
        """Return whether the rendered page explicitly represents no results."""

        del url
        rendered = visible_text if visible_text is not None else self.visible_text_from_html(html)
        lowered = rendered.lower()
        return bool(self.empty_visible_markers and any(marker in lowered for marker in self.empty_visible_markers))

    @staticmethod
    def visible_text_from_html(html: str) -> str:
        """Extract visible-ish text while excluding scripts and embedded payloads."""

        if not html:
            return ""
        try:
            dom = lxml.html.fromstring(html)
            for node in dom.xpath("//script|//style|//noscript|//template|//svg"):
                node.drop_tree()
            return " ".join(dom.text_content().split())
        except (TypeError, ValueError, etree.ParserError):
            return ""

    @property
    def enabled(self) -> bool:
        return self.readiness == "enabled"

    @property
    def capabilities(self) -> PluginCapabilities:
        return PluginCapabilities(
            search_types=tuple(self.search_types),
            pagination=self.pagination_strategy,
            transport=self.transport,
            supported_countries=frozenset(self.supported_countries),
        )

    def validate_contract(self) -> tuple[str, ...]:
        """Return actionable contract errors without performing I/O."""

        errors: list[str] = []
        engine_id = self.engine_id
        if not engine_id or engine_id != engine_id.lower() or any(
            character not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for character in engine_id
        ):
            errors.append("engine_id must be non-empty lowercase ASCII with '-', '_' or digits")
        if not self.search_url or "{" not in self.search_url:
            errors.append("search_url must be a non-empty URL template")
        if not self.search_types or len(set(self.search_types)) != len(self.search_types):
            errors.append("search_types must be a non-empty tuple without duplicates")
        if any(not value or value != value.lower() for value in self.search_types):
            errors.append("search_types must contain non-empty lowercase values")
        if self.readiness not in {"enabled", "experimental", "disabled"}:
            errors.append("readiness must be enabled, experimental, or disabled")
        if self.readiness != "enabled" and not self.disable_reason:
            errors.append("disable_reason is required for experimental or disabled plugins")
        if self.pagination_strategy not in {"offset", "page", "provider", "cursor", "none"}:
            errors.append("pagination_strategy is unsupported")
        if self.transport not in {"browser", "http", "hybrid"}:
            errors.append("transport must be browser, http, or hybrid")
        if self.authentication not in {"none", "api_key", "login"}:
            errors.append("authentication must be none, api_key, or login")
        if any(not country or country != country.upper() or len(country) != 2 for country in self.supported_countries):
            errors.append("supported_countries must contain ISO-3166 alpha-2 uppercase codes")
        if self.transport in {"browser", "hybrid"}:
            interaction = self.browser_interaction
            if interaction is None:
                errors.append("browser_interaction is required for browser or hybrid transport")
            elif not all((interaction.homepage_url, interaction.search_input_selectors, interaction.serp_ready_selectors, interaction.organic_card_selectors)):
                errors.append("browser_interaction requires homepage, input, ready, and organic selectors")
        return tuple(errors)

    def validate_request(self, *, search_type: str, country_code: str) -> None:
        """Validate a requested capability before navigation starts."""

        if search_type not in self.search_types:
            raise ValueError(f"{self.engine_id} does not support search type {search_type!r}")
        normalized_country = country_code.upper()
        if self.supported_countries and normalized_country not in self.supported_countries:
            raise ValueError(f"{self.engine_id} does not support country {normalized_country}")

    def metadata(self) -> dict[str, Any]:
        """Return stable operational metadata without importing a transport."""
        return {
            "engine_id": self.engine_id,
            "display_name": self.display_name or self.engine_id,
            "contract_version": self.contract_version,
            "plugin_version": self.plugin_version,
            "readiness": self.readiness,
            "disable_reason": self.disable_reason,
            "fixture_version": self.fixture_version,
            "supported_countries": sorted(self.supported_countries),
            "search_types": list(self.search_types),
            "pagination_strategy": self.pagination_strategy,
            "transport": self.transport,
            "authentication": self.authentication,
            "capabilities": self.capabilities.to_dict(),
            "provider_family": self.provider_family,
            "market_share": self.market_share,
            "terms_review_date": self.terms_review_date,
            "browser_interaction": (
                self.browser_interaction.metadata() if self.browser_interaction else None
            ),
        }


def _clean_text(value: str | None) -> str | None:
    if not value:
        return None
    text = " ".join(unescape(value).split())
    if any(marker in text for marker in ("Ã", "Â", "â")):
        try:
            repaired = text.encode("cp1252").decode("utf-8")
            if repaired.count("�") <= text.count("�"):
                text = repaired
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
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
