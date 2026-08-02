"""Shared job service used by the HTTP API and MCP gateway."""

from __future__ import annotations

import threading
import uuid
from typing import Any

from serpscrap.application import SearchApplication
from serpscrap.configuration_service import SearchConfigurationService
from serpscrap.history_store import SearchHistoryStore
from serpscrap.models import SearchRequest


class SearchJobService:
    def __init__(
        self,
        application: SearchApplication | None = None,
        store: SearchHistoryStore | None = None,
    ) -> None:
        self.application = application or SearchApplication()
        self.store = store or SearchHistoryStore()
        self.configuration = SearchConfigurationService(self.store)

    def submit(self, request: SearchRequest, configuration: dict[str, Any] | None = None) -> str:
        run_id = uuid.uuid4().hex
        options = request.to_config()
        if configuration:
            options["configuration_source"] = configuration["source"]
            options["configuration_revision"] = configuration["revision"]
        self.store.create_run(run_id, ", ".join(request.queries), options)
        thread = threading.Thread(target=self._run, args=(run_id, request), daemon=True)
        thread.start()
        return run_id

    def _run(self, run_id: str, request: SearchRequest) -> None:
        self.store.mark_running(run_id)
        config = request.to_config()
        engines = tuple(config.get("search_engines") or ("google",))
        total_jobs = len(request.queries) * len(engines) * int(config.get("num_pages_for_keyword", 1))
        self.store.update_progress(run_id, total_jobs, 0, state="starting")

        def on_progress(event: dict[str, Any]) -> None:
            self.store.update_progress(run_id, int(event.get("total_jobs") or total_jobs), int(event.get("completed_jobs") or 0), str(event.get("engine") or ""), str(event.get("state") or "running"))

        runtime_request = SearchRequest(queries=request.queries, settings={**config, "_progress_callback": on_progress})
        try:
            report = self.application.execute(runtime_request)
            self.store.store_report(run_id, report)
        except Exception as exc:  # pragma: no cover - exercised by API integration tests
            self.store.mark_failed(run_id, str(exc))
            self.store.update_progress(run_id, total_jobs, total_jobs, state="failed")

    def status(self, run_id: str) -> dict[str, Any] | None:
        return self.store.get_run(run_id)

    def events(self, run_id: str) -> list[dict[str, Any]]:
        status = self.status(run_id)
        if status is None:
            return []
        return [{"type": "job_status", "run_id": run_id, **status}]

    def resolve_options(self, options: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
        return self.configuration.resolve_options(options)
