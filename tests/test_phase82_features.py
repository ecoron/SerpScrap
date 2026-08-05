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
    root = Path(__file__).parents[1] / "ui"
    template = "\n".join((root / "templates" / "pages" / name).read_text(encoding="utf-8") for name in ("search.html", "history.html"))
    javascript = (root / "static" / "js" / "views" / "results.js").read_text(encoding="utf-8")
    history_javascript = (root / "static" / "js" / "views" / "history.js").read_text(encoding="utf-8")
    app = (root / "static" / "js" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "css" / "layout.css").read_text(encoding="utf-8")
    assert "groupResults" in javascript
    assert "group.engines" in javascript
    assert "delete-current" in template
    assert "delete-all" in template
    assert "progress-card" in template
    assert "progress-eta" in template
    assert "renderResults" in app
    assert "overflow-x: auto" in (root / "static" / "css" / "components.css").read_text(encoding="utf-8")
    assert "grid-template-columns" in css
    assert "Inspect" in app
    assert "history-detail-row" in app
    assert "AbortController" in history_javascript
    assert "identity_key_version" not in history_javascript
    assert "history-export-json" in template
    assert "history-country" in template
    assert "compare-moved" in template


def test_history_exposes_progress_state(tmp_path):
    store = SearchHistoryStore(f"sqlite:///{tmp_path / 'history.db'}")
    store.create_run("run-progress", "example", {})
    store.mark_running("run-progress")
    store.update_progress("run-progress", 8, 3, "bing", "results_parsed")
    status = store.get_run("run-progress")
    assert status["progress"]["total_jobs"] == 8
    assert status["progress"]["completed_jobs"] == 3
    assert status["progress"]["engine"] == "bing"


def test_frontend_polish_contract_covers_cancellation_responsive_states_and_motion():
    root = Path(__file__).parents[1] / "ui"
    client = (root / "static" / "js" / "api-client.js").read_text(encoding="utf-8")
    charts = (root / "static" / "js" / "charts.js").read_text(encoding="utf-8")
    base = (root / "static" / "css" / "base.css").read_text(encoding="utf-8")
    layout = (root / "static" / "css" / "layout.css").read_text(encoding="utf-8")
    history = (root / "static" / "css" / "history.css").read_text(encoding="utf-8")
    plan = (root.parent / "docs" / "a2ui-frontend-polish.md").read_text(encoding="utf-8")

    assert "AbortController" in client
    assert "setTimeout" in client
    assert "Exact values are available in the table below." in charts
    assert "prefers-reduced-motion" in base
    assert "focus-visible" in base
    assert "minmax" in layout
    assert "@media (max-width:700px)" in history
    assert "## Acceptance Criteria" in plan


def test_configuration_ui_contract_uses_schema_groups_and_safe_save_reset_flow():
    root = Path(__file__).parents[1]
    template = (root / "ui" / "templates" / "pages" / "configuration.html").read_text(encoding="utf-8")
    javascript = (root / "ui" / "static" / "js" / "views" / "configuration.js").read_text(encoding="utf-8")
    styles = (root / "ui" / "static" / "css" / "pages.css").read_text(encoding="utf-8")
    service = (root / "serpscrap" / "configuration_service.py").read_text(encoding="utf-8")

    for marker in ("configuration-groups", "config-error-summary", "reset-config", "reset-changes", "config-dirty-label"):
        assert marker in template
    for marker in ("loaded.groups", "loaded.fields", "Unsaved changes", "/configuration/reset", "beforeunload", "data-config-key=\"search_engines\""):
        assert marker in javascript
    for marker in ("configuration-group", "configuration-actions", "config-engine-grid", "configuration-source"):
        assert marker in styles
    for marker in ("SCHEMA_VERSION = 2", "initial_defaults", "SENSITIVE_KEYS", "FIELD_DEFINITIONS"):
        assert marker in service
