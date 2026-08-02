from __future__ import annotations

import json

import pytest

from serpscrap.plugins.searchengines.base import (
    BrowserInteraction,
    GenericHtmlPlugin,
)
from serpscrap.plugins.searchengines.registry import SearchEngineRegistry, default_registry


class FixturePlugin(GenericHtmlPlugin):
    engine_id = "fixture_engine"
    display_name = "Fixture Engine"
    search_url = "https://fixture.example/search?q={query}"
    pagination_strategy = "page"
    browser_interaction = BrowserInteraction(
        homepage_url="https://fixture.example/",
        search_input_selectors=("input[name='q']",),
        submit_selectors=("button[type='submit']",),
        serp_ready_selectors=("main",),
        organic_card_selectors=("article.result",),
    )
    card_selectors = ("article.result",)

    def _build_url(self, query: str, page: int, country_code: str) -> str:
        return self.search_url.format(query=query) + f"&page={page}"


def test_plugin_contract_is_self_describing_and_json_safe():
    plugin = FixturePlugin()

    assert plugin.validate_contract() == ()
    assert plugin.capabilities.pagination == "page"
    metadata = plugin.metadata()
    assert metadata["display_name"] == "Fixture Engine"
    assert metadata["capabilities"]["transport"] == "browser"
    json.dumps(metadata)


def test_registry_validates_plugins_and_finds_capabilities():
    registry = SearchEngineRegistry([FixturePlugin()])

    assert registry.ids() == ("fixture_engine",)
    assert registry.find_capable(search_type="normal", country_code="DE")[0].engine_id == "fixture_engine"
    with pytest.raises(ValueError, match="duplicate search-engine plugin ID"):
        registry.register(FixturePlugin())


def test_registry_rejects_incomplete_plugin_contract():
    class InvalidPlugin(GenericHtmlPlugin):
        engine_id = "Invalid ID"
        search_url = "https://fixture.example/search"
        browser_interaction = None

        def _build_url(self, query: str, page: int, country_code: str) -> str:
            return "https://fixture.example/"

    with pytest.raises(ValueError, match="invalid plugin"):
        SearchEngineRegistry([InvalidPlugin()])


def test_existing_registry_plugins_expose_valid_capabilities():
    registry = default_registry()

    assert len(registry.find_capable(search_type="normal", country_code="DE")) == 11
    for plugin in registry:
        assert plugin.validate_contract() == ()
        assert plugin.metadata()["contract_version"] == "1"
        assert plugin.metadata()["capabilities"]["search_types"]


def test_plugin_request_validation_is_explicit():
    plugin = FixturePlugin()
    with pytest.raises(ValueError, match="does not support search type"):
        plugin.validate_request(search_type="images", country_code="DE")

    class GermanOnly(FixturePlugin):
        supported_countries = frozenset({"DE"})

    with pytest.raises(ValueError, match="does not support country AT"):
        GermanOnly().validate_request(search_type="normal", country_code="AT")
