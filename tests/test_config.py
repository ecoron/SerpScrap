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


def test_validator_rejects_unsupported_engine():
    config = Config().get()
    config["search_engines"] = ["bing"]

    with pytest.raises(ConfigurationError, match="google"):
        ValidatorConfig().validate(config)


def test_validator_accepts_default_config():
    ValidatorConfig().validate(Config().get())

