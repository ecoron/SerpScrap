"""Bounded concurrent execution for configured search-engine plugins."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock, Semaphore
from typing import Any, Protocol

from serpscrap.models import FailureRecord, SearchReport, SearchRequest
from serpscrap.plugins.searchengines.base import EnginePage, SearchEnginePlugin
from serpscrap.plugins.searchengines.fusion import ResultFusion
from serpscrap.plugins.searchengines.registry import SearchEngineRegistry, default_registry


class PageCapture(Protocol):
    def __call__(self, plugin: SearchEnginePlugin, query: str, country_code: str, page: int, config: dict[str, Any]) -> EnginePage: ...


class SeleniumPageCapture:
    """Default capture adapter; browser ownership stays within one call."""

    def __call__(self, plugin, query, country_code, page, config):
        from scrapcore.scraper.browser import ChromeDriverFactory

        url = plugin.build_url(query, page, country_code, str(config.get("search_type", "normal")))
        driver = None
        try:
            driver = ChromeDriverFactory.from_config(config).create()
            driver.get(url)
            return EnginePage(
                url=driver.current_url or url,
                html=driver.page_source or "",
                query=query,
                engine=plugin.engine_id,
                country_code=country_code,
                page=page,
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
        jobs = [EngineJob(query, engine, country, page) for query in request.queries for engine in engines for page in range(1, pages + 1)]
        started = datetime.now(timezone.utc)
        rows: list[dict[str, Any]] = []
        failures: list[FailureRecord] = []
        lock = Lock()
        limits: dict[str, Semaphore] = {}
        per_engine = config.get("engine_workers_by_engine", {})
        for engine in engines:
            limit = int(per_engine.get(engine, config.get("engine_workers", workers)))
            limits[engine] = Semaphore(max(1, min(workers, limit)))

        def run_job(job: EngineJob):
            plugin = self.registry.get(job.engine)
            if plugin.supported_countries and job.country_code not in plugin.supported_countries:
                raise ValueError(f"{job.engine} does not support country {job.country_code}")
            with limits[job.engine]:
                page = self.capture(plugin, job.query, job.country_code, job.page, config)
            state = plugin.classify(page.url, page.html)
            if state:
                raise RuntimeError(f"{state}: {job.engine} rejected the request")
            parsed = plugin.parse(
                page.html,
                query=job.query,
                page=job.page,
                search_type=str(config.get("search_type", "normal")),
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
            return values

        with ThreadPoolExecutor(max_workers=max(1, min(workers, len(jobs) or 1)), thread_name_prefix="serpscrap-engine") as executor:
            futures = {executor.submit(run_job, job): job for job in jobs}
            for future in as_completed(futures):
                job = futures[future]
                try:
                    values = future.result()
                except Exception as exc:
                    message = str(exc)
                    category, _, detail = message.partition(": ")
                    failure = FailureRecord(
                        query=job.query,
                        search_engine=job.engine,
                        page_number=job.page,
                        url=None,
                        category=category or "plugin",
                        message=detail or message,
                        retryable=category in {"timeout", "rate_limited", "network"},
                        attempt_count=1,
                        country_code=job.country_code,
                        plugin_version=self.registry.get(job.engine).plugin_version,
                    )
                    with lock:
                        failures.append(failure)
                else:
                    with lock:
                        rows.extend(values)

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
            },
        )
