"""Common execution service for TopicPlugin implementations."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any
from urllib.request import Request, urlopen

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from scrapcore.scraper.browser import (
    ChromeDriverFactory,
    RequestPacer,
    RequestPolicy,
    RunCircuitBreaker,
)
from serpscrap.topic_plugins import (
    AllegroShoppingPlugin,
    BilligerShoppingPlugin,
    EtsyShoppingPlugin,
    FruugoShoppingPlugin,
    GeizhalsShoppingPlugin,
    IdealoShoppingPlugin,
    KauflandShoppingPlugin,
    NewsSourcePlugin,
)
from serpscrap.topic_registry import TopicPluginRegistry
from serpscrap.topics import TopicReport, TopicRequest, deduplicate


def default_topic_registry() -> TopicPluginRegistry:
    return TopicPluginRegistry(
        (NewsSourcePlugin(), GeizhalsShoppingPlugin(), IdealoShoppingPlugin(), BilligerShoppingPlugin(),
         FruugoShoppingPlugin(), KauflandShoppingPlugin(), AllegroShoppingPlugin(), EtsyShoppingPlugin())
    )


class TopicBrowserError(RuntimeError):
    """A typed error while loading a topic result page in Chrome."""

    def __init__(self, category: str, message: str) -> None:
        super().__init__(message)
        self.category = category


class TopicBrowserTransport:
    """Load topic pages with the same configured Chrome stack as SERPs."""

    blocked_markers = (
        "access denied", "forbidden", "unusual traffic", "verify you are human",
        "checking your browser", "cf-chl-captcha", "g-recaptcha", "automated queries",
    )
    consent_markers = ("cookie settings", "accept cookies", "cookie consent", "consent required")
    rate_limited_markers = ("too many requests", "rate limit", "try again later")

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        policy = RequestPolicy.from_config(self.config)
        self.pacer = RequestPacer(policy)
        self.circuit_breaker = RunCircuitBreaker(policy.block_threshold)
        self.policy = policy
        self.driver_factory = ChromeDriverFactory.from_config(self.config)

    @staticmethod
    def _visible_text(driver: Any) -> str:
        try:
            return str(driver.find_element(By.TAG_NAME, "body").text or "")
        except (AttributeError, WebDriverException):
            return str(getattr(driver, "page_source", "") or "")

    @classmethod
    def _classify(cls, driver: Any, payload: str) -> str | None:
        text = f"{getattr(driver, 'current_url', '')} {cls._visible_text(driver)} {payload}".lower()
        if any(marker in text for marker in cls.blocked_markers):
            return "blocked"
        if any(marker in text for marker in cls.rate_limited_markers):
            return "rate_limited"
        if any(marker in text for marker in cls.consent_markers):
            return "consent_required"
        return None

    def fetch(self, url: str, plugin: Any = None) -> str:
        if self.circuit_breaker.open:
            raise TopicBrowserError("circuit_open", "topic browser circuit breaker is open")
        last_error: TopicBrowserError | None = None
        for attempt in range(self.policy.retry_limit + 1):
            driver = None
            try:
                self.pacer.wait()
                driver = self.driver_factory.create()
                driver.get(url)
                timeout = float(self.config.get("wait_timeout", 15))
                try:
                    WebDriverWait(driver, timeout).until(
                        lambda current: bool(getattr(current, "page_source", ""))
                    )
                except TimeoutException as exc:
                    raise TopicBrowserError(
                        "timeout", f"topic page did not load after {timeout:g}s"
                    ) from exc
                payload = str(getattr(driver, "page_source", "") or "")
                state = self._classify(driver, payload)
                if state == "blocked":
                    self.circuit_breaker.record_block()
                    raise TopicBrowserError("blocked", "topic provider rejected the browser request")
                if state == "rate_limited":
                    self.circuit_breaker.record_block()
                    raise TopicBrowserError("rate_limited", "topic provider requested a lower request rate")
                if state == "consent_required":
                    raise TopicBrowserError("consent_required", "topic provider requires consent")
                if plugin is not None:
                    plugin_state = plugin.classify(payload)
                    if plugin_state:
                        raise TopicBrowserError(plugin_state, f"topic provider returned {plugin_state}")
                return payload
            except TopicBrowserError as exc:
                if exc.category not in {"timeout", "webdriver"} or attempt >= self.policy.retry_limit:
                    raise
                last_error = exc
                self.pacer.backoff(attempt + 1)
            except WebDriverException as exc:
                if attempt >= self.policy.retry_limit:
                    raise TopicBrowserError("webdriver", str(exc)) from exc
                last_error = TopicBrowserError("webdriver", str(exc))
                self.pacer.backoff(attempt + 1)
            finally:
                if driver is not None:
                    try:
                        driver.quit()
                    except WebDriverException:
                        pass
        assert last_error is not None
        raise last_error


class TopicService:
    def __init__(
        self,
        registry: TopicPluginRegistry | None = None,
        fetcher: Callable[[str], str] | None = None,
        config: dict[str, Any] | None = None,
        browser_transport: TopicBrowserTransport | None = None,
    ) -> None:
        self.registry = registry or default_topic_registry()
        self.config = config or {}
        self.fetcher = fetcher
        self.browser_transport = browser_transport or (
            TopicBrowserTransport(self.config) if fetcher is None else None
        )

    def configure(self, config: dict[str, Any]) -> None:
        """Use the current shared browser/scraping configuration for topics."""
        self.config = config
        self.browser_transport = TopicBrowserTransport(config)

    @staticmethod
    def _fetch(url: str) -> str:
        with urlopen(Request(url, headers={"User-Agent": "SerpScrap/2.0"}), timeout=20) as response:
            return response.read().decode(
                response.headers.get_content_charset() or "utf-8", errors="replace"
            )

    def execute(self, request: TopicRequest) -> TopicReport:
        started = time.perf_counter()
        report = TopicReport(request.topic, request.query)
        plugins = self.registry.find(
            topic=request.topic, country=request.country, language=request.language
        )
        if not plugins:
            raise ValueError(f"no enabled source for topic {request.topic!r}")
        for plugin in plugins:
            source = plugin.source_id or plugin.topic_id
            if request.sources and source not in request.sources and plugin.topic_id not in request.sources:
                continue
            status = {"status": "failed", "transport": plugin.capabilities.transport, "topic": plugin.topic_id}
            try:
                effective = plugin.build_request(request)
                url = plugin.build_url(effective, page=effective.page)
                if self.fetcher is not None:
                    payload = self.fetcher(url)
                elif plugin.capabilities.transport == "browser":
                    transport = self.browser_transport or TopicBrowserTransport(self.config)
                    payload = transport.fetch(url, plugin)
                else:
                    payload = self._fetch(url)
                state = plugin.classify(payload)
                if state:
                    raise RuntimeError(state)
                results = [
                    plugin.normalize(item)
                    for item in plugin.parse(payload, request=effective, page=effective.page)
                ]
                report.results.extend(results)
                status.update({"status": "ok", "result_count": len(results), "url": url})
            except Exception as exc:
                report.errors.append(
                    {"source": source, "category": type(exc).__name__, "message": str(exc)}
                )
                status["error"] = str(exc)
                if isinstance(exc, TopicBrowserError):
                    status["category"] = exc.category
            report.source_status[source] = status
        report.results = deduplicate(report.results)
        report.duration_ms = (time.perf_counter() - started) * 1000
        return report
