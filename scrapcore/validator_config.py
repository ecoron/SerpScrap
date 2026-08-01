"""Validation for the public dictionary configuration."""

from scrapcore.scraper.browser import BrowserSettings, RequestPolicy
from serpscrap.exceptions import ConfigurationError
from serpscrap.plugins.searchengines.registry import default_registry


class ValidatorConfig:
    """Validate configuration once at the pipeline boundary."""

    def validate(self, config: dict) -> None:
        if not isinstance(config, dict):
            raise ConfigurationError("Config is not a dict")
        removed = {"output_filename", "print_results"}.intersection(config)
        if removed:
            names = ", ".join(sorted(removed))
            raise ConfigurationError(
                f"Removed output setting(s): {names}; use search(output='results.json')"
            )
        for key in ("do_caching", "store_history", "scrape_urls", "screenshot"):
            if not isinstance(config.get(key), bool):
                raise ConfigurationError(f"{key} must be a boolean")
        if config.get("scrape_method") != "selenium":
            raise ConfigurationError("Only the selenium scrape method is supported")
        if config.get("sel_browser") != "chrome":
            raise ConfigurationError("Only Chrome is supported")
        search_types = {"normal", "image", "news", "shopping", "videos"}
        if config.get("search_type") not in search_types:
            raise ConfigurationError(
                "search_type must be one of: normal, image, news, shopping, videos"
            )

        engines = config.get("search_engines")
        if isinstance(engines, str):
            engines = [item.strip() for item in engines.split(",") if item.strip()]
        supported = set(default_registry().ids())
        if not engines or set(engines) - supported:
            unknown = sorted(set(engines or ()) - supported)
            raise ConfigurationError(
                "Unsupported search engine(s): " + ", ".join(unknown or ["none"])
            )
        if len(set(engines)) != len(engines):
            raise ConfigurationError("duplicate search engine IDs are not allowed")
        try:
            plugins = default_registry().validate_selection(engines)
        except ValueError as exc:
            raise ConfigurationError(str(exc)) from exc
        country_code = str(config.get("country_code", "DE"))
        if len(country_code) != 2 or not country_code.isalpha() or country_code != country_code.upper():
            raise ConfigurationError("country_code must be an uppercase ISO 3166-1 alpha-2 code")
        try:
            engine_workers = int(config.get("engine_workers", 1))
        except (TypeError, ValueError) as exc:
            raise ConfigurationError("engine_workers must be an integer") from exc
        if engine_workers < 1:
            raise ConfigurationError("engine_workers must be positive")
        try:
            workers = int(config.get("num_workers", 0))
        except (TypeError, ValueError) as exc:
            raise ConfigurationError("num_workers must be an integer") from exc
        if engine_workers > workers:
            raise ConfigurationError("engine_workers must not exceed num_workers")
        per_engine = config.get("engine_workers_by_engine", {})
        if not isinstance(per_engine, dict):
            raise ConfigurationError("engine_workers_by_engine must be a mapping")
        unknown_limits = set(per_engine) - set(engines)
        if unknown_limits:
            raise ConfigurationError("engine worker limit for unselected engine(s): " + ", ".join(sorted(unknown_limits)))
        for engine, limit in per_engine.items():
            if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1 or limit > workers:
                raise ConfigurationError(f"engine worker limit for {engine} must be between 1 and num_workers")
        if not isinstance(config.get("engine_weights", {}), dict):
            raise ConfigurationError("engine_weights must be a mapping")
        ranking = config.get("ranking", {})
        if not isinstance(ranking, dict):
            raise ConfigurationError("ranking must be a mapping")
        if int(ranking.get("rrf_k", config.get("rrf_k", 60))) < 1:
            raise ConfigurationError("rrf_k must be positive")
        if "provider_family_cap" in ranking and not isinstance(ranking["provider_family_cap"], bool):
            raise ConfigurationError("provider_family_cap must be a boolean")

        for key in ("num_pages_for_keyword", "num_workers", "num_results_per_page"):
            try:
                value = int(config.get(key, 0))
            except (TypeError, ValueError) as exc:
                raise ConfigurationError(f"{key} must be an integer") from exc
            if value < 1:
                raise ConfigurationError(f"{key} must be positive")
        if int(config["num_results_per_page"]) > 100:
            raise ConfigurationError("num_results_per_page must not exceed 100")
        for plugin in plugins:
            if config.get("search_type") not in plugin.search_types:
                raise ConfigurationError(
                    f"{plugin.engine_id} does not support search type {config.get('search_type')!r}"
                )

        if not config.get("use_own_ip", False) and not config.get("proxy_file"):
            raise ConfigurationError("proxy_file is required when use_own_ip is disabled")
        if config.get("screenshot") and not config.get("dir_screenshot"):
            raise ConfigurationError("dir_screenshot is required when screenshots are enabled")
        if config.get("do_caching") and not config.get("cachedir"):
            raise ConfigurationError("cachedir is required when caching is enabled")

        try:
            BrowserSettings.from_config(config)
            RequestPolicy.from_config(config)
        except (TypeError, ValueError) as exc:
            raise ConfigurationError(str(exc)) from exc

        for key in (
            "url_connect_timeout",
            "url_read_timeout",
            "url_max_redirects",
            "url_max_response_bytes",
        ):
            try:
                numeric_value = float(config.get(key, 0))
            except (TypeError, ValueError) as exc:
                raise ConfigurationError(f"{key} must be numeric") from exc
            if numeric_value <= 0:
                raise ConfigurationError(f"{key} must be positive")
