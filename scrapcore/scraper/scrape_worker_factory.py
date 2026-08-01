"""Create and execute browser workers."""

from __future__ import annotations

from scrapcore.jobs import ScrapeJob, ScrapeJobResult
from scrapcore.scraper.browser import ChromeDriverFactory
from scrapcore.scraper.selenium import SelScrape


class ScrapeWorkerFactory:
    """Small injectable factory used by the bounded worker pool."""

    def __init__(self, config: dict, driver_factory: ChromeDriverFactory | None = None):
        self.config = config
        self.driver_factory = driver_factory

    def create(self, job: ScrapeJob) -> SelScrape:
        return SelScrape(
            config=self.config,
            job=job,
            driver_factory=self.driver_factory,
        )

    def execute(self, job: ScrapeJob) -> ScrapeJobResult:
        return self.create(job).retrieve()
