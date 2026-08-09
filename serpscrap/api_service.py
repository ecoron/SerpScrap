"""Shared job service used by the HTTP API and MCP gateway."""

from __future__ import annotations

import logging
import os
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

from scrapcore.database import Proxy, SearchEngine, SearchEngineProxyStatus, fixtures, get_session
from scrapcore.proxy import ProxyPool
from serpscrap.application import SearchApplication
from serpscrap.configuration_service import SearchConfigurationService
from serpscrap.history_store import SearchHistoryStore
from serpscrap.models import SearchRequest

logger = logging.getLogger(__name__)


class SearchJobService:
    def __init__(
        self,
        application: SearchApplication | None = None,
        store: SearchHistoryStore | None = None,
        max_active_jobs: int | None = None,
        max_queued_jobs: int | None = None,
    ) -> None:
        self.application = application or SearchApplication()
        self.store = store or SearchHistoryStore()
        self.configuration = SearchConfigurationService(self.store)
        self.max_active_jobs = max_active_jobs or max(1, min(int(os.getenv("SERPSCRAP_MAX_ACTIVE_JOBS", "4")), 32))
        self.max_queued_jobs = max_queued_jobs or max(
            self.max_active_jobs,
            min(int(os.getenv("SERPSCRAP_MAX_QUEUED_JOBS", "16")), 128),
        )
        self._executor = ThreadPoolExecutor(max_workers=self.max_active_jobs, thread_name_prefix="serpscrap-job")
        self._futures: set[Future[None]] = set()
        self._lock = threading.Lock()
        self._proxy_refresh_lock = threading.Lock()
        self._proxy_worker_stop = threading.Event()
        self._closed = False
        self._proxy_worker = threading.Thread(
            target=self._proxy_refresh_loop,
            name="serpscrap-proxy-refresh",
            daemon=True,
        )
        self._proxy_worker.start()

    def _proxy_refresh_loop(self) -> None:
        """Refresh configured proxy sources and persist health on a schedule."""

        first_run = True
        while not self._proxy_worker_stop.is_set():
            try:
                configuration = self.configuration.get(include_sensitive=True)["configuration"]
                if not configuration.get("proxy_auto_refresh_enabled", True):
                    first_run = False
                else:
                    self.proxy_status(refresh=True, persist=True)
                    logger.info("Background proxy refresh completed")
            except Exception:
                logger.exception("Background proxy refresh failed")
            if self._proxy_worker_stop.wait(0 if first_run else self._proxy_refresh_interval()):
                break
            first_run = False

    def _proxy_refresh_interval(self) -> float:
        try:
            return max(60.0, float(self.configuration.get(include_sensitive=True)["configuration"].get(
                "proxy_auto_refresh_interval_seconds", 900
            )))
        except (TypeError, ValueError):
            return 900.0

    def submit(self, request: SearchRequest, configuration: dict[str, Any] | None = None) -> str:
        run_id = uuid.uuid4().hex
        with self._lock:
            if self._closed:
                raise RuntimeError("search service is shutting down")
            if len(self._futures) >= self.max_queued_jobs:
                raise RuntimeError("search service job capacity reached")
        options = request.to_config()
        if configuration:
            options["configuration_source"] = configuration["source"]
            options["configuration_revision"] = configuration["revision"]
        self.store.create_run(run_id, ", ".join(request.queries), options)
        with self._lock:
            if self._closed or len(self._futures) >= self.max_queued_jobs:
                future = None
            else:
                future = self._executor.submit(self._run, run_id, request)
                self._futures.add(future)
        if future is None:
            self.store.delete_run(run_id)
            raise RuntimeError("search service is shutting down or at capacity")
        future.add_done_callback(self._forget_future)
        return run_id

    def _forget_future(self, future: Future[None]) -> None:
        with self._lock:
            self._futures.discard(future)

    def readiness(self) -> dict[str, Any]:
        """Return a bounded, JSON-safe readiness snapshot."""

        with self._lock:
            accepting = not self._closed
            pending = len(self._futures)
        database = self.store.healthcheck()
        return {
            "status": "ready" if accepting and database else "not_ready",
            "database": "ok" if database else "unavailable",
            "accepting_jobs": accepting,
            "pending_jobs": pending,
            "max_queued_jobs": self.max_queued_jobs,
        }

    def close(self, wait: bool = True) -> None:
        """Stop accepting jobs and release worker/database resources."""

        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._executor.shutdown(wait=wait, cancel_futures=not wait)
        self._proxy_worker_stop.set()
        if wait and self._proxy_worker.is_alive():
            self._proxy_worker.join(timeout=2)
        self.store.close()

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

    def proxy_status(self, *, refresh: bool = False, persist: bool = False) -> dict[str, Any]:
        """Return a credential-free proxy snapshot for operations and the UI."""

        configuration = self.configuration.get(include_sensitive=True)["configuration"]
        enabled = bool(configuration.get("proxy_enabled") or not configuration.get("use_own_ip", True))
        if not enabled:
            return {"enabled": False, "proxies": [], "summary": {"total": 0, "healthy": 0, "offline": 0}}
        with self._proxy_refresh_lock:
            pool = ProxyPool.from_config(configuration, refresh=False)
        session = get_session(configuration)()
        try:
            engines = list(configuration.get("search_engines") or [])
            fixtures(configuration, session)
            pool.restore_from_db(session)
            if refresh:
                pool.refresh_health()
            if persist:
                pool.persist(session, engines)
            records = {
                (record.ip, int(record.port)): record
                for record in session.query(Proxy).all()
            }
            engine_ids = {engine.id: engine.name for engine in session.query(SearchEngine).all()}
            rows = []
            for endpoint in pool.endpoints:
                health = pool.health[endpoint.key]
                record = records.get((endpoint.host, endpoint.port))
                statuses = {
                    engine_ids[item.search_engine_id]: bool(item.available)
                    for item in session.query(SearchEngineProxyStatus).filter(
                        SearchEngineProxyStatus.proxy_id == (record.id if record else -1)
                    ).all()
                    if item.search_engine_id in engine_ids
                }
                rows.append({
                    "endpoint": endpoint.redacted,
                    "source": endpoint.source,
                    "online": bool(health.online),
                    "latency_ms": health.latency_ms,
                    "failure_count": health.failures,
                    "cooldown_until": health.cooldown_until,
                    "last_error": health.last_error,
                    "engines": statuses,
                })
            rows.sort(key=lambda row: (
                not row["online"],
                row["latency_ms"] is None,
                row["latency_ms"] if row["latency_ms"] is not None else float("inf"),
                row["endpoint"],
            ))
            return {
                "enabled": True,
                "refreshed": bool(refresh),
                "proxies": rows,
                "summary": {
                    "total": len(rows),
                    "healthy": sum(1 for row in rows if row["online"]),
                    "offline": sum(1 for row in rows if not row["online"]),
                },
            }
        finally:
            session.close()

    def refresh_proxies(self) -> dict[str, Any]:
        return self.proxy_status(refresh=True, persist=True)

    def test_proxies(self) -> dict[str, Any]:
        return self.proxy_status(refresh=True, persist=False)
