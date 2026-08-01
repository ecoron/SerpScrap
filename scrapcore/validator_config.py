"""Validation for the public dictionary configuration."""

from scrapcore.scraper.browser import BrowserSettings
from scrapcore.tools import ConfigurationError


class ValidatorConfig:
    """Validate configuration once at the pipeline boundary."""

    def validate(self, config: dict) -> None:
        if not isinstance(config, dict):
            raise ConfigurationError("Config is not a dict")
        if config.get("scrape_method") != "selenium":
            raise ConfigurationError("Only the selenium scrape method is supported")
        if config.get("sel_browser") != "chrome":
            raise ConfigurationError("Only Chrome is supported")
        if config.get("search_type") not in {"normal", "image"}:
            raise ConfigurationError("search_type must be 'normal' or 'image'")

        engines = config.get("search_engines")
        if isinstance(engines, str):
            engines = [item.strip() for item in engines.split(",") if item.strip()]
        if not engines or set(engines) - {"google"}:
            raise ConfigurationError("Only the google search engine is currently supported")

        for key in ("num_pages_for_keyword", "num_workers", "num_results_per_page"):
            try:
                value = int(config.get(key, 0))
            except (TypeError, ValueError) as exc:
                raise ConfigurationError(f"{key} must be an integer") from exc
            if value < 1:
                raise ConfigurationError(f"{key} must be positive")
        if int(config["num_results_per_page"]) > 100:
            raise ConfigurationError("num_results_per_page must not exceed 100")

        if not config.get("use_own_ip", False) and not config.get("proxy_file"):
            raise ConfigurationError("proxy_file is required when use_own_ip is disabled")
        if config.get("screenshot") and not config.get("dir_screenshot"):
            raise ConfigurationError("dir_screenshot is required when screenshots are enabled")
        if config.get("do_caching") and not config.get("cachedir"):
            raise ConfigurationError("cachedir is required when caching is enabled")

        try:
            BrowserSettings.from_config(config)
        except (TypeError, ValueError) as exc:
            raise ConfigurationError(str(exc)) from exc
