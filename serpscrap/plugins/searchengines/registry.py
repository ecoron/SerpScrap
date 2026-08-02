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
            "div[role='dialog'][aria-modal='true'] button#W0wltc",
            "div[role='dialog'][aria-modal='true'] button",
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
    ):
        self._engine_id = engine_id
        self._base = base
        self._template = template
        self.market_share = market_share
        self.provider_family = family
        self.supported_countries = frozenset()
        self.browser_interaction = browser_interaction
        self.card_selectors = card_selectors

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
        _TemplatePlugin("bing", "https://www.bing.com", "https://www.bing.com/search?q={query}&first={offset}", 5.00, "bing", interaction("https://www.bing.com/", ("textarea#sb_form_q", "input[name='q']"), ("form#sb_form button[type='submit']",), ("#b_results",), ("li.b_algo",)), ("li.b_algo",)),
        _TemplatePlugin("yandex", "https://yandex.com", "https://yandex.com/search/?text={query}&p={page_minus_one}", 2.50, "yandex", interaction("https://yandex.com/", ("input[name='text']", "input[type='search']"), ("form[action*='/search'] button[type='submit']",), ("[data-serp-item]", ".serp-item"), (".serp-item",)), (".serp-item",)),
        _TemplatePlugin("yahoo", "https://search.yahoo.com", "https://search.yahoo.com/search?p={query}&b={offset_plus_one}", 1.47, "bing", interaction("https://search.yahoo.com/", ("input[name='p']", "input[type='search']"), ("form[action*='/search'] button[type='submit']",), ("#web",), ("div.algo",)), ("div.algo",)),
        _TemplatePlugin("duckduckgo", "https://html.duckduckgo.com", "https://html.duckduckgo.com/html/?q={query}&s={offset}", 0.85, "bing", interaction("https://html.duckduckgo.com/html/", ("input[name='q']",), ("form[action='/html/'] input[type='submit']",), ("div.results",), (".result",)), (".result",)),
        _TemplatePlugin("ecosia", "https://www.ecosia.org", "https://www.ecosia.org/search?q={query}&p={page}", 0.48, "mixed", interaction("https://www.ecosia.org/", ("input[name='q']", "input[type='search']"), ("form[action*='/search'] button[type='submit']",), ("main",), ("article",)), ("article",)),
        _TemplatePlugin("qwant", "https://www.qwant.com", "https://www.qwant.com/?q={query}&t=web&locale={country}", None, "bing", interaction("https://www.qwant.com/", ("input[name='q']", "input[type='search']"), ("button[type='submit']",), ("main",), ("article",)), ("article",)),
        _TemplatePlugin("startpage", "https://www.startpage.com", "https://www.startpage.com/sp/search?q={query}", None, "google", interaction("https://www.startpage.com/", ("input[name='query']", "input[type='search']"), ("form[action*='/sp/search'] button[type='submit']",), ("a.result-title", ".w-gl"), ("a.result-title",)), ("a.result-title",)),
        _TemplatePlugin("brave", "https://search.brave.com", "https://search.brave.com/search?q={query}&source=web&offset={offset}", None, "brave", interaction("https://search.brave.com/", ("textarea#searchbox", "textarea[name='q']", "input[name='q']", "input[type='search']"), ("form button[type='submit']",), (".snippet",), (".snippet",)), (".snippet",)),
        _TemplatePlugin("swisscows", "https://swisscows.com", "https://swisscows.com/en/web?query={query}&page={page}", None, "bing", interaction("https://swisscows.com/en/web", ("input[name='query']", "input[type='search']"), ("form button[type='submit']",), ("article.item.web-page",), ("article.item.web-page",), (".swisscows-pro-popup .buttons button",)), ("article.item.web-page",)),
        _TemplatePlugin("mojeek", "https://www.mojeek.com", "https://www.mojeek.com/search?q={query}&s={offset}", None, "mojeek", interaction("https://www.mojeek.com/", ("input[name='q']", "input[placeholder*='Search']"), ("form button[type='submit']",), (".results-standard",), ("ul.results-standard > li[class^='r']",)), ("ul.results-standard > li[class^='r']",)),
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
                    "#didomi-host button",
                    "#didomi-host [role='button']",
                    "[data-testid*='consent'] button",
                    "[role='dialog'][aria-modal='true'] button",
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
    return plugins


class SearchEngineRegistry:
    def __init__(self, plugins: Iterable[SearchEnginePlugin]):
        plugin_list = list(plugins)
        self._plugins = {plugin.engine_id: plugin for plugin in plugin_list}
        if len(self._plugins) != len(plugin_list):
            raise ValueError("duplicate search-engine plugin IDs")
        if any(not key or key != key.lower() for key in self._plugins):
            raise ValueError("search-engine IDs must be lowercase and non-empty")

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

    def ids(self) -> tuple[str, ...]:
        return tuple(self._plugins)

    def __iter__(self):
        return iter(self._plugins.values())

    def metadata(self) -> list[dict[str, object]]:
        return [plugin.metadata() for plugin in self._plugins.values()]


def default_registry() -> SearchEngineRegistry:
    return SearchEngineRegistry([_GooglePlugin(), *_alternatives()])
