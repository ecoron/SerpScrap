"""Orchestrate capture, parsing, persistence, and serialization."""

from __future__ import annotations

import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from scrapcore.cachemanager import CacheManager
from scrapcore.database import ScraperSearch, SearchEngineResultsPage, fixtures, get_session
from scrapcore.jobs import CapturedPage, ScrapeFailure, ScrapeJob, ScrapeJobResult
from scrapcore.logger import Logger
from scrapcore.parsing import Parsing
from scrapcore.proxy import ProxyPool
from scrapcore.repository import SqliteHistoryRepository
from scrapcore.scraper.scrape_worker_factory import ScrapeWorkerFactory
from scrapcore.tools import ScrapeJobGenerator
from scrapcore.validator_config import ValidatorConfig


def utc_now_naive() -> datetime:
    """Return UTC in the naive form used by the existing SQLite schema."""

    return datetime.now(timezone.utc).replace(tzinfo=None)


class Core:
    """Main controller for a complete scrape operation."""

    def __init__(
        self,
        worker_factory: ScrapeWorkerFactory | None = None,
        history_repository: SqliteHistoryRepository | None = None,
    ):
        self.logger: logging.Logger | None = None
        self.worker_factory = worker_factory
        self.history_repository = history_repository or SqliteHistoryRepository()

    def run(self, config: dict):
        ValidatorConfig().validate(config)
        return self.main(return_results=True, config=config)

    @staticmethod
    def _parse_search_engines(config: dict) -> list[str]:
        engines = config.get("search_engines", ["google"])
        if isinstance(engines, str):
            engines = [item.strip() for item in engines.split(",") if item.strip()]
        return sorted(set(engines))

    @staticmethod
    def _get_proxy_pool(config: dict) -> ProxyPool | None:
        if not config.get("proxy_enabled", False) and config.get("use_own_ip", True):
            return None
        return ProxyPool.from_config(config)

    def _init_logger(self, config: dict) -> None:
        configured = Logger()
        configured.setup_logger(level=config.get("log_level", "INFO").upper())
        self.logger = configured.get_logger()

    @staticmethod
    def _group_jobs(
        raw_jobs: list[dict], config: dict, proxy_pool: ProxyPool | None
    ) -> list[ScrapeJob]:
        pages_by_query: dict[tuple[str, str], list[int]] = defaultdict(list)
        for raw_job in raw_jobs:
            pages_by_query[(raw_job["query"], raw_job["search_engine"])].append(
                int(raw_job["page_number"])
            )
        return [
            ScrapeJob(
                query=query,
                search_engine=engine,
                search_type=config.get("search_type", "normal"),
                pages=tuple(sorted(set(pages))),
                proxy=proxy_pool.select(engine) if proxy_pool else None,
            )
            for (query, engine), pages in pages_by_query.items()
        ]

    def _persist_page(
        self,
        captured: CapturedPage,
        config: dict,
        session,
        scraper_search: ScraperSearch,
        cache_manager: CacheManager,
    ) -> SearchEngineResultsPage:
        parser_class = Parsing().get_parser_by_search_engine(captured.search_engine)
        parser = parser_class(config=config, query=captured.query)
        parser.parse(captured.html)

        serp = Parsing().parse_serp(config, parser=parser, query=captured.query)
        serp.search_engine_name = captured.search_engine
        serp.scrape_method = "selenium"
        serp.page_number = captured.page_number
        serp.requested_at = captured.requested_at.replace(tzinfo=None)
        serp.requested_by = captured.requested_by
        serp.status = "successful"
        serp.screenshot = captured.screenshot
        scraper_search.serps.append(serp)
        session.add(serp)
        cache_manager.cache_results(
            parser,
            captured.query,
            captured.search_engine,
            "selenium",
            captured.page_number,
        )
        return serp

    @staticmethod
    def _persist_failure(
        failure: ScrapeFailure, session, scraper_search: ScraperSearch
    ) -> SearchEngineResultsPage:
        serp = SearchEngineResultsPage(
            status=f"{failure.category}: {failure.message}",
            search_engine_name=failure.search_engine,
            scrape_method="selenium",
            page_number=failure.page_number,
            requested_at=utc_now_naive(),
            requested_by="localhost",
            query=failure.query,
            num_results=0,
            no_results=False,
        )
        serp.failure_url = failure.url
        serp.failure_retryable = failure.retryable
        serp.correlation_id = failure.correlation_id
        serp.attempt_count = failure.attempt_count
        scraper_search.serps.append(serp)
        session.add(serp)
        return serp

    def main(self, return_results: bool = False, config: dict | None = None):
        if config is None:
            raise ValueError("config is required")
        self._init_logger(config)
        assert self.logger is not None

        keywords = list(dict.fromkeys(config.get("keywords", [])))
        if not keywords:
            raise ValueError("At least one keyword is required")
        engines = self._parse_search_engines(config)
        proxy_pool = self._get_proxy_pool(config)
        proxies = proxy_pool.endpoints if proxy_pool else [None]
        pages = int(config.get("num_pages_for_keyword", 1))
        num_workers = int(config.get("num_workers", 1))

        cache_manager = CacheManager(config, self.logger)
        session_factory = get_session(config, path=":memory:")
        session = session_factory()
        scraper_search = ScraperSearch(
            number_search_engines_used=len(engines),
            number_proxies_used=len([proxy for proxy in proxies if proxy]),
            number_search_queries=len(keywords),
            started_searching=utc_now_naive(),
            used_search_engines=",".join(engines),
        )

        try:
            fixtures(config, session)
            if proxy_pool:
                proxy_pool.restore_from_db(session)
                if proxy_pool.health_checker:
                    proxy_pool.refresh_health()
                proxy_pool.persist(session, engines)
            raw_jobs = list(
                ScrapeJobGenerator().get(keywords, engines, "selenium", pages)
            )
            if config.get("do_caching", True):
                raw_jobs = cache_manager.filter_scrape_jobs(
                    raw_jobs, session, scraper_search
                )

            jobs = self._group_jobs(raw_jobs, config, proxy_pool)
            factory = self.worker_factory or ScrapeWorkerFactory(config, proxy_pool=proxy_pool)
            results: list[ScrapeJobResult] = []
            if jobs:
                self.logger.info(
                    "Capturing %s query jobs with %s Chrome worker(s)",
                    len(jobs),
                    min(num_workers, len(jobs)),
                )
                with ThreadPoolExecutor(
                    max_workers=min(num_workers, len(jobs)),
                    thread_name_prefix="serpscrap",
                ) as executor:
                    futures = [executor.submit(factory.execute, job) for job in jobs]
                    results = [future.result() for future in futures]

            for result in results:
                for captured in result.pages:
                    self._persist_page(
                        captured,
                        config,
                        session,
                        scraper_search,
                        cache_manager,
                    )
                for failure in result.failures:
                    self._persist_failure(failure, session, scraper_search)

            if proxy_pool:
                proxy_pool.persist(session, engines)

            scraper_search.stopped_searching = utc_now_naive()
            session.add(scraper_search)
            session.commit()

            # Fully materialize the graph before detaching it from the session.
            for serp in scraper_search.serps:
                list(serp.links)
                list(serp.related_keywords)
            session.expunge_all()
            scraper_search.persistence_failures = []
            if config.get("store_history", True):
                try:
                    self.history_repository.persist(config, scraper_search)
                except Exception as exc:
                    self.logger.error("Optional SQLite history persistence failed: %s", exc)
                    scraper_search.persistence_failures.append(str(exc))
            return scraper_search if return_results else None
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
