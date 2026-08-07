"""Bounded concurrent execution for configured search-engine plugins."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock, Semaphore
from typing import Any, Protocol
from uuid import uuid4

from serpscrap.diagnostics import (
    DiagnosticArtifactStore,
    JsonLinesProgressSink,
    LoggingProgressSink,
    NullProgressSink,
    ProgressCoordinator,
)
from serpscrap.models import FailureRecord, SearchReport, SearchRequest
from serpscrap.plugins.searchengines.base import EnginePage, SearchEnginePlugin
from serpscrap.plugins.searchengines.browser_flow import BrowserFlowError, HomepageSearchFlow
from serpscrap.plugins.searchengines.fusion import ResultFusion
from serpscrap.plugins.searchengines.registry import SearchEngineRegistry, default_registry
from serpscrap.result_normalizer import normalize_result_url


class PageCapture(Protocol):
    def __call__(self, plugin: SearchEnginePlugin, query: str, country_code: str, page: int, config: dict[str, Any]) -> EnginePage: ...


class SeleniumPageCapture:
    """Default capture adapter; browser ownership stays within one call."""

    def __call__(self, plugin, query, country_code, page, config):
        from scrapcore.scraper.browser import ChromeDriverFactory

        driver = None
        try:
            driver = ChromeDriverFactory.from_config(config).create()
            callback = config.get("_progress_callback")
            if callback is not None:
                callback("driver_created", elapsed_ms=0)
            return HomepageSearchFlow(float(config.get("wait_timeout", 15))).capture(
                driver,
                plugin,
                query,
                country_code,
                page,
                str(config.get("search_type", "normal")),
                correlation_id=config.get("_correlation_id"),
                progress=callback,
                artifact_store=config.get("_artifact_store"),
                consent_action=str(config.get("consent_action", "necessary")),
                interaction_settle_delay=float(config.get("interaction_settle_delay", 0.0)),
            )
        finally:
            if driver is not None:
                driver.quit()


@dataclass(frozen=True, slots=True)
class EngineJob:
    query: str
    engine: str
    country_code: str
    page: int
    correlation_id: str


class MultiEngineRunner:
    """Execute plugins concurrently and return a canonical :class:`SearchReport`."""

    def __init__(
        self,
        registry: SearchEngineRegistry | None = None,
        capture: PageCapture | None = None,
        fusion: ResultFusion | None = None,
    ) -> None:
        self.registry = registry or default_registry()
        self.capture = capture or SeleniumPageCapture()
        self.fusion = fusion or ResultFusion()

    def execute(self, request: SearchRequest) -> SearchReport:
        config = request.to_config()
        country = str(config.get("country_code", "DE")).upper()
        engines = tuple(config.get("search_engines") or ("google",))
        self.registry.validate_selection(engines)
        pages = int(config.get("num_pages_for_keyword", 1))
        workers = int(config.get("num_workers", 1))
        jobs = [
            EngineJob(query, engine, country, page, uuid4().hex[:16])
            for query in request.queries
            for engine in engines
            for page in range(1, pages + 1)
        ]
        started = datetime.now(timezone.utc)
        run_id = uuid4().hex[:16]
        total_jobs = len(jobs)
        if config.get("progress"):
            progress_format = str(config.get("progress_format", "text"))
            sink = (
                JsonLinesProgressSink()
                if progress_format == "jsonl"
                else LoggingProgressSink(logging.getLogger("serpscrap.progress"))
            )
        else:
            sink = NullProgressSink()
        progress = ProgressCoordinator(run_id, total_jobs, sink)

        def emit_progress(*, state: str, **kwargs: Any) -> None:
            progress.emit(state=state, **kwargs)
            callback = config.get("_progress_callback")
            if callback is not None:
                callback({"total_jobs": progress.total_jobs, "completed_jobs": progress.completed_jobs, "state": state, **kwargs})
        artifact_store = None
        if config.get("diagnostic_html"):
            artifact_store = DiagnosticArtifactStore(
                config.get("diagnostic_dir", "logs/phase7"),
                run_id,
                max_bytes_per_file=int(config.get("diagnostic_max_bytes_per_file", 2 * 1024 * 1024)),
                max_total_bytes=int(config.get("diagnostic_max_total_bytes", 20 * 1024 * 1024)),
                max_artifacts_per_job=int(config.get("diagnostic_max_artifacts_per_job", 10)),
            )
        rows: list[dict[str, Any]] = []
        failures: list[FailureRecord] = []
        terminal_summaries: list[dict[str, Any]] = []
        lock = Lock()
        limits: dict[str, Semaphore] = {}
        per_engine = config.get("engine_workers_by_engine", {})
        for engine in engines:
            limit = int(per_engine.get(engine, config.get("engine_workers", workers)))
            limits[engine] = Semaphore(max(1, min(workers, limit)))

        def run_job(job: EngineJob):
            plugin = self.registry.get(job.engine)
            plugin.validate_request(
                search_type=str(config.get("search_type", "normal")),
                country_code=job.country_code,
            )
            with limits[job.engine]:
                job_config = dict(config)
                job_config.update({
                    "_correlation_id": job.correlation_id,
                    "_artifact_store": artifact_store,
                    "_progress_callback": lambda state, **kwargs: emit_progress(
                        correlation_id=job.correlation_id,
                        engine=job.engine,
                        page=job.page,
                        state=state,
                        **kwargs,
                    ),
                })
                emit_progress(
                    correlation_id=job.correlation_id,
                    engine=job.engine,
                    page=job.page,
                    state="job_started",
                )
                page = self.capture(plugin, job.query, job.country_code, job.page, job_config)
            state = plugin.classify(page.url, page.html, visible_text=page.visible_text)
            if state:
                raise RuntimeError(f"{state}: {job.engine} rejected the request")
            parsed = plugin.parse(
                page.html,
                query=job.query,
                page=job.page,
                search_type=str(config.get("search_type", "normal")),
            )
            if not parsed:
                category = "empty" if plugin.classify_empty(
                    page.url, page.html, visible_text=page.visible_text
                ) else "malformed"
                emit_progress(
                    correlation_id=job.correlation_id,
                    engine=job.engine,
                    page=job.page,
                    state="state_classified",
                    url=page.url,
                    error_category=category,
                    result_count=0,
                )
                raise BrowserFlowError(
                    category,
                    f"no organic results parsed for {job.engine}",
                    url=page.url,
                    result_count=0,
                )
            values = [
                item.to_dict(
                    query=job.query,
                    engine=job.engine,
                    country_code=job.country_code,
                    page=job.page,
                )
                for item in parsed
            ]
            for value in values:
                value["query_num_results_page"] = len(parsed)
            emit_progress(
                correlation_id=job.correlation_id,
                engine=job.engine,
                page=job.page,
                state="state_classified",
                url=page.url,
                result_count=len(parsed),
            )
            emit_progress(
                correlation_id=job.correlation_id,
                engine=job.engine,
                page=job.page,
                state="results_parsed",
                result_count=len(parsed),
            )
            return values, page.url

        with ThreadPoolExecutor(max_workers=max(1, min(workers, len(jobs) or 1)), thread_name_prefix="serpscrap-engine") as executor:
            futures = {executor.submit(run_job, job): job for job in jobs}
            for future in as_completed(futures):
                job = futures[future]
                try:
                    values = future.result()
                except Exception as exc:
                    message = str(exc)
                    category, _, detail = message.partition(": ")
                    failure_url = getattr(exc, "url", None)
                    failure = FailureRecord(
                        query=job.query,
                        search_engine=job.engine,
                        page_number=job.page,
                        url=failure_url,
                        category=category or "plugin",
                        message=detail or message,
                        retryable=category in set(config.get("retryable_engine_categories", ("timeout", "navigation_state", "network"))),
                        attempt_count=1,
                        country_code=job.country_code,
                        plugin_version=self.registry.get(job.engine).plugin_version,
                        correlation_id=job.correlation_id,
                    )
                    if artifact_store is not None:
                        artifact_store.record_terminal(
                            engine=job.engine,
                            page=job.page,
                            correlation_id=job.correlation_id,
                            state="failed",
                            error_category=category or "plugin",
                            result_count=getattr(exc, "result_count", None),
                            url=failure_url,
                        )
                    emit_progress(
                        correlation_id=job.correlation_id,
                        engine=job.engine,
                        page=job.page,
                        state="job_failed",
                        error_category=category or "plugin",
                        result_count=getattr(exc, "result_count", None),
                        terminal=True,
                    )
                    with lock:
                        failures.append(failure)
                        terminal_summaries.append({
                            "engine": job.engine,
                            "page": job.page,
                            "state": "failed",
                            "category": category or "plugin",
                            "result_count": getattr(exc, "result_count", None),
                            "url": failure_url,
                            "correlation_id": job.correlation_id,
                        })
                else:
                    values, page_url = values
                    if artifact_store is not None:
                        artifact_store.record_terminal(
                            engine=job.engine,
                            page=job.page,
                            correlation_id=job.correlation_id,
                            state="completed",
                            result_count=len(values),
                            url=page_url,
                        )
                    emit_progress(
                        correlation_id=job.correlation_id,
                        engine=job.engine,
                        page=job.page,
                        state="job_completed",
                        result_count=len(values),
                        terminal=True,
                    )
                    with lock:
                        rows.extend(values)
                        terminal_summaries.append({
                            "engine": job.engine,
                            "page": job.page,
                            "state": "completed",
                            "category": None,
                            "result_count": len(values),
                            "url": page_url,
                            "correlation_id": job.correlation_id,
                        })

        weights = {plugin.engine_id: float(plugin.market_share or 0.0) for plugin in self.registry}
        configured = config.get("engine_weights") or {}
        weights.update({str(key): float(value) for key, value in configured.items()})
        active = {engine: weight for engine, weight in weights.items() if engine in engines}
        unreported = [engine for engine in engines if active.get(engine, 0.0) == 0.0]
        fallback = float(config.get("other_market_share", 0.63)) / max(1, len(unreported))
        for engine in unreported:
            active[engine] = fallback
        total = sum(active.values()) or 1.0
        active = {engine: value / total for engine, value in active.items()}
        families = {plugin.engine_id: plugin.provider_family for plugin in self.registry}
        ranking = config.get("ranking", {})
        if ranking:
            from serpscrap.plugins.searchengines.fusion import FusionSettings

            self.fusion = ResultFusion(FusionSettings(
                rrf_k=int(ranking.get("rrf_k", 60)),
                provider_family_cap=bool(ranking.get("provider_family_cap", False)),
            ))
        ranked = self.fusion.fuse(rows, active, families)
        for row in ranked:
            url_info = normalize_result_url(row.get("serp_url"), row.get("serp_type"))
            row["source_url"] = url_info["source_url"]
            row["canonical_url"] = url_info["canonical_url"]
            row["serp_url"] = url_info["canonical_url"]
            row["result_kind"] = url_info["result_kind"]
            row["relevance"] = float(row.get("relevance_score") or 0.0)
        ranked.sort(key=lambda row: (str(row.get("query") or ""), int(row.get("best_rank") or 0), -float(row.get("relevance_score") or 0.0), str(row.get("serp_url") or "")))
        # Preserve query order while keeping fusion deterministic within each query.
        query_index = {query: index for index, query in enumerate(request.queries)}
        ranked.sort(key=lambda row: (query_index.get(str(row.get("query")), len(query_index)), -float(row.get("relevance_score") or 0.0), str(row.get("serp_url") or "")))
        stopped = datetime.now(timezone.utc)
        return SearchReport(
            results=ranked,
            failures=sorted(failures, key=lambda item: (item.query, item.search_engine, item.page_number)),
            started_at=started,
            stopped_at=stopped,
            report_metadata={
                "fusion_version": self.fusion.version,
                "fusion_snapshot_id": config.get("fusion_snapshot_id", "europe-2026-07"),
                "market_share_weights": active,
                "market_share_fallback": fallback,
                "provider_families": families,
                "plugin_metadata": self.registry.metadata(),
                "run_id": run_id,
                "progress_completed_jobs": progress.completed_jobs,
                "diagnostic_manifest": str(artifact_store.manifest_path) if artifact_store else None,
                "terminal_summaries": sorted(
                    terminal_summaries,
                    key=lambda item: (item["engine"], item["page"]),
                ),
                "outcome_counts": {
                    category: sum(1 for item in terminal_summaries if (item["category"] or item["state"]) == category)
                    for category in sorted({item["category"] or item["state"] for item in terminal_summaries})
                },
            },
        )
