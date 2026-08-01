from pathlib import Path

import pytest

from scrapcore.tools import ConfigurationError
from scrapcore.validator_config import ValidatorConfig
from serpscrap.config import Config


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


def test_validator_accepts_registered_alternative_engine():
    config = Config().get()
    config["search_engines"] = ["bing"]

    ValidatorConfig().validate(config)


def test_validator_rejects_unknown_engine():
    config = Config().get()
    config["search_engines"] = ["not-an-engine"]

    with pytest.raises(ConfigurationError, match="Unsupported search engine"):
        ValidatorConfig().validate(config)


def test_validator_accepts_default_config():
    ValidatorConfig().validate(Config().get())


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
