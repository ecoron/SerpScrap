import pytest

from scrapcore.cachemanager import CacheManager
from scrapcore.validator_config import ValidatorConfig
from serpscrap.config import Config
from serpscrap.exceptions import ConfigurationError
from serpscrap.plugins.searchengines.registry import default_registry


def test_registry_exposes_operational_metadata_for_all_phase5_engines():
    metadata = default_registry().metadata()
    assert len(metadata) == 11
    assert {item["readiness"] for item in metadata} == {"enabled"}
    assert all(item["plugin_version"] for item in metadata)


@pytest.mark.parametrize("key,value", [("search_engines", ["bing", "bing"]), ("search_engines", ["missing"])])
def test_phase5_rejects_ambiguous_engine_selection(key, value):
    config = Config().get()
    config[key] = value
    with pytest.raises(ConfigurationError):
        ValidatorConfig().validate(config)


def test_phase5_rejects_per_engine_limit_above_global_limit():
    config = Config().get()
    config.update({"search_engines": ["bing"], "num_workers": 2, "engine_workers": 2, "engine_workers_by_engine": {"bing": 3}})
    with pytest.raises(ConfigurationError, match="between 1 and num_workers"):
        ValidatorConfig().validate(config)


def test_phase5_cache_identity_includes_provider_dimensions(tmp_path):
    config = Config().get()
    config.update({"cachedir": str(tmp_path), "country_code": "DE", "plugin_version": "bing-2"})
    manager = CacheManager(config, logger=type("Logger", (), {"warning": lambda *_: None, "error": lambda *_: None})())
    first = manager.cached_file_name("query", "bing", "selenium", 1)
    config["country_code"] = "FR"
    second = manager.cached_file_name("query", "bing", "selenium", 1)
    assert first != second
