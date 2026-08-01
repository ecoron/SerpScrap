from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest

from scrapcore.scraper.browser import (
    FALLBACK_CHROME_USER_AGENT,
    BrowserConfigurationError,
    BrowserSettings,
    ChromeDriverFactory,
    ChromeIdentityProvider,
    GoogleSearchAdapter,
    RequestPacer,
    RequestPolicy,
    RunCircuitBreaker,
)
from serpscrap.config import Config


def test_google_url_is_encoded_and_page_offset_is_deterministic():
    config = Config().get()
    adapter = GoogleSearchAdapter(config)

    url = adapter.build_url("c++ & python", page_number=3)
    params = parse_qs(urlparse(url).query)

    assert params["q"] == ["c++ & python"]
    assert params["start"] == ["20"]
    assert params["num"] == ["10"]


def test_image_search_adds_tbm_parameter():
    url = GoogleSearchAdapter(Config().get()).build_url("cats", 1, "image")

    assert parse_qs(urlparse(url).query)["tbm"] == ["isch"]


@pytest.mark.parametrize(
    ("search_type", "vertical"),
    [("news", "nws"), ("shopping", "shop"), ("videos", "vid")],
)
def test_vertical_search_adds_tbm_parameter(search_type, vertical):
    url = GoogleSearchAdapter(Config().get()).build_url("query", 1, search_type)

    assert parse_qs(urlparse(url).query)["tbm"] == [vertical]


def test_browser_settings_map_explicit_config():
    config = Config().get()
    config.update({"window_width": 1440, "window_height": 1000, "wait_timeout": 7})

    settings = BrowserSettings.from_config(config)

    assert settings.window_width == 1440
    assert settings.window_height == 1000
    assert settings.wait_timeout == 7
    assert "Chrome/" in settings.user_agent
    assert "HeadlessChrome" not in settings.user_agent


def test_identity_matches_detected_chrome_major_and_validates_overrides():
    provider = ChromeIdentityProvider(version_reader=lambda _binary: 155)

    assert "Chrome/155.0.0.0" in provider.resolve(None)
    assert (
        ChromeIdentityProvider(version_reader=lambda _binary: None).resolve(None)
        == FALLBACK_CHROME_USER_AGENT
    )
    with pytest.raises(BrowserConfigurationError, match="desktop"):
        provider.resolve("Mozilla/5.0 HeadlessChrome/155.0.0.0 Safari/537.36")


def test_identity_fallback_has_an_enforced_maintenance_window():
    ChromeIdentityProvider.ensure_fallback_fresh()
    with pytest.raises(BrowserConfigurationError, match="stale"):
        ChromeIdentityProvider.ensure_fallback_fresh(date(2027, 1, 1))


def test_request_pacer_skips_first_delay_and_circuit_breaker_opens():
    now = [10.0]
    sleeps = []

    def sleep(delay):
        sleeps.append(delay)
        now[0] += delay

    pacer = RequestPacer(
        RequestPolicy(delay_min=1, delay_max=1),
        sleeper=sleep,
        monotonic=lambda: now[0],
    )
    pacer.wait()
    pacer.wait()

    assert sleeps == [1]
    breaker = RunCircuitBreaker(2)
    breaker.record_block()
    assert breaker.open is False
    breaker.record_block()
    assert breaker.open is True


def test_chrome_factory_applies_effective_identity_to_options_and_cdp(monkeypatch):
    captured = {}

    class Driver:
        def execute_cdp_cmd(self, command, values):
            captured["cdp"] = (command, values)

        def set_page_load_timeout(self, timeout):
            captured["timeout"] = timeout

        def set_window_size(self, width, height):
            captured["window"] = (width, height)

    def create_driver(*, service, options):
        captured["arguments"] = options.arguments
        return Driver()

    monkeypatch.setattr("scrapcore.scraper.browser.webdriver.Chrome", create_driver)
    settings = BrowserSettings(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/151.0.0.0 Safari/537.36",
        language="de-DE",
    )

    ChromeDriverFactory(settings).create()

    assert "--user-agent=" + settings.user_agent in captured["arguments"]
    assert "--lang=de-DE" in captured["arguments"]
    assert captured["cdp"][1]["userAgent"] == settings.user_agent
    assert captured["cdp"][1]["acceptLanguage"] == "de-DE"


def test_adapter_classifies_block_and_consent_states():
    adapter = GoogleSearchAdapter(Config().get())

    assert adapter.classify("https://google.com/sorry/", "") == "blocked"
    assert adapter.classify("https://consent.google.com/", "") == "consent_required"
    assert adapter.classify("https://google.com/search", "Too many requests") == "rate_limited"
    assert adapter.classify("https://google.com/search?q=test", "recaptcha library") is None
