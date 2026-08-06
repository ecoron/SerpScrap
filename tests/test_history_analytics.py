from datetime import datetime, timezone

from serpscrap.history_store import SearchHistoryStore
from serpscrap.models import FailureRecord, SearchReport


def _store():
    store = SearchHistoryStore("sqlite:///:memory:")
    store.create_run("a", "alpha", {"country_code": "DE"})
    store.store_report("a", SearchReport(results=[{"url": "https://example.org/a", "search_engine": "bing"}], started_at=datetime.now(timezone.utc), stopped_at=datetime.now(timezone.utc)))
    store.create_run("b", "beta", {"country_code": "DE"})
    store.store_report("b", SearchReport(results=[{"url": "https://example.org/b", "search_engine": "google"}], failures=[FailureRecord("beta", "google", 1, None, "timeout", "x", True)], started_at=datetime.now(timezone.utc), stopped_at=datetime.now(timezone.utc)))
    return store


def test_analytics_contract_and_provider_aggregation():
    store = _store()
    payload = store.analytics(filters={"provider": "bing"})
    assert payload["schema_version"] == 2
    assert payload["scope"]["timezone"] == "UTC"
    assert "freshness" in payload["scope"]
    assert payload["result_count"] == 1
    assert store.aggregates("providers")["items"][0]["name"] == "bing"
    assert store.aggregates("providers")["semantics"]["ranking"]
    assert store.aggregates("providers", limit=1, offset=0)["limit"] == 1
    assert store.timeseries()["semantics"]["run_count"] == "run-scoped"


def test_timeseries_compare_and_bounded_export():
    store = _store()
    assert store.timeseries()["points"][0]["searches"] == 2
    comparison = store.compare("a", "b")
    assert comparison["totals"]["shared"] == 0
    assert comparison["totals"]["new"] == 1
    assert comparison["totals"]["lost"] == 1
    body, content_type = store.export({}, "csv")
    assert content_type == "text/csv" and "run_id" in body


def test_compare_normalizes_urls_and_classifies_rank_changes():
    store = SearchHistoryStore("sqlite:///:memory:")
    options = {"country_code": "DE", "search_type": "normal", "search_engines": ["bing"], "num_pages_for_keyword": 1, "num_results_per_page": 10}
    now = datetime.now(timezone.utc)
    store.create_run("left", "same query", options)
    store.store_report("left", SearchReport(results=[
        {"url": "http://www.example.org/a/?utm_source=test", "serp_rank": 1, "search_engine": "bing"},
        {"url": "https://lost.example.org/", "serp_rank": 2, "search_engine": "bing"},
    ], started_at=now, stopped_at=now))
    store.create_run("right", "same query", options)
    store.store_report("right", SearchReport(results=[
        {"url": "https://example.org/a", "serp_rank": 3, "search_engine": "bing"},
        {"url": "https://new.example.org/", "serp_rank": 1, "search_engine": "bing"},
    ], started_at=now, stopped_at=now))

    comparison = store.compare("left", "right")

    assert comparison["identity_key_version"] == 1
    assert comparison["compatibility"]["compatible"] is True
    assert comparison["totals"]["moved"] == 1
    assert comparison["totals"]["new"] == 1
    assert comparison["totals"]["lost"] == 1
    assert comparison["compatibility"]["fingerprint"]
    assert comparison["provider_overlap"] == ["bing"]
    assert comparison["domains"]["rank_changed"] == ["example.org"]


def test_incomplete_scope_and_export_preflight_metadata():
    store = _store()
    scoped = store.analytics(filters={"from": "2000-01-01", "to": "2099-01-01"})
    assert scoped["scope"]["data_status"] == "insufficient"
    preflight = store.export_preflight({"provider": "bing"}, "csv", 99999)
    assert preflight["row_limit"] == 5000
    assert preflight["estimated_rows"] == 1
    body, _ = store.export({"provider": "bing"}, "csv")
    assert "# schema_version=2" in body
    assert "# identity_key_version=1" in body
