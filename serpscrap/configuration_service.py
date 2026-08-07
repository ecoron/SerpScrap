"""Registry-backed, schema-described, database-persisted configuration."""

from __future__ import annotations

import copy
import re
from typing import Any

from scrapcore.validator_config import ValidatorConfig
from serpscrap.config import Config
from serpscrap.history_store import SearchHistoryStore
from serpscrap.plugins.searchengines.registry import SearchEngineRegistry, default_registry

SCHEMA_VERSION = 2
READ_ONLY_KEYS = {"supported_search_engines", "today", "headers", "chrome_binary", "executable_path", "scrape_method", "sel_browser"}
SENSITIVE_KEYS = {"headers"}


GROUPS = (
    {"id": "search", "title": "Search behavior", "description": "Defaults used for new searches and provider selection.", "expanded": True},
    {"id": "ranking", "title": "Ranking and fusion", "description": "How provider results are combined and ranked.", "expanded": False},
    {"id": "browser", "title": "Browser and scraping", "description": "Browser execution, pacing, retries, and request behavior.", "expanded": False},
    {"id": "network", "title": "Network and proxy", "description": "Connection limits, redirects, proxy checks, and request policy.", "expanded": False},
    {"id": "storage", "title": "Storage, cache, and history", "description": "Persistence, cache retention, and URL/history behavior.", "expanded": False},
    {"id": "diagnostics", "title": "Diagnostics and execution", "description": "Workers, progress, logs, consent, and diagnostic artifacts.", "expanded": False},
    {"id": "runtime", "title": "Runtime information", "description": "Values supplied by the deployment and shown for transparency.", "expanded": False},
)


FIELD_DEFINITIONS = (
    ("search_engines", "search", "Search engines", "engine-list", "Choose the providers used for new searches.", True, False, None, None),
    ("country_code", "search", "Country code", "text", "ISO 3166-1 alpha-2 code, for example DE.", True, True, 2, 2),
    ("search_type", "search", "Search type", "select", "The result family requested from every selected provider.", True, False, None, None),
    ("num_pages_for_keyword", "search", "Pages per query", "number", "More pages increase coverage and runtime.", True, True, 1, 20),
    ("num_results_per_page", "search", "Results per page", "number", "Maximum normalized results requested per page.", True, True, 1, 100),
    ("results_age", "search", "Result age", "text", "Provider result-age policy.", True, False, None, None),
    ("language", "search", "Language", "text", "Browser language sent to providers.", True, False, None, None),
    ("use_own_ip", "search", "Use own IP", "boolean", "Disable only when a proxy is configured and approved.", True, False, None, None),
    ("engine_workers", "ranking", "Engine workers", "number", "Concurrent workers assigned to provider engines.", True, True, 1, 32),
    ("engine_workers_by_engine", "ranking", "Per-engine worker limits", "map-number", "Optional per-provider worker overrides.", True, False, None, None),
    ("engine_weights", "ranking", "Engine weights", "map-number", "Optional provider weights used by fusion.", True, False, None, None),
    ("other_market_share", "ranking", "Other market share", "number", "Weight assigned to providers without a known market share.", True, True, 0, 1),
    ("ranking.rrf_k", "ranking", "RRF k", "number", "Reciprocal-rank-fusion constant.", True, True, 1, 1000),
    ("ranking.provider_family_cap", "ranking", "Limit provider families", "boolean", "Prevent one provider family dominating fused results.", True, False, None, None),
    ("fusion_snapshot_id", "ranking", "Fusion snapshot", "text", "Pinned provider-ranking snapshot identifier.", True, False, None, None),
    ("scrape_method", "browser", "Scrape method", "text", "The current release supports Selenium.", False, False, None, None),
    ("sel_browser", "browser", "Browser", "text", "The current release supports Chrome.", False, False, None, None),
    ("chrome_headless", "browser", "Headless Chrome", "boolean", "Run Chrome without a visible window.", True, False, None, None),
    ("chrome_no_sandbox", "browser", "Chrome no-sandbox", "boolean", "Use only in trusted container environments.", True, False, None, None),
    ("window_width", "browser", "Window width", "number", "Browser viewport width in pixels.", True, True, 320, 4096),
    ("window_height", "browser", "Window height", "number", "Browser viewport height in pixels.", True, True, 240, 4096),
    ("chrome_binary", "browser", "Chrome binary", "text", "Deployment-provided browser path.", False, False, None, None),
    ("executable_path", "browser", "ChromeDriver path", "text", "Deployment-provided driver path.", False, False, None, None),
    ("page_load_timeout", "browser", "Page-load timeout", "number", "Maximum page-load wait in seconds.", True, True, 1, 300),
    ("wait_timeout", "browser", "Element wait timeout", "number", "Maximum wait for provider result markers in seconds.", True, True, 1, 300),
    ("user_agent", "browser", "User agent", "text", "Optional browser identity; empty derives the installed Chrome major.", True, False, None, None),
    ("chrome_profile_dir", "browser", "Chrome profile directory", "text", "Optional disposable profile directory for controlled smoke tests.", True, False, None, None),
    ("interaction_settle_delay", "browser", "Interaction settle delay", "number", "Short wait after query entry so provider autocomplete can settle before submit.", True, True, 0, 5),
    ("request_delay_min", "browser", "Minimum request delay", "number", "Lower bound for delay between provider requests in seconds.", True, True, 0, 60),
    ("request_delay_max", "browser", "Maximum request delay", "number", "Upper bound for delay between provider requests in seconds.", True, True, 0, 60),
    ("request_retry_limit", "browser", "Request retry limit", "number", "Retries for retryable provider failures.", True, True, 0, 10),
    ("retryable_engine_categories", "browser", "Retryable failure categories", "list-text", "Failure categories eligible for retry.", True, False, None, None),
    ("request_backoff_base", "browser", "Backoff base", "number", "Initial retry backoff in seconds.", True, True, 0, 120),
    ("request_backoff_max", "browser", "Backoff maximum", "number", "Maximum retry backoff in seconds.", True, True, 0, 600),
    ("block_threshold", "browser", "Block threshold", "number", "Provider blocks before the engine is stopped.", True, True, 1, 20),
    ("url_connect_timeout", "network", "Connect timeout", "number", "Connection timeout in seconds.", True, True, 1, 300),
    ("url_read_timeout", "network", "Read timeout", "number", "Response read timeout in seconds.", True, True, 1, 600),
    ("url_max_redirects", "network", "Maximum redirects", "number", "Maximum redirects followed for a URL.", True, True, 0, 20),
    ("url_max_response_bytes", "network", "Maximum response size", "number", "Maximum downloaded response size in bytes.", True, True, 1024, 100000000),
    ("proxy_file", "network", "Proxy file", "text", "Proxy source used when own-IP mode is disabled.", True, False, None, None),
    ("proxy_check_url", "network", "Proxy check URL", "url", "Endpoint used to verify proxy connectivity.", True, False, None, None),
    ("proxy_info_url", "network", "Proxy info URL", "url", "Endpoint used for proxy metadata.", True, False, None, None),
    ("check_proxies", "network", "Check proxies", "boolean", "Verify proxy health before running searches.", True, False, None, None),
    ("do_caching", "storage", "Enable caching", "boolean", "Cache provider responses to reduce repeated work.", True, False, None, None),
    ("cachedir", "storage", "Cache directory", "text", "Filesystem location for cache data.", True, False, None, None),
    ("clean_cache_after", "storage", "Clean cache after", "number", "Cache cleanup age in hours.", True, True, 1, 720),
    ("minimize_caching_files", "storage", "Minimize cache files", "boolean", "Reduce cache artifact count where supported.", True, False, None, None),
    ("database_name", "storage", "Database location", "text", "History database URL or path.", True, False, None, None),
    ("store_history", "storage", "Store search history", "boolean", "Persist future runs, results, and failures.", True, False, None, None),
    ("scrape_urls", "storage", "Scrape result URLs", "boolean", "Fetch destination pages after SERP collection.", True, False, None, None),
    ("diagnostic_html", "diagnostics", "Diagnostic HTML", "boolean", "Store provider HTML artifacts for troubleshooting.", True, False, None, None),
    ("diagnostic_dir", "diagnostics", "Diagnostic directory", "text", "Filesystem location for diagnostics.", True, False, None, None),
    ("diagnostic_max_bytes_per_file", "diagnostics", "Diagnostic file limit", "number", "Maximum bytes for one diagnostic artifact.", True, True, 1024, 100000000),
    ("diagnostic_max_total_bytes", "diagnostics", "Diagnostic total limit", "number", "Maximum diagnostic bytes per job.", True, True, 1024, 1000000000),
    ("diagnostic_max_artifacts_per_job", "diagnostics", "Diagnostic artifact limit", "number", "Maximum artifacts retained per job.", True, True, 1, 100),
    ("url_threads", "diagnostics", "URL threads", "number", "Concurrent URL scraping threads.", True, True, 1, 64),
    ("num_workers", "diagnostics", "Total workers", "number", "Maximum application worker count.", True, True, 1, 64),
    ("progress", "diagnostics", "Progress reporting", "boolean", "Emit progress events while searching.", True, False, None, None),
    ("progress_format", "diagnostics", "Progress format", "text", "Progress event format.", True, False, None, None),
    ("log_level", "diagnostics", "Log level", "select", "Application logging verbosity.", True, False, None, None),
    ("consent_action", "diagnostics", "Consent handling", "select", "How provider consent dialogs are handled.", True, False, None, None),
    ("supported_search_engines", "runtime", "Supported engines", "engine-list", "All engines known to the registry.", False, False, None, None),
    ("today", "runtime", "Runtime date", "text", "Date supplied by the runtime.", False, False, None, None),
    ("headers", "runtime", "Request headers", "json", "Internal request headers; not exposed for editing.", False, True, None, None),
)


def _get_path(payload: dict[str, Any], path: str) -> Any:
    value: Any = payload
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _set_path(payload: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    target = payload
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value


class SearchConfigurationService:
    def __init__(self, store: SearchHistoryStore, registry: SearchEngineRegistry | None = None) -> None:
        self.store = store
        self.registry = registry or default_registry()

    def engines(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self.registry.metadata()]

    def _default_payload(self) -> dict[str, Any]:
        defaults = copy.deepcopy(Config().get())
        defaults["search_engines"] = [engine_id for engine_id in defaults["search_engines"] if self.registry.get(engine_id).enabled]
        defaults["supported_search_engines"] = list(self.registry.ids())
        return defaults

    def _editable_keys(self) -> set[str]:
        return {definition[0] for definition in FIELD_DEFINITIONS if definition[5]}

    def _coerce(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = copy.deepcopy(payload)
        for path, _group, _label, field_type, _description, editable, _required, _minimum, _maximum in FIELD_DEFINITIONS:
            value = _get_path(result, path)
            if not editable or value is None:
                continue
            if field_type == "number":
                value = float(value) if isinstance(value, str) and "." in value else int(value)
            elif field_type == "boolean" and isinstance(value, str):
                value = value.lower() in {"true", "1", "yes", "on"}
            elif field_type == "list-text" and isinstance(value, str):
                value = [item.strip() for item in value.split(",") if item.strip()]
            elif field_type == "map-number" and isinstance(value, dict):
                value = {str(key): float(item) if isinstance(item, str) and "." in item else int(item) for key, item in value.items()}
            _set_path(result, path, value)
        return result

    def _validate(self, payload: dict[str, Any], base: dict[str, Any] | None = None) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("configuration must be an object")
        defaults = copy.deepcopy(base or self._default_payload())
        unknown = set(payload) - set(defaults)
        if unknown:
            raise ValueError("unknown configuration key(s): " + ", ".join(sorted(unknown)))
        candidate = defaults
        for path, _group, _label, _field_type, _description, editable, _required, _minimum, _maximum in FIELD_DEFINITIONS:
            value = _get_path(payload, path)
            if editable and value is not None:
                _set_path(candidate, path, copy.deepcopy(value))
        candidate = self._coerce(candidate)
        selected = candidate.get("search_engines")
        if not isinstance(selected, list) or not selected:
            raise ValueError("at least one search engine must be selected")
        selected_ids = [str(engine).strip().lower() for engine in selected]
        try:
            self.registry.validate_selection(selected_ids)
            ValidatorConfig().validate(candidate)
        except Exception as exc:
            raise ValueError(str(exc)) from exc
        country = str(candidate.get("country_code", "DE")).upper()
        if not re.fullmatch(r"[A-Z]{2}", country):
            raise ValueError("country_code must be an ISO alpha-2 code")
        if float(candidate["request_delay_min"]) > float(candidate["request_delay_max"]):
            raise ValueError("request_delay_min must not exceed request_delay_max")
        if float(candidate["request_backoff_base"]) > float(candidate["request_backoff_max"]):
            raise ValueError("request_backoff_base must not exceed request_backoff_max")
        candidate["search_engines"] = selected_ids
        candidate["country_code"] = country
        return candidate

    def _field_schema(self, configuration: dict[str, Any], defaults: dict[str, Any]) -> list[dict[str, Any]]:
        fields = []
        for path, group, label, field_type, description, editable, required, minimum, maximum in FIELD_DEFINITIONS:
            value = _get_path(configuration, path)
            default = _get_path(defaults, path)
            field = {"key": path, "group": group, "label": label, "description": description, "type": field_type, "value": None if path in SENSITIVE_KEYS else value, "default": None if path in SENSITIVE_KEYS else default, "editable": editable, "read_only": not editable, "sensitive": path in SENSITIVE_KEYS, "required": required}
            if minimum is not None:
                field["min"] = minimum
            if maximum is not None:
                field["max"] = maximum
            if path == "search_type":
                field["options"] = [{"value": item, "label": item.title()} for item in ("normal", "image", "news", "shopping", "videos")]
            elif path == "log_level":
                field["options"] = [{"value": item, "label": item} for item in ("DEBUG", "INFO", "WARNING", "ERROR")]
            elif path == "consent_action":
                field["options"] = [{"value": item, "label": item.title()} for item in ("necessary", "reject", "accept", "disabled")]
            fields.append(field)
        return fields

    def _response(self, source: str, revision: int, configuration: dict[str, Any], updated_at: str | None = None) -> dict[str, Any]:
        defaults = self._default_payload()
        public = copy.deepcopy(configuration)
        public["headers"] = {}
        public_defaults = copy.deepcopy(defaults)
        public_defaults["headers"] = {}
        return {"schema_version": SCHEMA_VERSION, "source": source, "revision": revision, "updated_at": updated_at, "configuration": public, "initial_defaults": public_defaults, "groups": [dict(group) for group in GROUPS], "fields": self._field_schema(configuration, defaults), "engines": self.engines(), "capabilities": {"editable_keys": sorted(self._editable_keys()), "read_only_keys": sorted(READ_ONLY_KEYS), "sensitive_keys": sorted(SENSITIVE_KEYS)}}

    def get(self, include_sensitive: bool = False) -> dict[str, Any]:
        record = self.store.get_configuration()
        defaults = self._default_payload()
        if record is None:
            return self._response("defaults", 0, defaults)
        raw = record["payload"] if isinstance(record.get("payload"), dict) else {}
        try:
            payload = self._validate(raw, defaults)
        except (TypeError, ValueError):
            legacy = {key: value for key, value in raw.items() if key in defaults}
            if isinstance(legacy.get("search_engines"), list):
                legacy["search_engines"] = [
                    engine_id
                    for engine_id in legacy["search_engines"]
                    if self.registry.get(str(engine_id)).enabled
                ]
            payload = self._validate({**defaults, **legacy}, defaults)
        response = self._response("persisted", record["revision"], payload, record["updated_at"])
        if include_sensitive:
            response["configuration"] = payload
        return response

    def save(self, payload: dict[str, Any]) -> dict[str, Any]:
        validated = self._validate(payload)
        record = self.store.save_configuration(validated)
        return self._response("persisted", record["revision"], validated, record["updated_at"])

    def reset(self) -> dict[str, Any]:
        self.store.reset_configuration()
        return self.get()

    def resolve_options(self, options: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
        explicit = dict(options or {})
        current = self.get(include_sensitive=True)
        selected = copy.deepcopy(current["configuration"])
        selected.update({key: value for key, value in explicit.items() if key in selected})
        validated = self._validate(selected, selected)
        validated.update({key: value for key, value in explicit.items() if key not in validated})
        return validated, {"source": "explicit" if explicit else current["source"], "revision": current["revision"]}
