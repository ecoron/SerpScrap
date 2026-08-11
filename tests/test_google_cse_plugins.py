from pathlib import Path

import pytest

from serpscrap.plugins.searchengines.registry import default_registry


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "searchengines" / "google_cse" / "valid_serp.html"


ENGINES = ("altpower", "blackle", "kiddle", "kidrex", "poper")


@pytest.mark.parametrize("engine", ENGINES)
def test_google_cse_wrappers_are_registered_and_parse_results(engine):
    plugin = default_registry().get(engine)
    parsed = plugin.parse(FIXTURE.read_text(encoding="utf-8"), query="fixture", page=1, search_type="normal")

    assert plugin.provider_family == "google_cse"
    assert plugin.authentication == "none"
    assert plugin.readiness in {"experimental", "disabled"}
    assert plugin.validate_contract() == ()
    assert len(parsed) == 2
    assert parsed[0].url == "https://example.test/one"
    assert plugin.title_selectors
    assert plugin.snippet_selectors


@pytest.mark.parametrize("engine", ENGINES)
def test_google_cse_wrapper_urls_encode_queries(engine):
    plugin = default_registry().get(engine)
    url = plugin.build_url("europe query", 2, "DE", "normal")

    assert "europe%20query" in url
    assert "page=2" in url


def test_google_cse_plugins_are_visible_in_metadata():
    metadata = {item["engine_id"]: item for item in default_registry().metadata()}

    assert set(ENGINES).issubset(metadata)
    assert all(metadata[engine]["provider_family"] == "google_cse" for engine in ENGINES)


def test_experimental_google_cse_plugins_can_be_selected_for_live_verification():
    registry = default_registry()

    selectable = tuple(
        engine for engine in ENGINES if registry.get(engine).readiness == "experimental"
    )
    selected = registry.validate_selection(selectable)

    assert tuple(plugin.engine_id for plugin in selected) == selectable
