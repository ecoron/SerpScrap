"""Public SerpScrap configuration with backward-compatible dictionary access."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import gettempdir
from typing import Any


class Config:
    """Mutable configuration facade retained for the public API."""

    def __init__(self) -> None:
        temp_root = Path(gettempdir())
        self.config: dict[str, Any] = {
            "use_own_ip": True,
            "search_engines": ["google"],
            "supported_search_engines": ["google"],
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
            "wait_timeout": 15,
            "user_agent": "",
            "language": "en",
            "do_caching": True,
            "cachedir": str(temp_root / ".serpscrap"),
            "screenshot": False,
            "dir_screenshot": str(temp_root / "serpscrap-screenshots"),
            "database_name": str(temp_root / "serpscrap"),
            "minimize_caching_files": False,
            "clean_cache_after": 24,
            "output_filename": None,
            "print_results": None,
            "scrape_urls": False,
            "url_threads": 6,
            "log_level": "INFO",
            "num_workers": 1,
            "num_results_per_page": 10,
            "results_age": "Any",
            "search_type": "normal",
            "google_search_url": "https://www.google.com/search?",
            "headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.8",
            },
            "proxy_file": "",
            "proxy_check_url": "https://icanhazip.com/",
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
