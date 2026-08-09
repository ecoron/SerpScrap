from pathlib import Path

import pytest

from serpscrap.plugins.searchengines.base import BrowserInteraction, GenericHtmlPlugin
from serpscrap.plugins.searchengines.registry import (
    SearchEngineRegistry,
    default_registry,
    searxng_plugin,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "searchengines"


@pytest.mark.parametrize(
    ("engine", "fixture"),
    [
        ("good", "good/valid_serp_public.html"),
        ("xprivo", "xprivo/valid_serp_public.html"),
        ("marginalia", "marginalia/valid_serp_public.html"),
        ("etools", "etools/valid_serp_public.html"),
    ],
)
def test_public_candidate_plugins_parse_fixture_without_auth(engine, fixture):
    plugin = default_registry().get(engine)
    html = (FIXTURES / fixture).read_text(encoding="utf-8")

    assert plugin.authentication == "none"
    assert plugin.readiness == "enabled"
    assert plugin.validate_contract() == ()
    assert plugin.build_url("europe query", 2, "DE", "normal")
    parsed = plugin.parse(html, query="fixture", page=1, search_type="normal")
    assert len(parsed) == 1
    assert parsed[0].url == f"https://example.test/{engine}"


def test_public_candidate_urls_encode_queries_and_use_no_credentials():
    registry = default_registry()
    expected = {
        "good": "q=europe%20query",
        "xprivo": "q=europe%20query",
        "marginalia": "q=europe%20query",
        "etools": "query=europe%20query",
    }
    for engine, marker in expected.items():
        plugin = registry.get(engine)
        assert marker in plugin.build_url("europe query", 1, "DE", "normal")
        assert plugin.metadata()["authentication"] == "none"


def test_xprivo_contract_covers_the_rendered_search_placeholder():
    plugin = default_registry().get("xprivo")
    interaction = plugin.browser_interaction

    assert interaction is not None
    assert "input[placeholder*='Privat suchen']" in interaction.search_input_selectors
    assert "a.block.py-3" in interaction.serp_ready_selectors
    assert "div.group" in plugin.card_selectors


def test_searxng_requires_explicit_instance_and_remains_auth_free():
    plugin = searxng_plugin("https://public.example/searxng")

    assert plugin.engine_id == "searxng"
    assert plugin.search_url.startswith("https://public.example/searxng/search")
    assert plugin.authentication == "none"
    assert plugin.readiness == "enabled"
    assert plugin.capabilities.transport == "http"
    assert plugin.validate_contract() == ()


def test_searxng_parses_json_results_without_browser():
    plugin = searxng_plugin("http://searxng:8080")
    parsed = plugin.parse(
        '{"results":[{"url":"https://example.test/a","title":"Example","content":"Snippet","engine":"dummy"}]}',
        query="test", page=1, search_type="normal",
    )
    assert len(parsed) == 1
    assert parsed[0].url == "https://example.test/a"
    assert parsed[0].source == "SearXNG:dummy"


def test_searxng_preserves_upstream_engine_in_result_source():
    plugin = searxng_plugin("http://searxng:8080")
    parsed = plugin.parse(
        '{"results":[{"url":"https://example.test/a","title":"Example","engine":"brave"}]}',
        query="test", page=1, search_type="normal",
    )

    assert parsed[0].source == "SearXNG:brave"
    assert parsed[0].extras["searxng_engine"] == "brave"


def test_searxng_normalizes_display_engine_names_for_fusion():
    plugin = searxng_plugin("http://searxng:8080")
    parsed = plugin.parse(
        '{"results":[{"url":"https://example.test/a","title":"Paper","engine":"semantic scholar"}]}',
        query="test", page=1, search_type="normal",
    )

    assert parsed[0].source == "SearXNG:semantic_scholar"


def test_searxng_does_not_block_partial_results_for_one_upstream_captcha():
    plugin = searxng_plugin("http://searxng:8080")
    payload = '{"results":[{"url":"https://example.test/a","title":"Example"}],"errors":[{"engine":"startpage","exception":"captcha"}]}'

    assert plugin.classify("http://searxng:8080/search", payload) is None


def test_metager_is_not_selected_without_a_public_no_auth_route():
    plugin = default_registry().get("metager")

    assert plugin.readiness == "disabled"
    assert "MetaGer key" in plugin.disable_reason


def test_public_plugins_are_visible_in_registry_metadata():
    metadata = {item["engine_id"]: item for item in default_registry().metadata()}

    assert {"metager", "good", "xprivo", "marginalia", "etools"}.issubset(metadata)
    assert all(metadata[engine]["authentication"] == "none" for engine in ("metager", "good", "xprivo", "marginalia", "etools"))


def test_default_registry_rejects_authenticated_plugins():
    class AuthenticatedPlugin(GenericHtmlPlugin):
        engine_id = "authenticated"
        search_url = "https://example.test/search?q={query}"
        authentication = "api_key"
        browser_interaction = BrowserInteraction(
            homepage_url="https://example.test/",
            search_input_selectors=("input[name='q']",),
            submit_selectors=("button[type='submit']",),
            serp_ready_selectors=("main",),
            organic_card_selectors=("article.result",),
        )

        def _build_url(self, query, page, country_code):
            return self.search_url.format(query=query)

    with pytest.raises(ValueError, match="default registry accepts only no-auth plugins"):
        SearchEngineRegistry([AuthenticatedPlugin()])
