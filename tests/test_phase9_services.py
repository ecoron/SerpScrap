import threading
from datetime import datetime, timezone

import pytest

from serpscrap.api_service import SearchJobService
from serpscrap.history_store import SearchHistoryStore
from serpscrap.models import SearchReport, SearchRequest


def _request() -> SearchRequest:
    return SearchRequest(queries=("example",), settings={"keywords": ["example"]})


class BlockingApplication:
    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()

    def execute(self, request: SearchRequest) -> SearchReport:
        self.started.set()
        self.release.wait(timeout=2)
        now = datetime.now(timezone.utc)
        return SearchReport(started_at=now, stopped_at=now)


def test_job_service_limits_pending_jobs_and_rejects_after_shutdown(tmp_path):
    application = BlockingApplication()
    store = SearchHistoryStore(f"sqlite:///{tmp_path / 'history.db'}")
    service = SearchJobService(application, store, max_active_jobs=1, max_queued_jobs=1)

    service.submit(_request())
    assert application.started.wait(timeout=1)
    with pytest.raises(RuntimeError, match="capacity"):
        service.submit(_request())

    application.release.set()
    service.close()
    assert service.readiness()["status"] == "not_ready"
    with pytest.raises(RuntimeError, match="shutting down"):
        service.submit(_request())


def test_store_health_and_filtered_offset_pagination(tmp_path):
    store = SearchHistoryStore(f"sqlite:///{tmp_path / 'history.db'}")
    assert store.healthcheck()
    store.create_run("run", "example", {})
    store.store_report(
        "run",
        SearchReport(
            results=[
                {"search_engine": "fixture", "result_kind": "organic", "id": 1},
                {"search_engine": "fixture", "result_kind": "image", "id": 2},
                {"search_engine": "fixture", "result_kind": "organic", "id": 3},
            ]
        ),
    )

    rows = store.list_results(run_id="run", result_kind="organic", offset=1, limit=1)
    assert [row["id"] for row in rows] == [3]
    store.close()
