"""Explicit trusted registry for the Phase 4 in-tree engine plugins."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from serpscrap.plugins.searchengines.base import (
    BrowserInteraction,
    GenericHtmlPlugin,
    SearchEnginePlugin,
)


class _GooglePlugin(SearchEnginePlugin):
    engine_id = "google"
    search_url = "https://www.google.com/search?q={query}"
    # Empty means the provider accepts an ISO code as a neutral locale hint;
    # country-specific provider IDs are added as fixtures mature.
    supported_countries = frozenset()
    market_share = 89.07
    provider_family = "google"
    search_types = ("normal", "image", "news", "shopping", "videos")
    browser_interaction = BrowserInteraction(
        homepage_url="https://www.google.com/",
        search_input_selectors=("textarea[name='q']", "input[name='q']"),
        submit_selectors=("button[name='btnK']", "input[name='btnK']"),
        serp_ready_selectors=("#search", "#rso", "div[role='main']"),
        organic_card_selectors=("div.MjjYud", "#search a h3"),
        observed_at="2026-08-02",
        consent_button_selectors=(
            "div.GzLjMd button#W0wltc",
            "button#W0wltc",
            "div[role='dialog'][aria-modal='true'] button",
            "div[role='dialog'][aria-modal='true'] [role='button']",
        ),
    )
    homepage_consent_selectors = ("div[role='dialog'][aria-modal='true']",)

    def build_url(self, query: str, page: int, country_code: str, search_type: str) -> str:
        from scrapcore.scraper.browser import GoogleSearchAdapter

        config = {"google_search_url": "https://www.google.com/search?", "language": "de-DE"}
        return GoogleSearchAdapter(config).build_url(query, page, search_type)

    def parse(self, html: str, *, query: str, page: int, search_type: str):
        from scrapcore.parser.google_parser import GoogleParser

        parser = GoogleParser(config={"search_type": search_type}, query=query, html=html)
        values = []
        for result_type, items in parser.search_results.items():
            for item in items:
                from serpscrap.plugins.searchengines.base import EngineResult

                values.append(
                    EngineResult(
                        url=item["link"],
                        title=item.get("title"),
                        snippet=item.get("snippet"),
                        visible_link=item.get("visible_link"),
                        domain=None,
                        rank=int(item.get("rank") or 0),
                        result_type=result_type,
                        source=item.get("source"),
                        date=item.get("published_at"),
                        extras={key: item.get(key) for key in ("rating", "sitelinks", "price", "merchant", "duration", "image_url", "thumbnail_url")},
                    )
                )
        return values


class _TemplatePlugin(GenericHtmlPlugin):
    def __init__(
        self,
        engine_id: str,
        base: str,
        template: str,
        market_share: float | None,
        family: str | None,
        browser_interaction: BrowserInteraction,
        card_selectors: tuple[str, ...],
        *,
        display_name: str | None = None,
        readiness: str = "enabled",
        disable_reason: str | None = None,
        pagination_strategy: str = "provider",
        authentication: str = "none",
    ):
        self._engine_id = engine_id
        self._base = base
        self._template = template
        self.market_share = market_share
        self.provider_family = family
        self.supported_countries = frozenset()
        self.browser_interaction = browser_interaction
        self.card_selectors = card_selectors
        self.display_name = display_name or engine_id.replace("_", " ").title()
        self.readiness = readiness
        self.disable_reason = disable_reason
        self.pagination_strategy = pagination_strategy
        self.authentication = authentication

    @property
    def engine_id(self) -> str:
        return self._engine_id

    @property
    def search_url(self) -> str:
        return self._template

    def _build_url(self, query: str, page: int, country_code: str) -> str:
        from urllib.parse import quote

        offset = max(0, page - 1) * 10
        encoded = quote(query, safe="")
        return self._template.format(
            query=encoded,
            offset=offset,
            offset_plus_one=offset + 1,
            page=page,
            page_minus_one=max(0, page - 1),
            country=country_code.lower(),
        )


def _alternatives() -> list[SearchEnginePlugin]:
    def interaction(homepage: str, inputs: tuple[str, ...], submits: tuple[str, ...], ready: tuple[str, ...], cards: tuple[str, ...], dismiss: tuple[str, ...] = ()) -> BrowserInteraction:
        return BrowserInteraction(homepage, inputs, submits, ready, cards, observed_at="2026-08-02", dismiss_selectors=dismiss)

    plugins = [
        _TemplatePlugin("bing", "https://www.bing.com", "https://www.bing.com/search?q={query}&first={offset}", 5.00, "bing", interaction("https://www.bing.com/", ("textarea#sb_form_q", "input[name='q']"), ("form#sb_form button[type='submit']",), ("#b_results",), ("li.b_algo",)), ("li.b_algo", "li.result")),
        _TemplatePlugin("yandex", "https://yandex.com", "https://yandex.com/search/?text={query}&p={page_minus_one}", 2.50, "yandex", interaction("https://yandex.com/", ("input[name='text']", "input[type='search']"), ("form[action*='/search'] button[type='submit']",), ("[data-serp-item]", ".serp-item"), (".serp-item",)), (".serp-item",)),
        _TemplatePlugin("yahoo", "https://search.yahoo.com", "https://search.yahoo.com/search?p={query}&b={offset_plus_one}", 1.47, "bing", interaction("https://search.yahoo.com/", ("input[name='p']", "input[type='search']"), ("form[action*='/search'] button[type='submit']",), ("#web",), ("div.algo",)), ("div.algo",)),
        _TemplatePlugin("duckduckgo", "https://html.duckduckgo.com", "https://html.duckduckgo.com/html/?q={query}&s={offset}", 0.85, "bing", interaction("https://html.duckduckgo.com/html/", ("input[name='q']",), ("form[action='/html/'] input[type='submit']",), ("div.results",), (".result",)), (".result",)),
        _TemplatePlugin("ecosia", "https://www.ecosia.org", "https://www.ecosia.org/search?q={query}&p={page}", 0.48, "mixed", interaction("https://www.ecosia.org/", ("input[name='q']", "input[type='search']"), ("form[action*='/search'] button[type='submit']",), ("main",), ("article",)), ("article",)),
        _TemplatePlugin("qwant", "https://www.qwant.com", "https://www.qwant.com/?q={query}&t=web&locale={country}", None, "bing", interaction("https://www.qwant.com/", ("input[name='q']", "input[type='search']"), ("button[type='submit']",), ("main",), ("article",)), ("article",)),
        _TemplatePlugin("startpage", "https://www.startpage.com", "https://www.startpage.com/sp/search?q={query}", None, "google", interaction("https://www.startpage.com/", ("input[name='query']", "input[type='search']"), ("form[action*='/sp/search'] button[type='submit']",), ("a.result-title", ".w-gl"), ("a.result-title",)), ("a.result-title",)),
        _TemplatePlugin("brave", "https://search.brave.com", "https://search.brave.com/search?q={query}&source=web&offset={offset}", None, "brave", interaction("https://search.brave.com/", ("textarea#searchbox", "textarea[name='q']", "input[name='q']", "input[type='search']"), ("form button[type='submit']",), (".snippet",), (".snippet",)), (".snippet",)),
        _TemplatePlugin("swisscows", "https://swisscows.com", "https://swisscows.com/en/web?query={query}&page={page}", None, "bing", interaction("https://swisscows.com/en/web", ("input[name='query']", "input[type='search']"), ("form button[type='submit']",), ("article.item.web-page",), ("article.item.web-page",), (".swisscows-pro-popup .buttons button",)), ("article.item.web-page",)),
        _TemplatePlugin("mojeek", "https://www.mojeek.com", "https://www.mojeek.com/search?q={query}&s={offset}", None, "mojeek", interaction("https://www.mojeek.com/", ("input[name='q']", "input[placeholder*='Search']"), ("form button[type='submit']",), (".results-standard",), ("ul.results-standard > li[class^='r']",)), ("ul.results-standard > li[class^='r']",)),
        _TemplatePlugin("metager", "https://metager.org", "https://metager.org/meta/meta.ger3?eingabe={query}", None, "metager", interaction("https://metager.org/", ("input[name='eingabe']",), ("form[action*='meta.ger3'] button[type='submit']",), ("main",), ("article", "li.result")), ("article", "li.result"), display_name="MetaGer", pagination_strategy="provider", readiness="disabled", disable_reason="public search currently requires a MetaGer key"),
        _TemplatePlugin("good", "https://good-search.org", "https://good-search.org/en/?q={query}", None, "brave", interaction("https://good-search.org/en/", ("input[placeholder*='Search the web']", "input[name='q']", "input[type='search']"), ("form button[type='submit']",), ("main",), ("article", "li.result")), ("article", "li.result"), display_name="GOOD Search", pagination_strategy="none"),
        _TemplatePlugin("xprivo", "https://www.xprivo.com", "https://www.xprivo.com/search/?q={query}&page={page}", None, "xprivo", interaction("https://www.xprivo.com/search/", ("input[name='q']", "input[type='search']", "textarea[placeholder*='Search']"), ("form button[type='submit']",), ("main", "[class*='result']", "article"), ("[class*='result']", "article")), ("[class*='result']", "article"), display_name="xPrivo", pagination_strategy="page"),
        _TemplatePlugin("marginalia", "https://marginalia-search.com", "https://marginalia-search.com/search?q={query}&page={page}", None, "marginalia", interaction("https://marginalia-search.com/", ("input[name='query']", "input[name='q']", "input[type='search']"), ("form button[type='submit']",), ("main",), ("article", "li.result")), ("article", "li.result"), display_name="Marginalia", pagination_strategy="page"),
        _TemplatePlugin("etools", "https://www.etools.ch", "https://www.etools.ch/searchSubmit.do?query={query}&country={country}", None, "etools", interaction("https://www.etools.ch/", ("input[name='query']",), ("form[action*='searchSubmit.do'] button[type='submit']", "form[action*='searchSubmit.do'] input[type='submit']"), ("#results", ".results", ".searchResult", ".result", "table.results", ".content h2"), ("#results .result", ".results .result", ".searchResult", ".result", "table.results tr")), ("#results .result", ".results .result", ".searchResult", ".result", "table.results tr"), display_name="eTools.ch", pagination_strategy="provider"),
    ]
    for plugin in plugins:
        if plugin.engine_id == "brave":
            plugin.homepage_block_markers = ("captcha", "verify you are human", "challenge")
            plugin.homepage_block_selectors = (
                "[id*='captcha']", "[class*='captcha']", "[data-testid*='captcha']",
            )
            plugin.title_selectors = ("div.title", "h2", "h3", "[role='heading']")
            plugin.snippet_selectors = (".generic-snippet .content", ".snippet", "p")
        elif plugin.engine_id == "ecosia":
            plugin.homepage_consent_markers = (
                "consent", "privacy choices", "accept all", "reject all", "didomi"
            )
            plugin.homepage_consent_selectors = (
                "#didomi-host", "[data-testid*='consent']", "[role='dialog'][aria-modal='true']",
            )
            assert plugin.browser_interaction is not None
            plugin.browser_interaction = replace(
                plugin.browser_interaction,
                consent_button_selectors=(
                    "#didomi-notice-disagree-button",
                    "#didomi-host button",
                    "#didomi-host [role='button']",
                    "[data-testid*='consent'] button",
                    "[role='dialog'][aria-modal='true'] button",
                    "[role='dialog'][aria-modal='true'] [role='button']",
                ),
                consent_reject_labels=(
                    "reject",
                    "reject all",
                    "ablehnen",
                    "alle ablehnen",
                    "nicht essenzielle cookies ablehnen",
                    "necessary",
                    "notwendig",
                    "nur notwendige",
                    "refuse",
                ),
            )
        elif plugin.engine_id == "mojeek":
            plugin.empty_visible_markers = ("no results", "nothing found", "did not match any")
            plugin.title_selectors = ("h2.title", "h2", "h3", "[role='heading']")
            plugin.snippet_selectors = ("p.s", ".snippet", "p")
        elif plugin.engine_id == "qwant":
            plugin.blocked_visible_markers = (*plugin.blocked_visible_markers, "http 403")
            plugin.blocked_visible_markers = (
                *plugin.blocked_visible_markers,
                "http 403", "temporarily unavailable", "vorübergehend nicht verfügbar",
            )
            plugin.empty_visible_markers = ("no results", "aucun résultat", "keine ergebnisse")
        elif plugin.engine_id == "startpage":
            plugin.title_selectors = ("h2.wgl-title", "h2", "h3", "[role='heading']")
            plugin.snippet_selectors = ("p.description", ".snippet", "p")
            plugin.empty_visible_markers = ("no results", "did not match any", "keine ergebnisse")
        elif plugin.engine_id == "swisscows":
            plugin.title_selectors = ("h1.title", "h2", "h3", "[role='heading']")
            plugin.snippet_selectors = ("p.description", ".snippet", "p")
            plugin.empty_visible_markers = ("no results", "keine ergebnisse", "nothing found")
        elif plugin.engine_id == "good":
            plugin.card_selectors = ("div.margin-bottom--small.box",)
            plugin.title_selectors = ("h4.result", "h2", "h3", "[role='heading']")
            plugin.snippet_selectors = ("div.link--search p", ".snippet", "p")
        elif plugin.engine_id == "marginalia":
            # The current UI renders each result as a heading-led block rather
            # than an article or li.result card.
            plugin.card_selectors = ("main h2",)
            plugin.title_selectors = ("h2",)
            plugin.snippet_selectors = ("p",)
    return plugins


def searxng_plugin(instance_url: str) -> SearchEnginePlugin:
    """Create an auth-free plugin for one explicitly trusted SearXNG instance.

    SearXNG is instance-scoped: the instance controls enabled engines, locale,
    theme, limiter, and result markup. No public instance is selected by
    default and no instance rotation is performed.
    """

    normalized = instance_url.rstrip("/")
    return _TemplatePlugin(
        "searxng",
        normalized,
        f"{normalized}/search?q={{query}}&format=html&pageno={{page}}",
        None,
        "searxng",
        BrowserInteraction(
            homepage_url=f"{normalized}/",
            search_input_selectors=("input[name='q']", "input[type='search']"),
            submit_selectors=("form[action='/'] button[type='submit']", "form button[type='submit']"),
            serp_ready_selectors=("#results", "main", "article.result"),
            organic_card_selectors=("article.result", ".result", ".result_header"),
            observed_at=None,
            verification_status="candidate",
        ),
        ("article.result", ".result"),
        display_name="SearXNG instance",
        readiness="experimental",
        disable_reason="requires explicit trusted public instance and fixture verification",
        pagination_strategy="page",
    )


class SearchEngineRegistry:
    def __init__(self, plugins: Iterable[SearchEnginePlugin], *, allow_authenticated: bool = False):
        self._plugins: dict[str, SearchEnginePlugin] = {}
        self.allow_authenticated = allow_authenticated
        for plugin in plugins:
            self.register(plugin)

    def register(self, plugin: SearchEnginePlugin) -> SearchEnginePlugin:
        """Register one validated plugin while preserving insertion order."""

        errors = plugin.validate_contract()
        if errors:
            details = "; ".join(errors)
            raise ValueError(f"invalid plugin {plugin.engine_id!r}: {details}")
        if plugin.authentication != "none" and not self.allow_authenticated:
            raise ValueError(
                f"plugin {plugin.engine_id!r} requires {plugin.authentication}; "
                "the default registry accepts only no-auth plugins"
            )
        if plugin.engine_id in self._plugins:
            raise ValueError(f"duplicate search-engine plugin ID: {plugin.engine_id}")
        self._plugins[plugin.engine_id] = plugin
        return plugin

    def get(self, engine_id: str) -> SearchEnginePlugin:
        try:
            return self._plugins[engine_id.lower()]
        except KeyError as exc:
            raise ValueError(f"Unknown search engine: {engine_id}") from exc

    def validate_selection(self, engine_ids: Iterable[str]) -> tuple[SearchEnginePlugin, ...]:
        selected = tuple(engine_ids)
        if len(set(selected)) != len(selected):
            raise ValueError("duplicate search engine IDs are not allowed")
        plugins = tuple(self.get(engine_id) for engine_id in selected)
        disabled = [plugin.engine_id for plugin in plugins if not plugin.enabled]
        if disabled:
            reasons = ", ".join(
                f"{plugin.engine_id}: {plugin.disable_reason or 'disabled'}"
                for plugin in plugins if not plugin.enabled
            )
            raise ValueError(f"disabled search engine(s): {reasons}")
        return plugins

    def find_capable(
        self,
        *,
        search_type: str = "normal",
        country_code: str = "",
        include_experimental: bool = False,
    ) -> tuple[SearchEnginePlugin, ...]:
        """Return plugins supporting a capability in deterministic registry order."""

        result = []
        for plugin in self:
            if plugin.readiness == "disabled" or (
                plugin.readiness == "experimental" and not include_experimental
            ):
                continue
            try:
                plugin.validate_request(search_type=search_type, country_code=country_code)
            except ValueError:
                continue
            result.append(plugin)
        return tuple(result)

    def ids(self) -> tuple[str, ...]:
        return tuple(self._plugins)

    def __iter__(self):
        return iter(self._plugins.values())

    def metadata(self) -> list[dict[str, object]]:
        return [plugin.metadata() for plugin in self._plugins.values()]


def default_registry() -> SearchEngineRegistry:
    return SearchEngineRegistry([_GooglePlugin(), *_alternatives()])
