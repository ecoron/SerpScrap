"""Explicit trusted registry for the Phase 4 in-tree engine plugins."""

from __future__ import annotations

from collections.abc import Iterable

from serpscrap.plugins.searchengines.base import GenericHtmlPlugin, SearchEnginePlugin


class _GooglePlugin(SearchEnginePlugin):
    engine_id = "google"
    search_url = "https://www.google.com/search?q={query}"
    # Empty means the provider accepts an ISO code as a neutral locale hint;
    # country-specific provider IDs are added as fixtures mature.
    supported_countries = frozenset()
    market_share = 89.07
    provider_family = "google"
    search_types = ("normal", "image", "news", "shopping", "videos")

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
    def __init__(self, engine_id: str, base: str, template: str, market_share: float | None, family: str | None):
        self._engine_id = engine_id
        self._base = base
        self._template = template
        self.market_share = market_share
        self.provider_family = family
        self.supported_countries = frozenset()

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
    return [
        _TemplatePlugin("bing", "https://www.bing.com", "https://www.bing.com/search?q={query}&first={offset}", 5.00, "bing"),
        _TemplatePlugin("yandex", "https://yandex.com", "https://yandex.com/search/?text={query}&p={page_minus_one}", 2.50, "yandex"),
        _TemplatePlugin("yahoo", "https://search.yahoo.com", "https://search.yahoo.com/search?p={query}&b={offset_plus_one}", 1.47, "bing"),
        _TemplatePlugin("duckduckgo", "https://html.duckduckgo.com", "https://html.duckduckgo.com/html/?q={query}&s={offset}", 0.85, "bing"),
        _TemplatePlugin("ecosia", "https://www.ecosia.org", "https://www.ecosia.org/search?q={query}&p={page}", 0.48, "mixed"),
        _TemplatePlugin("qwant", "https://www.qwant.com", "https://www.qwant.com/?q={query}&t=web&locale={country}", None, "bing"),
        _TemplatePlugin("startpage", "https://www.startpage.com", "https://www.startpage.com/sp/search?q={query}", None, "google"),
        _TemplatePlugin("brave", "https://search.brave.com", "https://search.brave.com/search?q={query}&source=web&offset={offset}", None, "brave"),
        _TemplatePlugin("swisscows", "https://swisscows.com", "https://swisscows.com/en/web?query={query}&page={page}", None, "bing"),
        _TemplatePlugin("mojeek", "https://www.mojeek.com", "https://www.mojeek.com/search?q={query}&s={offset}", None, "mojeek"),
    ]


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
