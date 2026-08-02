from datetime import datetime, timezone
from pathlib import Path

from serpscrap.history_store import SearchHistoryStore
from serpscrap.models import FailureRecord, SearchReport


def test_history_exposes_engine_attributed_failures(tmp_path):
    store = SearchHistoryStore(f"sqlite:///{tmp_path / 'history.db'}")
    store.create_run("run-1", "example", {})
    store.store_report(
        "run-1",
        SearchReport(
            results=[],
            failures=[FailureRecord(query="example", search_engine="bing", page_number=1, url=None, category="timeout", message="timed out", retryable=True)],
            started_at=datetime.now(timezone.utc),
            stopped_at=datetime.now(timezone.utc),
        ),
    )
    assert store.get_run("run-1")["failures"][0]["search_engine"] == "bing"
    assert store.list_failures("run-1")[0]["category"] == "timeout"


def test_history_can_delete_one_run_or_all_runs(tmp_path):
    store = SearchHistoryStore(f"sqlite:///{tmp_path / 'history.db'}")
    store.create_run("run-1", "one", {})
    store.create_run("run-2", "two", {})
    assert store.delete_run("run-1") is True
    assert store.get_run("run-1") is None
    assert store.delete_all_runs() == 1
    assert store.list_runs() == []


def test_ui_contract_contains_grouped_engine_and_delete_controls():
    document = (Path(__file__).parents[1] / "ui" / "index.html").read_text(encoding="utf-8")
    assert "groupedResults" in document
    assert "group.engines" in document
    assert "delete-current" in document
    assert "delete-all" in document
    assert "progress-card" in document
    assert "progress-eta" in document
    assert "overflow-y: auto" in document
    assert "overflow: visible" in document
    assert "history-table" in document
    assert "nth-child(1)" in document
    assert "delete-historical').disabled = !historicalRunId" in document


def test_history_exposes_progress_state(tmp_path):
    store = SearchHistoryStore(f"sqlite:///{tmp_path / 'history.db'}")
    store.create_run("run-progress", "example", {})
    store.mark_running("run-progress")
    store.update_progress("run-progress", 8, 3, "bing", "results_parsed")
    status = store.get_run("run-progress")
    assert status["progress"]["total_jobs"] == 8
    assert status["progress"]["completed_jobs"] == 3
    assert status["progress"]["engine"] == "bing"
