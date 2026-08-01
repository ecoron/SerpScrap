from urllib.parse import parse_qs, urlparse

from scrapcore.scraper.browser import BrowserSettings, GoogleSearchAdapter
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


def test_browser_settings_map_explicit_config():
    config = Config().get()
    config.update({"window_width": 1440, "window_height": 1000, "wait_timeout": 7})

    settings = BrowserSettings.from_config(config)

    assert settings.window_width == 1440
    assert settings.window_height == 1000
    assert settings.wait_timeout == 7


def test_adapter_classifies_block_and_consent_states():
    adapter = GoogleSearchAdapter(Config().get())

    assert adapter.classify("https://google.com/sorry/", "") == "blocked"
    assert adapter.classify("https://consent.google.com/", "") == "consent_required"
    assert adapter.classify("https://google.com/search?q=test", "recaptcha library") is None
