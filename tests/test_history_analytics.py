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
    assert payload["schema_version"] == 1
    assert payload["result_count"] == 1
    assert store.aggregates("providers")["items"][0]["name"] == "bing"


def test_timeseries_compare_and_bounded_export():
    store = _store()
    assert store.timeseries()["points"][0]["searches"] == 2
    comparison = store.compare("a", "b")
    assert comparison["totals"] == {"shared": 0, "added": 1, "removed": 1}
    body, content_type = store.export({}, "csv")
    assert content_type == "text/csv" and "run_id" in body
