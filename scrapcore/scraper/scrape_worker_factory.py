"""Create and execute browser workers."""

from __future__ import annotations

from scrapcore.jobs import ScrapeJob, ScrapeJobResult
from scrapcore.proxy import ProxyPool
from scrapcore.scraper.browser import (
    ChromeDriverFactory,
    RequestPacer,
    RequestPolicy,
    RunCircuitBreaker,
)
from scrapcore.scraper.selenium import SelScrape


class ScrapeWorkerFactory:
    """Small injectable factory used by the bounded worker pool."""

    def __init__(
        self,
        config: dict,
        driver_factory: ChromeDriverFactory | None = None,
        proxy_pool: ProxyPool | None = None,
    ):
        self.config = config
        self.driver_factory = driver_factory
        self.proxy_pool = proxy_pool
        policy = RequestPolicy.from_config(config)
        self.pacer = RequestPacer(policy)
        self.circuit_breaker = RunCircuitBreaker(policy.block_threshold)

    def create(self, job: ScrapeJob) -> SelScrape:
        return SelScrape(
            config=self.config,
            job=job,
            driver_factory=self.driver_factory,
            pacer=self.pacer,
            circuit_breaker=self.circuit_breaker,
            proxy_selector=(
                lambda engine, current: self.proxy_pool.select(engine, exclude=current)
                if self.proxy_pool
                else None
            ),
            proxy_failure_reporter=self.proxy_pool.mark_failure if self.proxy_pool else None,
            proxy_success_reporter=self.proxy_pool.mark_success if self.proxy_pool else None,
        )

    def execute(self, job: ScrapeJob) -> ScrapeJobResult:
        return self.create(job).retrieve()
