"""Chrome WebDriver configuration and search-engine navigation adapters."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from random import Random
from typing import Any
from urllib.parse import urlencode

from selenium import webdriver
from selenium.webdriver.chrome.service import Service


class BrowserConfigurationError(ValueError):
    """Raised when Chrome cannot be configured safely."""


FALLBACK_CHROME_MAJOR = 150
FALLBACK_CHROME_RELEASE_DATE = date(2026, 7, 22)
FALLBACK_CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    f"(KHTML, like Gecko) Chrome/{FALLBACK_CHROME_MAJOR}.0.0.0 Safari/537.36"
)


class ChromeIdentityProvider:
    """Resolve one coherent desktop Chrome identity for a search request."""

    version_pattern = re.compile(r"(?:Google Chrome|Chromium)\s+(\d+)(?:\.\d+){0,3}")
    user_agent_pattern = re.compile(r"\bChrome/(\d+)(?:\.\d+){0,3}\b")

    def __init__(
        self,
        fallback_user_agent: str = FALLBACK_CHROME_USER_AGENT,
        version_reader: Callable[[str | None], int | None] | None = None,
    ) -> None:
        self.fallback_user_agent = fallback_user_agent
        self.version_reader = version_reader or self.detect_installed_major

    @classmethod
    def validate_user_agent(cls, user_agent: str) -> int:
        match = cls.user_agent_pattern.search(user_agent)
        if not match or "Mobile" in user_agent or "HeadlessChrome" in user_agent:
            raise BrowserConfigurationError(
                "user_agent must be a non-headless desktop Google Chrome user agent"
            )
        return int(match.group(1))

    @staticmethod
    def ensure_fallback_fresh(today: date | None = None, max_age_days: int = 120) -> None:
        age = (today or date.today()) - FALLBACK_CHROME_RELEASE_DATE
        if age.days > max_age_days:
            raise BrowserConfigurationError(
                "The bundled Chrome user-agent fallback is stale; update it or configure user_agent"
            )

    @classmethod
    def detect_installed_major(cls, binary_location: str | None = None) -> int | None:
        candidates = [binary_location] if binary_location else []
        if os.name == "nt":
            try:
                import winreg

                for registry_root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                    try:
                        with winreg.OpenKey(
                            registry_root, r"Software\Google\Chrome\BLBeacon"
                        ) as key:
                            version = str(winreg.QueryValueEx(key, "version")[0])
                            if version.split(".", 1)[0].isdigit():
                                return int(version.split(".", 1)[0])
                    except OSError:
                        continue
            except ImportError:
                pass
            for environment_name in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
                environment_root = os.environ.get(environment_name)
                if environment_root:
                    candidates.append(
                        str(
                            Path(environment_root)
                            / "Google"
                            / "Chrome"
                            / "Application"
                            / "chrome.exe"
                        )
                    )
        for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
            discovered = shutil.which(name)
            if discovered:
                candidates.append(discovered)
        for candidate in dict.fromkeys(candidates):
            try:
                completed = subprocess.run(
                    [candidate, "--version"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
            except (OSError, subprocess.SubprocessError):
                continue
            match = cls.version_pattern.search(completed.stdout or completed.stderr)
            if match:
                return int(match.group(1))
        return None

    def resolve(self, configured: str | None, binary_location: str | None = None) -> str:
        if configured:
            self.validate_user_agent(configured)
            return configured
        major = self.version_reader(binary_location)
        fallback = self.fallback_user_agent
        if os.name != "nt":
            fallback = fallback.replace("Windows NT 10.0; Win64; x64", "X11; Linux x86_64")
        fallback_major = self.validate_user_agent(fallback)
        if major is None:
            return fallback
        if major == fallback_major:
            return fallback
        return re.sub(r"\bChrome/\d+(?=\.)", f"Chrome/{major}", fallback)


@dataclass(frozen=True, slots=True)
class RequestPolicy:
    """Validated pacing, retry, and circuit-breaker settings."""

    delay_min: float = 0.75
    delay_max: float = 2.0
    retry_limit: int = 1
    backoff_base: float = 2.0
    backoff_max: float = 10.0
    block_threshold: int = 2

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> RequestPolicy:
        policy = cls(
            delay_min=float(config.get("request_delay_min", 0.75)),
            delay_max=float(config.get("request_delay_max", 2.0)),
            retry_limit=int(config.get("request_retry_limit", 1)),
            backoff_base=float(config.get("request_backoff_base", 2.0)),
            backoff_max=float(config.get("request_backoff_max", 10.0)),
            block_threshold=int(config.get("block_threshold", 2)),
        )
        if policy.delay_min < 0 or policy.delay_max < policy.delay_min:
            raise BrowserConfigurationError("request delay range is invalid")
        if policy.retry_limit < 0 or policy.retry_limit > 5:
            raise BrowserConfigurationError("request_retry_limit must be between 0 and 5")
        if policy.backoff_base < 0 or policy.backoff_max < policy.backoff_base:
            raise BrowserConfigurationError("request backoff range is invalid")
        if policy.block_threshold < 1:
            raise BrowserConfigurationError("block_threshold must be positive")
        return policy


class RequestPacer:
    """Serialize navigation starts and keep a jittered gap between them."""

    def __init__(
        self,
        policy: RequestPolicy,
        *,
        sleeper: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        random: Random | None = None,
    ) -> None:
        self.policy = policy
        self.sleeper = sleeper
        self.monotonic = monotonic
        self.random = random or Random()
        self._last_request: float | None = None
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = self.monotonic()
            if self._last_request is not None:
                delay = self.random.uniform(self.policy.delay_min, self.policy.delay_max)
                remaining = self._last_request + delay - now
                if remaining > 0:
                    self.sleeper(remaining)
            self._last_request = self.monotonic()

    def backoff(self, attempt: int) -> None:
        delay = min(self.policy.backoff_max, self.policy.backoff_base * (2 ** (attempt - 1)))
        if delay > 0:
            self.sleeper(delay)


class RunCircuitBreaker:
    """Stop new navigations after repeated explicit access-control responses."""

    def __init__(self, threshold: int) -> None:
        self.threshold = threshold
        self._failures = 0
        self._lock = threading.Lock()

    @property
    def open(self) -> bool:
        with self._lock:
            return self._failures >= self.threshold

    def record_block(self) -> None:
        with self._lock:
            self._failures += 1


@dataclass(frozen=True, slots=True)
class BrowserSettings:
    headless: bool = True
    executable_path: str | None = None
    binary_location: str | None = None
    user_agent: str = FALLBACK_CHROME_USER_AGENT
    language: str = "de-DE"
    window_width: int = 1366
    window_height: int = 900
    page_load_timeout: float = 30.0
    wait_timeout: float = 15.0
    no_sandbox: bool = False
    disable_dev_shm_usage: bool = True

    @classmethod
    def from_config(
        cls,
        config: dict[str, Any],
        identity_provider: ChromeIdentityProvider | None = None,
    ) -> BrowserSettings:
        provider = identity_provider or ChromeIdentityProvider()
        binary_location = config.get("chrome_binary") or None
        settings = cls(
            headless=bool(config.get("chrome_headless", True)),
            executable_path=config.get("executable_path") or None,
            binary_location=binary_location,
            user_agent=provider.resolve(config.get("user_agent") or None, binary_location),
            language=str(config.get("language", "de-DE")),
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
        options.add_argument(f"--lang={self.settings.language}")
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
        if "Windows NT" in self.settings.user_agent:
            platform = "Windows"
        elif "Macintosh" in self.settings.user_agent:
            platform = "macOS"
        else:
            platform = "Linux"
        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {
                "userAgent": self.settings.user_agent,
                "acceptLanguage": self.settings.language,
                "platform": platform,
            },
        )
        driver.set_page_load_timeout(self.settings.page_load_timeout)
        driver.set_window_size(self.settings.window_width, self.settings.window_height)
        return driver


class GoogleSearchAdapter:
    """Build Google query URLs and define observable SERP states."""

    result_selectors = ("#search", "#rso", "div[role='main']")
    blocked_url_fragments = ("/sorry/", "/sorry/index")
    blocked_html_needles = (
        "unusual traffic",
        "automated queries",
        "our systems have detected",
        "g-recaptcha",
        "recaptcha-token",
    )
    rate_limited_html_needles = ("too many requests", "rate limit", "try again later")
    consent_url_fragments = ("consent.google.",)
    empty_result_needles = (
        "did not match any documents",
        "no results found for",
        "keine mit deiner suchanfrage",
        "aucun document ne correspond",
    )
    vertical_parameters = {
        "normal": None,
        "image": "isch",
        "news": "nws",
        "shopping": "shop",
        "videos": "vid",
    }

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
        try:
            vertical = self.vertical_parameters[search_type]
        except KeyError as exc:
            raise ValueError(f"Unsupported Google search type: {search_type}") from exc
        if vertical:
            params["tbm"] = vertical
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
        if any(needle in html_lower for needle in self.rate_limited_html_needles):
            return "rate_limited"
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
