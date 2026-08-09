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
        if config.get("consent_action") not in {"necessary", "reject", "accept", "disabled"}:
            raise ConfigurationError("consent_action must be one of: necessary, reject, accept, disabled")
        searxng_engines = config.get("searxng_engines", [])
        if isinstance(searxng_engines, str) or not isinstance(searxng_engines, (list, tuple, set)):
            raise ConfigurationError("searxng_engines must be a sequence")
        if any(not str(engine).strip() for engine in searxng_engines):
            raise ConfigurationError("searxng_engines must contain non-empty engine IDs")

        engines = config.get("search_engines")
        if isinstance(engines, str):
            engines = [item.strip() for item in engines.split(",") if item.strip()]
        try:
            searxng_url = str(config.get("searxng_url") or "")
            if config.get("searxng_enabled") and not searxng_url.startswith(("http://", "https://")):
                raise ConfigurationError("searxng_url must be an absolute HTTP(S) URL when enabled")
            registry = default_registry(config)
        except ValueError as exc:
            raise ConfigurationError(str(exc)) from exc
        supported = set(registry.ids())
        if not engines or set(engines) - supported:
            unknown = sorted(set(engines or ()) - supported)
            raise ConfigurationError(
                "Unsupported search engine(s): " + ", ".join(unknown or ["none"])
            )
        if len(set(engines)) != len(engines):
            raise ConfigurationError("duplicate search engine IDs are not allowed")
        try:
            plugins = registry.validate_selection(engines)
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
        retryable_categories = config.get("retryable_engine_categories", [])
        if isinstance(retryable_categories, str) or not isinstance(retryable_categories, (list, tuple, set)):
            raise ConfigurationError("retryable_engine_categories must be a sequence")
        allowed_categories = {
            "timeout", "navigation_state", "network", "webdriver", "malformed", "empty",
            "selector_drift", "blocked", "consent_required", "rate_limited",
        }
        unknown_retry_categories = set(retryable_categories) - allowed_categories
        if unknown_retry_categories:
            raise ConfigurationError(
                "unsupported retryable engine category(ies): "
                + ", ".join(sorted(unknown_retry_categories))
            )
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

        proxy_enabled = config.get("proxy_enabled", False)
        if not isinstance(proxy_enabled, bool):
            raise ConfigurationError("proxy_enabled must be a boolean")
        proxy_requested = proxy_enabled or not config.get("use_own_ip", True)
        if proxy_requested and not (
            config.get("proxy_file") or config.get("proxy_sources")
        ):
            raise ConfigurationError(
                "proxy_file or proxy_sources is required when proxy use is enabled"
            )
        if not isinstance(config.get("proxy_sources", []), (list, tuple, str)):
            raise ConfigurationError("proxy_sources must be a sequence or string")
        for key in ("proxy_source_timeout", "proxy_check_timeout"):
            try:
                if float(config.get(key, 0)) <= 0:
                    raise ConfigurationError(f"{key} must be positive")
            except (TypeError, ValueError) as exc:
                raise ConfigurationError(f"{key} must be numeric") from exc
        try:
            if int(config.get("proxy_failure_threshold", 0)) < 1:
                raise ConfigurationError("proxy_failure_threshold must be positive")
        except (TypeError, ValueError) as exc:
            raise ConfigurationError("proxy_failure_threshold must be an integer") from exc
        for key in ("proxy_allowed_protocols", "proxy_allowed_countries"):
            values = config.get(key, [])
            if isinstance(values, str) or not isinstance(values, (list, tuple, set)):
                raise ConfigurationError(f"{key} must be a sequence")
            if any(not str(value).strip() for value in values):
                raise ConfigurationError(f"{key} must not contain empty values")
        if not set(str(value).lower() for value in config.get("proxy_allowed_protocols", [])) <= {"http", "socks4", "socks5"}:
            raise ConfigurationError("proxy_allowed_protocols contains an unsupported protocol")
        for key in ("proxy_source_max_bytes", "proxy_max_endpoints"):
            try:
                if int(config.get(key, 0)) < 1:
                    raise ConfigurationError(f"{key} must be positive")
            except (TypeError, ValueError) as exc:
                raise ConfigurationError(f"{key} must be an integer") from exc
        for key in ("proxy_cache_ttl", "proxy_max_age_seconds"):
            try:
                if float(config.get(key, 0)) < 0:
                    raise ConfigurationError(f"{key} must not be negative")
            except (TypeError, ValueError) as exc:
                raise ConfigurationError(f"{key} must be numeric") from exc
        try:
            if float(config.get("proxy_auto_refresh_interval_seconds", 900)) < 60:
                raise ConfigurationError("proxy_auto_refresh_interval_seconds must be at least 60 seconds")
        except (TypeError, ValueError) as exc:
            raise ConfigurationError("proxy_auto_refresh_interval_seconds must be numeric") from exc
        if config.get("screenshot") and not config.get("dir_screenshot"):
            raise ConfigurationError("dir_screenshot is required when screenshots are enabled")
        if config.get("do_caching") and not config.get("cachedir"):
            raise ConfigurationError("cachedir is required when caching is enabled")
        if float(config.get("searxng_timeout", 20)) <= 0:
            raise ConfigurationError("searxng_timeout must be positive")

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
