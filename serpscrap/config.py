"""Public SerpScrap configuration with backward-compatible dictionary access."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import gettempdir
from typing import Any

DEFAULT_SEARXNG_ENGINES = [
    "google", "bing", "yandex", "yahoo", "duckduckgo", "ecosia", "qwant",
    "startpage", "brave", "swisscows", "mojeek", "marginalia", "etools",
    "wiby", "mwmbl", "searchmysite", "wikipedia",
    "arxiv", "pubmed", "openalex", "crossref", "semantic_scholar",
    "stackoverflow", "askubuntu", "superuser", "reuters",
]

SEARXNG_ENGINE_GROUPS = {
    **{engine: "Web search" for engine in DEFAULT_SEARXNG_ENGINES[:17]},
    **{engine: "Scientific search" for engine in ("arxiv", "pubmed", "openalex", "crossref", "semantic_scholar")},
    **{engine: "Developer and Q&A" for engine in ("stackoverflow", "askubuntu", "superuser")},
    "reuters": "News",
}

SEARXNG_QUERY_NAMES = {"semantic_scholar": "semantic scholar"}


class Config:
    """Mutable configuration facade retained for the public API."""

    def __init__(self) -> None:
        temp_root = Path(gettempdir())
        self.config: dict[str, Any] = {
            "use_own_ip": True,
            "search_engines": [
                "bing", "yandex", "yahoo", "duckduckgo", "startpage", "brave", "swisscows",
                "mojeek", "good", "xprivo", "marginalia", "etools",
            ] + (["searxng"] if os.environ.get("SERPSCRAP_SEARXNG_URL", "") else []),
            "searxng_url": os.environ.get("SERPSCRAP_SEARXNG_URL", ""),
            "searxng_enabled": bool(os.environ.get("SERPSCRAP_SEARXNG_URL", "")),
            "searxng_fallback": False,
            "searxng_engines": list(DEFAULT_SEARXNG_ENGINES),
            "searxng_timeout": 20.0,
            "supported_search_engines": [
                "google", "bing", "yandex", "yahoo", "duckduckgo", "ecosia", "qwant",
                "startpage", "brave", "swisscows", "mojeek", "metager", "good", "xprivo",
                "marginalia", "etools",
            ] + (["searxng"] if os.environ.get("SERPSCRAP_SEARXNG_URL", "") else []),
            "country_code": "DE",
            "engine_workers": 1,
            "engine_workers_by_engine": {},
            "engine_weights": {},
            "other_market_share": 0.63,
            "ranking": {"rrf_k": 60, "provider_family_cap": False},
            "fusion_snapshot_id": "europe-2026-07",
            "num_pages_for_keyword": 1,
            "scrape_method": "selenium",
            "sel_browser": "chrome",
            "chrome_headless": True,
            "chrome_binary": os.environ.get("SERPSCRAP_CHROME_BINARY", ""),
            "chrome_no_sandbox": os.environ.get("SERPSCRAP_CHROME_NO_SANDBOX") == "1",
            "disable_dev_shm_usage": True,
            "executable_path": os.environ.get("SERPSCRAP_CHROMEDRIVER", ""),
            "window_width": 1366,
            "window_height": 900,
            "page_load_timeout": 30,
            "wait_timeout": 25,
            # Empty means: derive a desktop Chrome UA matching the installed
            # browser. Keeping a fixed major here drifts from local Chrome.
            "user_agent": "",
            "chrome_profile_dir": os.environ.get("SERPSCRAP_CHROME_PROFILE_DIR", ""),
            "interaction_settle_delay": 3.0,
            "request_delay_min": 4.0,
            "request_delay_max": 6.0,
            "request_retry_limit": 1,
            "retryable_engine_categories": ["timeout", "navigation_state", "network"],
            "request_backoff_base": 2.0,
            "request_backoff_max": 10.0,
            "block_threshold": 2,
            "language": "de-DE",
            "do_caching": True,
            "cachedir": str(temp_root / ".serpscrap"),
            "screenshot": True,
            "dir_screenshot": os.environ.get("SERPSCRAP_SCREENSHOT_DIR", str(Path("C:/tmp/screenshots"))),
            "database_name": str(temp_root / "serpscrap"),
            "minimize_caching_files": False,
            "clean_cache_after": 24,
            "store_history": True,
            "scrape_urls": False,
            "url_threads": 6,
            "log_level": "INFO",
            "progress": False,
            "progress_format": "text",
            "consent_action": "necessary",
            "diagnostic_html": False,
            "diagnostic_dir": str(Path("/var/lib/serpscrap/diagnostics")),
            "diagnostic_max_bytes_per_file": 2 * 1024 * 1024,
            "diagnostic_max_total_bytes": 20 * 1024 * 1024,
            "diagnostic_max_artifacts_per_job": 10,
            "num_workers": 4,
            "num_results_per_page": 10,
            "results_age": "Any",
            "search_type": "normal",
            "topic_default": "web",
            "topic_sources": {"news": [], "shopping": ["geizhals", "idealo", "billiger", "fruugo", "kaufland", "allegro", "etsy"]},
            "topic_country": "DE",
            "topic_language": "de",
            "topic_since": "24h",
            "topic_currency": "EUR",
            "google_search_url": "https://www.google.com/search?",
            "headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            },
            "url_connect_timeout": 10.0,
            "url_read_timeout": 30.0,
            "url_max_redirects": 5,
            "url_max_response_bytes": 5 * 1024 * 1024,
            "proxy_file": "",
            "proxy_enabled": False,
            "proxy_sources": [
              {
                "location": "https://cdn.jsdelivr.net/gh/proxyscrape/free-proxy-list@main/proxies/all/data.json",
                "type": "url"
              },
              {
                "location": "https://databay.com/api/v1/proxy-list?format=json&limit=500",
                "type": "url"
              }
            ],
            "proxy_source_timeout": 10.0,
            "proxy_source_max_bytes": 2 * 1024 * 1024,
            "proxy_cache_dir": str(temp_root / ".serpscrap" / "proxy-sources"),
            "proxy_cache_ttl": 900.0,
            "proxy_allowed_protocols": ["http", "socks5"],
            "proxy_allowed_countries": [], # [AT, BE, BG, HR, CY, CZ, DK, EE, FI, FR, DE, GR, HU, IE, IT, LV, LT, LU, MT, NL, PL, PT, RO, SK, SI, ES, SE],
            "proxy_max_age_seconds": 0,
            "proxy_max_endpoints": 500,
            "proxy_check_url": "https://icanhazip.com/",
            "proxy_check_timeout": 10.0,
            "proxy_failure_threshold": 2,
            "proxy_auto_refresh_enabled": True,
            "proxy_auto_refresh_interval_seconds": 900,
            "proxy_info_url": "https://ipinfo.io/json",
            "check_proxies": True,
            "stop_on_detection": True,
            "today": datetime.now(timezone.utc).date().isoformat(),
        }

    @property
    def __dict__(self) -> dict[str, Any]:
        return self.config

    def __getattr__(self, key: str) -> Any:
        try:
            return self.config[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def get(self) -> dict[str, Any]:
        return self.config

    def set(self, key: str, value: Any) -> None:
        self.config[key] = value

    def apply(self, config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise TypeError("config must be a dictionary")
        self.config.update(config)
