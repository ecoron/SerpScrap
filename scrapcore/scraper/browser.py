"""Chrome WebDriver configuration and search-engine navigation adapters."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from selenium import webdriver
from selenium.webdriver.chrome.service import Service


class BrowserConfigurationError(ValueError):
    """Raised when Chrome cannot be configured safely."""


@dataclass(frozen=True, slots=True)
class BrowserSettings:
    headless: bool = True
    executable_path: str | None = None
    binary_location: str | None = None
    user_agent: str | None = None
    window_width: int = 1366
    window_height: int = 900
    page_load_timeout: float = 30.0
    wait_timeout: float = 15.0
    no_sandbox: bool = False
    disable_dev_shm_usage: bool = True

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> BrowserSettings:
        settings = cls(
            headless=bool(config.get("chrome_headless", True)),
            executable_path=config.get("executable_path") or None,
            binary_location=config.get("chrome_binary") or None,
            user_agent=config.get("user_agent") or None,
            window_width=int(config.get("window_width", 1366)),
            window_height=int(config.get("window_height", 900)),
            page_load_timeout=float(config.get("page_load_timeout", 30)),
            wait_timeout=float(config.get("wait_timeout", 15)),
            no_sandbox=bool(config.get("chrome_no_sandbox", False)),
            disable_dev_shm_usage=bool(config.get("disable_dev_shm_usage", True)),
        )
        if settings.window_width < 320 or settings.window_height < 240:
            raise BrowserConfigurationError("Chrome window dimensions are too small")
        if settings.page_load_timeout <= 0 or settings.wait_timeout <= 0:
            raise BrowserConfigurationError("Chrome timeouts must be positive")
        return settings


class ChromeDriverFactory:
    """Create configured Chrome drivers; Selenium Manager resolves the default driver."""

    def __init__(self, settings: BrowserSettings):
        self.settings = settings

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ChromeDriverFactory:
        return cls(BrowserSettings.from_config(config))

    def create(self, proxy: Any = None):
        options = webdriver.ChromeOptions()
        if self.settings.headless:
            options.add_argument("--headless=new")
        options.add_argument(
            f"--window-size={self.settings.window_width},{self.settings.window_height}"
        )
        options.add_argument("--disable-gpu")
        if self.settings.disable_dev_shm_usage:
            options.add_argument("--disable-dev-shm-usage")
        if self.settings.no_sandbox:
            options.add_argument("--no-sandbox")
        if self.settings.user_agent:
            options.add_argument(f"--user-agent={self.settings.user_agent}")
        if self.settings.binary_location:
            options.binary_location = self.settings.binary_location
        if proxy:
            if getattr(proxy, "username", None) or getattr(proxy, "password", None):
                raise BrowserConfigurationError(
                    "Authenticated proxies require an external Chrome extension and are not supported"
                )
            options.add_argument(f"--proxy-server={proxy.proto}://{proxy.host}:{proxy.port}")

        service = (
            Service(executable_path=self.settings.executable_path)
            if self.settings.executable_path
            else Service()
        )
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(self.settings.page_load_timeout)
        driver.set_window_size(self.settings.window_width, self.settings.window_height)
        return driver


class GoogleSearchAdapter:
    """Build Google query URLs and define observable SERP states."""

    result_selectors = ("#search", "#rso", "div[role='main']")
    blocked_url_fragments = ("/sorry/", "/sorry/index")
    blocked_html_needles = ("unusual traffic", "automated queries")
    consent_url_fragments = ("consent.google.",)
    empty_result_needles = ("did not match any documents", "No results found for")

    def __init__(self, config: dict[str, Any]):
        self.config = config

    def build_url(self, query: str, page_number: int, search_type: str = "normal") -> str:
        if page_number < 1:
            raise ValueError("page_number must be at least 1")
        base = self.config.get("google_search_url", "https://www.google.com/search?")
        params: dict[str, str | int] = {
            "q": query,
            "num": int(self.config.get("num_results_per_page", 10)),
            "start": (page_number - 1) * int(self.config.get("num_results_per_page", 10)),
            "hl": self.config.get("language", "en"),
            "filter": "0",
        }
        if search_type == "image":
            params["tbm"] = "isch"
        separator = "" if base.endswith(("?", "&")) else "?"
        return f"{base}{separator}{urlencode(params)}"

    def classify(self, current_url: str, html: str) -> str | None:
        url_lower = current_url.lower()
        html_lower = html.lower()
        if any(fragment in url_lower for fragment in self.blocked_url_fragments):
            return "blocked"
        if any(needle.lower() in html_lower for needle in self.blocked_html_needles):
            return "blocked"
        if any(fragment in url_lower for fragment in self.consent_url_fragments):
            return "consent_required"
        if any(needle.lower() in html_lower for needle in self.empty_result_needles):
            return "empty"
        return None


def safe_artifact_name(query: str) -> str:
    """Return a filesystem-safe, bounded query fragment."""

    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", query).strip("-._")
    return (normalized or "query")[:80]


def screenshot_path(config: dict[str, Any], query: str, correlation_id: str, page: int) -> Path:
    root = Path(config["dir_screenshot"]) / config["today"]
    root.mkdir(parents=True, exist_ok=True)
    return root / f"google_{safe_artifact_name(query)}_{correlation_id[:8]}-p{page}.png"
