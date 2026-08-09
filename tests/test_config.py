from pathlib import Path

import pytest

from scrapcore.tools import ConfigurationError
from scrapcore.validator_config import ValidatorConfig
from serpscrap.config import Config


def test_default_search_engines_activate_public_candidates_without_disabled_defaults():
    config = Config().get()

    expected = [
        "bing", "yandex", "yahoo", "duckduckgo", "startpage", "brave",
        "swisscows", "mojeek", "good", "xprivo", "marginalia", "etools",
    ]
    if config["searxng_url"]:
        expected.append("searxng")
    assert config["search_engines"] == expected
    assert {"google", "ecosia", "qwant"}.isdisjoint(config["search_engines"])
    assert set(config["search_engines"]).issubset(config["supported_search_engines"])
    assert "google" in config["searxng_engines"]
    assert "brave" in config["searxng_engines"]
    assert "arxiv" in config["searxng_engines"]


def test_config_preserves_attribute_and_dictionary_access():
    config = Config()
    config.set("screenshot", True)

    assert config.screenshot is True
    assert config.get()["screenshot"] is True
    assert config.chrome_headless is True


def test_config_defaults_are_cross_platform():
    config = Config().get()

    assert Path(config["cachedir"]).is_absolute()
    assert Path(config["database_name"]).is_absolute()


def test_screenshots_are_enabled_and_use_requested_directory():
    config = Config().get()

    assert config["screenshot"] is True
    assert config["dir_screenshot"] == "C:\\tmp\\screenshots"


def test_validator_accepts_registered_alternative_engine():
    config = Config().get()
    config["search_engines"] = ["bing"]

    ValidatorConfig().validate(config)


def test_validator_accepts_enabled_local_searxng_engine():
    config = Config().get()
    config.update({
        "searxng_enabled": True,
        "searxng_url": "http://searxng:8080",
        "search_engines": ["searxng"],
    })

    ValidatorConfig().validate(config)


def test_validator_accepts_separate_searxng_engine_selection():
    config = Config().get()
    config["searxng_engines"] = ["duckduckgo", "brave"]

    ValidatorConfig().validate(config)


def test_validator_rejects_unknown_engine():
    config = Config().get()
    config["search_engines"] = ["not-an-engine"]

    with pytest.raises(ConfigurationError, match="Unsupported search engine"):
        ValidatorConfig().validate(config)


def test_validator_accepts_default_config():
    ValidatorConfig().validate(Config().get())


def test_consent_action_defaults_to_necessary_and_rejects_invalid_values():
    config = Config().get()
    assert config["consent_action"] == "necessary"
    config["consent_action"] = "invalid"

    with pytest.raises(ConfigurationError, match="consent_action"):
        ValidatorConfig().validate(config)


def test_validator_accepts_explicit_consent_accept_mode():
    config = Config().get()
    config["consent_action"] = "accept"

    ValidatorConfig().validate(config)


@pytest.mark.parametrize("search_type", ["normal", "image", "news", "shopping", "videos"])
def test_validator_accepts_documented_google_search_types(search_type):
    config = Config().get()
    config["search_engines"] = ["google"]
    config["search_type"] = search_type

    ValidatorConfig().validate(config)


def test_validator_rejects_invalid_request_policy():
    config = Config().get()
    config.update({"request_delay_min": 3, "request_delay_max": 1})

    with pytest.raises(ConfigurationError, match="delay range"):
        ValidatorConfig().validate(config)
