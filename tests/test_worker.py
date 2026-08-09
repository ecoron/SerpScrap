from scrapcore.jobs import ScrapeJob
from scrapcore.proxy import ProxyEndpoint
from scrapcore.scraper.selenium import SelScrape
from serpscrap.config import Config

HTML = "<html><body><main id='search'><div id='rso'></div></main></body></html>"


class FakeDriver:
    def __init__(self, error=None):
        self.error = error
        self.current_url = "https://www.google.com/search?q=test"
        self.page_source = HTML
        self.quit_calls = 0
        self.get_calls = 0

    def get(self, url):
        self.get_calls += 1
        self.current_url = url
        if self.error:
            raise self.error

    def find_elements(self, by, selector):
        return [object()] if selector == "#search" else []

    def quit(self):
        self.quit_calls += 1


class FakeFactory:
    def __init__(self, driver):
        self.driver = driver

    def create(self, proxy=None):
        return self.driver


def test_worker_quits_driver_after_success():
    driver = FakeDriver()
    scraper = SelScrape(
        Config().get(), ScrapeJob(query="test"), driver_factory=FakeFactory(driver)
    )

    result = scraper.retrieve()

    assert len(result.pages) == 1
    assert not result.failures
    assert driver.quit_calls == 1


def test_worker_quits_driver_after_navigation_failure():
    from selenium.common.exceptions import WebDriverException

    driver = FakeDriver(error=WebDriverException("navigation failed"))
    scraper = SelScrape(
        Config().get(), ScrapeJob(query="test"), driver_factory=FakeFactory(driver)
    )

    result = scraper.retrieve()

    assert result.failures[0].category == "webdriver"
    assert driver.quit_calls == 1


def test_worker_reports_startup_failure_without_driver():
    class BrokenFactory:
        def create(self, proxy=None):
            raise RuntimeError("Chrome missing")

    result = SelScrape(
        Config().get(), ScrapeJob(query="test"), driver_factory=BrokenFactory()
    ).retrieve()

    assert result.failures[0].category == "browser_startup"


def test_worker_preserves_first_page_when_second_page_fails():
    from selenium.common.exceptions import WebDriverException

    class SecondPageFailsDriver(FakeDriver):
        def get(self, url):
            super().get(url)
            if self.get_calls == 2:
                raise WebDriverException("second page failed")

    driver = SecondPageFailsDriver()
    job = ScrapeJob(query="test", pages=(1, 2))
    config = Config().get()
    config["request_retry_limit"] = 0

    result = SelScrape(config, job, driver_factory=FakeFactory(driver)).retrieve()

    assert [page.page_number for page in result.pages] == [1]
    assert result.failures[0].page_number == 2
    assert driver.quit_calls == 1


def test_worker_retries_transient_navigation_once_and_records_attempt_count():
    from selenium.common.exceptions import WebDriverException

    driver = FakeDriver(error=WebDriverException("navigation failed"))
    config = Config().get()
    config.update(
        {
            "request_retry_limit": 1,
            "request_delay_min": 0,
            "request_delay_max": 0,
            "request_backoff_base": 0,
            "request_backoff_max": 0,
        }
    )

    result = SelScrape(
        config, ScrapeJob(query="test"), driver_factory=FakeFactory(driver)
    ).retrieve()

    assert driver.get_calls == 2
    assert result.failures[0].attempt_count == 2


def test_worker_does_not_retry_explicit_google_block():
    driver = FakeDriver()
    driver.page_source = "Our systems have detected unusual traffic"
    config = Config().get()
    config.update({"request_delay_min": 0, "request_delay_max": 0})

    result = SelScrape(
        config, ScrapeJob(query="test", pages=(1, 2)), driver_factory=FakeFactory(driver)
    ).retrieve()

    assert driver.get_calls == 1
    assert result.failures[0].category == "blocked"
    assert result.failures[0].retryable is False


def test_worker_rotates_proxy_for_transient_navigation_failure():
    from selenium.common.exceptions import WebDriverException

    first_proxy = ProxyEndpoint("http", "127.0.0.1", 8000)
    second_proxy = ProxyEndpoint("http", "127.0.0.2", 8000)
    first_driver = FakeDriver(error=WebDriverException("first proxy failed"))
    second_driver = FakeDriver()

    class RotatingFactory:
        def __init__(self):
            self.calls = []
            self.drivers = iter((first_driver, second_driver))

        def create(self, proxy=None):
            self.calls.append(proxy)
            return next(self.drivers)

    factory = RotatingFactory()
    config = Config().get()
    config.update(
        {
            "request_retry_limit": 1,
            "request_delay_min": 0,
            "request_delay_max": 0,
            "request_backoff_base": 0,
            "request_backoff_max": 0,
        }
    )
    selected = []
    scraper = SelScrape(
        config,
        ScrapeJob(query="test", proxy=first_proxy),
        driver_factory=factory,
        proxy_selector=lambda engine, current: second_proxy,
        proxy_failure_reporter=lambda proxy, error: selected.append((proxy, str(error))),
    )

    result = scraper.retrieve()

    assert not result.failures
    assert factory.calls == [first_proxy, second_proxy]
    assert selected[0][0] == first_proxy
    assert result.pages[0].requested_by == "127.0.0.2:8000"


def test_worker_does_not_rotate_proxy_for_explicit_block():
    first_proxy = ProxyEndpoint("http", "127.0.0.1", 8000)
    driver = FakeDriver()
    driver.page_source = "Our systems have detected unusual traffic"
    calls = []
    config = Config().get()
    config.update({"request_delay_min": 0, "request_delay_max": 0})

    result = SelScrape(
        config,
        ScrapeJob(query="test", proxy=first_proxy),
        driver_factory=FakeFactory(driver),
        proxy_selector=lambda engine, current: calls.append(current),
    ).retrieve()

    assert result.failures[0].category == "blocked"
    assert calls == []
