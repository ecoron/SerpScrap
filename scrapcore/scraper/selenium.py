"""Headless Chrome SERP retrieval.

This module intentionally does not parse or persist results. A worker owns one
driver, captures pages, and always terminates the browser before returning.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from scrapcore.jobs import CapturedPage, ScrapeFailure, ScrapeJob, ScrapeJobResult
from scrapcore.scraper.browser import (
    ChromeDriverFactory,
    GoogleSearchAdapter,
    screenshot_path,
)

logger = logging.getLogger(__name__)


class SeleniumSearchError(RuntimeError):
    """Base error for a SERP browser operation."""


class MaliciousRequestDetected(SeleniumSearchError):
    """The search engine rejected the automated request."""


class ConsentRequiredError(SeleniumSearchError):
    """A consent page prevented access to the SERP."""


class SerpLoadTimeout(SeleniumSearchError):
    """No recognizable SERP state appeared before the timeout."""


def get_selenium_scraper_by_search_engine_name(
    config: dict, search_engine_name: str, *args, **kwargs
) -> SelScrape:
    """Return a scraper for a supported search engine."""

    if search_engine_name.lower() != "google":
        raise ValueError(f'No Selenium adapter for search engine "{search_engine_name}"')
    return SelScrape(config, *args, **kwargs)


class SelScrape:
    """Retrieve all requested pages for one immutable :class:`ScrapeJob`."""

    def __init__(
        self,
        config: dict,
        job: ScrapeJob,
        driver_factory: ChromeDriverFactory | None = None,
        adapter: GoogleSearchAdapter | None = None,
    ) -> None:
        self.config = config
        self.job = job
        self.driver_factory = driver_factory or ChromeDriverFactory.from_config(config)
        self.adapter = adapter or GoogleSearchAdapter(config)
        self.result: ScrapeJobResult | None = None

    def _wait_for_serp(self, driver) -> None:
        timeout = float(self.config.get("wait_timeout", 15))

        def loaded(current_driver):
            html = current_driver.page_source or ""
            state = self.adapter.classify(current_driver.current_url, html)
            if state:
                return True
            return any(
                current_driver.find_elements(By.CSS_SELECTOR, selector)
                for selector in self.adapter.result_selectors
            )

        try:
            WebDriverWait(driver, timeout).until(loaded)
        except TimeoutException as exc:
            raise SerpLoadTimeout(f"No recognizable Google SERP after {timeout:g}s") from exc

    def _save_screenshot(self, driver, page_number: int) -> str | None:
        if not self.config.get("screenshot", False):
            return None
        path = screenshot_path(
            self.config, self.job.query, self.job.correlation_id, page_number
        )
        driver.save_screenshot(str(path))
        return str(path)

    def _failure(
        self, page_number: int, url: str, category: str, error: Exception, retryable: bool
    ) -> ScrapeFailure:
        logger.warning(
            "SERP capture failed [%s] query=%r page=%s: %s",
            category,
            self.job.query,
            page_number,
            error,
        )
        return ScrapeFailure(
            query=self.job.query,
            search_engine=self.job.search_engine,
            page_number=page_number,
            url=url,
            category=category,
            message=str(error),
            retryable=retryable,
            correlation_id=self.job.correlation_id,
        )

    def retrieve(self) -> ScrapeJobResult:
        pages: list[CapturedPage] = []
        failures: list[ScrapeFailure] = []
        driver = None
        try:
            driver = self.driver_factory.create(proxy=self.job.proxy)
            for page_number in self.job.pages:
                url = self.adapter.build_url(
                    self.job.query, page_number, self.job.search_type
                )
                try:
                    driver.get(url)
                    self._wait_for_serp(driver)
                    html = driver.page_source or ""
                    state = self.adapter.classify(driver.current_url, html)
                    if state == "blocked":
                        raise MaliciousRequestDetected("Google rejected the request")
                    if state == "consent_required":
                        raise ConsentRequiredError("Google consent is required")
                    screenshot = self._save_screenshot(driver, page_number)
                    pages.append(
                        CapturedPage(
                            query=self.job.query,
                            search_engine=self.job.search_engine,
                            page_number=page_number,
                            url=driver.current_url,
                            html=html,
                            requested_at=datetime.now(timezone.utc),
                            requested_by=(
                                f"{self.job.proxy.host}:{self.job.proxy.port}"
                                if self.job.proxy
                                else "localhost"
                            ),
                            screenshot=screenshot,
                        )
                    )
                except MaliciousRequestDetected as exc:
                    failures.append(self._failure(page_number, url, "blocked", exc, False))
                    break
                except ConsentRequiredError as exc:
                    failures.append(
                        self._failure(page_number, url, "consent_required", exc, False)
                    )
                    break
                except SerpLoadTimeout as exc:
                    self._save_screenshot(driver, page_number)
                    failures.append(self._failure(page_number, url, "timeout", exc, True))
                except WebDriverException as exc:
                    failures.append(self._failure(page_number, url, "webdriver", exc, True))
        except Exception as exc:
            pending_pages = self.job.pages[len(pages) + len(failures) :]
            if not pending_pages:
                pending_pages = self.job.pages[:1]
            for page_number in pending_pages:
                url = self.adapter.build_url(
                    self.job.query, page_number, self.job.search_type
                )
                failures.append(
                    self._failure(page_number, url, "browser_startup", exc, True)
                )
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except WebDriverException:
                    logger.exception("Chrome did not terminate cleanly")

        self.result = ScrapeJobResult(
            job=self.job, pages=tuple(pages), failures=tuple(failures)
        )
        return self.result

    def search(self) -> ScrapeJobResult:
        """Backward-compatible alias for :meth:`retrieve`."""

        return self.retrieve()

    def run(self) -> None:
        """Thread-compatible entry point retained for external callers."""

        self.result = self.retrieve()


GoogleSelScrape = SelScrape
