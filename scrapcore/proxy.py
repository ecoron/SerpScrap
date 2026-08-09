"""Validated proxy sources, health checks, and bounded proxy selection."""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import socket
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
ALLOWED_PROTOCOLS = frozenset({"http", "socks4", "socks5"})


@dataclass(frozen=True, slots=True)
class ProxyEndpoint:
    """A normalized proxy endpoint safe to pass to the browser layer."""

    proto: str
    host: str
    port: int
    username: str = ""
    password: str = ""
    source: str = ""
    country_code: str = ""
    last_checked: datetime | None = None

    def __post_init__(self) -> None:
        proto = self.proto.lower().removesuffix("://")
        if proto not in ALLOWED_PROTOCOLS:
            raise ValueError(f"unsupported proxy protocol: {self.proto}")
        if not self.host or any(character.isspace() for character in self.host):
            raise ValueError("proxy host must be non-empty and contain no whitespace")
        if not 1 <= int(self.port) <= 65535:
            raise ValueError("proxy port must be between 1 and 65535")
        object.__setattr__(self, "proto", proto)
        object.__setattr__(self, "port", int(self.port))

    @property
    def key(self) -> str:
        return f"{self.proto}://{self.host}:{self.port}"

    @property
    def redacted(self) -> str:
        return self.key


def parse_proxy_line(line: str, source: str = "") -> ProxyEndpoint | None:
    """Parse URL, host:port, or the legacy ``proto host:port [credentials]``."""

    value = line.strip()
    if not value or value.startswith(("#", "//")):
        return None
    tokens = value.split()
    if len(tokens) >= 2 and "://" not in tokens[0] and ":" not in tokens[0]:
        proto, address = tokens[0], tokens[1]
        credentials = tokens[2] if len(tokens) > 2 else ""
    else:
        proto = "http"
        address = tokens[0]
        credentials = ""
    if "://" in address:
        parsed = urlparse(address)
        proto = parsed.scheme
        host = parsed.hostname or ""
        port = parsed.port
        credentials = (
            f"{parsed.username}:{parsed.password}"
            if parsed.username is not None and parsed.password is not None
            else ""
        )
    else:
        host, separator, port_text = address.rpartition(":")
        if not separator or not host or not port_text.isdigit():
            raise ValueError(f"invalid proxy endpoint: {line.strip()}")
        port = int(port_text)
    username = password = ""
    if credentials:
        username, separator, password = credentials.partition(":")
        if not separator or not username or not password:
            raise ValueError("proxy credentials must use username:password")
    if port is None:
        raise ValueError(f"proxy endpoint has no port: {line.strip()}")
    return ProxyEndpoint(proto, host, port, username, password, source)


class ProxySource:
    """Source interface returning raw proxy lines."""

    def load(self) -> list[ProxyEndpoint]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class FileProxySource(ProxySource):
    location: str

    def load(self) -> list[ProxyEndpoint]:
        path = Path(self.location)
        if not path.is_file():
            raise ValueError(f"proxy source is not a file: {self.location}")
        return _parse_payload(path.read_bytes(), str(path))


@dataclass(frozen=True, slots=True)
class DirectoryProxySource(ProxySource):
    location: str
    extensions: tuple[str, ...] = (".txt", ".list", ".proxy", ".json", ".csv")

    def load(self) -> list[ProxyEndpoint]:
        path = Path(self.location)
        if not path.is_dir():
            raise ValueError(f"proxy source is not a directory: {self.location}")
        endpoints: list[ProxyEndpoint] = []
        for child in sorted(path.iterdir()):
            if child.is_file() and child.suffix.lower() in self.extensions:
                endpoints.extend(_parse_payload(child.read_bytes(), str(child)))
        return endpoints


@dataclass(frozen=True, slots=True)
class UrlProxySource(ProxySource):
    location: str
    timeout: float = 10.0
    max_bytes: int = 2 * 1024 * 1024
    cache_dir: str = ""
    cache_ttl: float = 900.0

    def load(self) -> list[ProxyEndpoint]:
        parsed = urlparse(self.location)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("proxy URL sources must use an absolute HTTPS URL")
        cache_path = self._cache_path()
        if cache_path and cache_path.is_file() and time.time() - cache_path.stat().st_mtime <= self.cache_ttl:
            payload = cache_path.read_bytes()
        else:
            request = urllib.request.Request(self.location, headers={"User-Agent": "SerpScrap proxy source"})
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    payload = response.read(self.max_bytes + 1)
            except (OSError, urllib.error.URLError) as exc:
                raise ValueError(f"could not load proxy source {self.location}: {exc}") from exc
            if len(payload) <= self.max_bytes and cache_path:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_bytes(payload)
        if len(payload) > self.max_bytes:
            raise ValueError(f"proxy source exceeds {self.max_bytes} bytes")
        return _parse_payload(payload, self.location)

    def _cache_path(self) -> Path | None:
        if not self.cache_dir:
            return None
        digest = hashlib.sha256(self.location.encode("utf-8")).hexdigest()[:24]
        return Path(self.cache_dir) / f"{digest}.proxy-source"


def _parse_lines(payload: str, source: str) -> list[ProxyEndpoint]:
    endpoints: list[ProxyEndpoint] = []
    for line_number, line in enumerate(payload.splitlines(), 1):
        try:
            endpoint = parse_proxy_line(line, source)
        except ValueError as exc:
            raise ValueError(f"{source}:{line_number}: {exc}") from exc
        if endpoint:
            endpoints.append(endpoint)
    return endpoints


def _parse_payload(payload: bytes, source: str) -> list[ProxyEndpoint]:
    """Parse newline, JSON, or CSV proxy lists into normalized endpoints."""

    text = payload.decode("utf-8", errors="replace")
    stripped = text.lstrip()
    if source.lower().split("?", 1)[0].endswith(".json") or stripped.startswith(("[", "{")):
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{source}: invalid JSON proxy list") from exc
        records = value if isinstance(value, list) else value.get("data", value.get("proxies", value.get("results", [])))
        if not isinstance(records, list):
            raise ValueError(f"{source}: JSON proxy list must contain an array")
        return _parse_records(records, source)
    first_line = stripped.splitlines()[0] if stripped else ""
    header = {item.strip().lower() for item in first_line.split(",")}
    if source.lower().split("?", 1)[0].endswith(".csv") or header.intersection({"ip", "host", "protocol"}):
        return _parse_records(list(csv.DictReader(text.splitlines())), source)
    return _parse_lines(text, source)


def _endpoint_from_record(record: dict, source: str) -> ProxyEndpoint:
    host = str(record.get("host") or record.get("ip") or record.get("address") or "")
    port = record.get("port")
    proto = str(record.get("protocol") or record.get("type") or record.get("scheme") or "http")
    country = str(record.get("country_code") or record.get("country") or "").upper()
    checked = record.get("last_checked") or record.get("lastChecked")
    checked_at = None
    if isinstance(checked, (int, float)):
        checked_at = datetime.fromtimestamp(checked, tz=timezone.utc)
    elif checked:
        try:
            checked_at = datetime.fromisoformat(str(checked).replace("Z", "+00:00"))
        except ValueError:
            pass
    if not host or port in (None, ""):
        raise ValueError(f"{source}: proxy record is missing host or port")
    return ProxyEndpoint(proto, host, int(port), source=source, country_code=country, last_checked=checked_at)


def _parse_records(records: list, source: str) -> list[ProxyEndpoint]:
    """Parse records independently so one unsupported public entry cannot drop a source."""

    endpoints: list[ProxyEndpoint] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        try:
            endpoints.append(_endpoint_from_record(record, source))
        except (TypeError, ValueError):
            continue
    return endpoints


def sources_from_config(config: dict) -> list[ProxySource]:
    """Build configured sources while retaining support for ``proxy_file``."""

    definitions = config.get("proxy_sources") or []
    if isinstance(definitions, str):
        definitions = [{"type": "file", "location": definitions}]
    if not definitions and config.get("proxy_file"):
        definitions = [{"type": "file", "location": config["proxy_file"]}]
    sources: list[ProxySource] = []
    for definition in definitions:
        if not isinstance(definition, dict):
            raise ValueError("proxy_sources entries must be mappings")
        kind = str(definition.get("type", "")).lower()
        location = str(definition.get("location", ""))
        if kind == "file":
            sources.append(FileProxySource(location))
        elif kind == "directory":
            sources.append(DirectoryProxySource(location))
        elif kind == "url":
            sources.append(
                UrlProxySource(
                    location,
                    float(config.get("proxy_source_timeout", 10)),
                    int(config.get("proxy_source_max_bytes", 2 * 1024 * 1024)),
                    str(config.get("proxy_cache_dir", "")),
                    float(config.get("proxy_cache_ttl", 900)),
                )
            )
        else:
            raise ValueError(f"unsupported proxy source type: {kind}")
    return sources


@dataclass(slots=True)
class ProxyHealth:
    online: bool = False
    latency_ms: float | None = None
    failures: int = 0
    last_error: str = ""
    cooldown_until: float = 0.0
    checked_at: datetime | None = None


class ProxyHealthChecker:
    """Check proxy reachability without exposing credentials in diagnostics."""

    def __init__(self, check_url: str, timeout: float = 10.0, failure_threshold: int = 2):
        parsed = urlparse(check_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("proxy_check_url must be an absolute HTTP(S) URL")
        self.check_url = check_url
        self.timeout = float(timeout)
        self.failure_threshold = max(1, int(failure_threshold))

    def check(self, proxy: ProxyEndpoint) -> ProxyHealth:
        started = monotonic()
        try:
            if proxy.proto.startswith("socks"):
                with socket.create_connection((proxy.host, proxy.port), timeout=self.timeout):
                    pass
            else:
                handler = urllib.request.ProxyHandler({
                    "http": proxy.key,
                    "https": proxy.key,
                })
                opener = urllib.request.build_opener(handler)
                with opener.open(self.check_url, timeout=self.timeout) as response:
                    if response.status >= 400:
                        raise OSError(f"health check returned HTTP {response.status}")
                    response.read(1024)
            return ProxyHealth(online=True, latency_ms=(monotonic() - started) * 1000)
        except (OSError, urllib.error.URLError, ValueError) as exc:
            return ProxyHealth(online=False, failures=1, last_error=str(exc)[:300])


class ProxyPool:
    """Deduplicated proxy pool with health and search-engine selection state."""

    def __init__(self, endpoints: list[ProxyEndpoint], health_checker: ProxyHealthChecker | None = None):
        unique = {endpoint.key: endpoint for endpoint in endpoints}
        self.endpoints = list(unique.values())
        self.health_checker = health_checker
        self.health = {endpoint.key: ProxyHealth() for endpoint in self.endpoints}
        self._cursor: dict[str, int] = {}

    @classmethod
    def from_config(cls, config: dict, *, refresh: bool = True) -> ProxyPool:
        endpoints: list[ProxyEndpoint] = []
        errors: list[str] = []
        for source in sources_from_config(config):
            try:
                endpoints.extend(source.load())
            except ValueError as exc:
                errors.append(str(exc))
                logger.warning("Proxy source skipped: %s", exc)
        allowed_protocols = {
            str(item).lower() for item in config.get("proxy_allowed_protocols", ALLOWED_PROTOCOLS)
        }
        allowed_countries = {str(item).upper() for item in config.get("proxy_allowed_countries", [])}
        max_age = float(config.get("proxy_max_age_seconds", 0))
        now = datetime.now(timezone.utc)
        endpoints = [
            endpoint for endpoint in endpoints
            if endpoint.proto in allowed_protocols
            and (not allowed_countries or endpoint.country_code in allowed_countries)
            and (
                not max_age
                or not endpoint.last_checked
                or (now - endpoint.last_checked.astimezone(timezone.utc)).total_seconds() <= max_age
            )
        ]
        max_endpoints = int(config.get("proxy_max_endpoints", 500))
        if max_endpoints < 1:
            raise ValueError("proxy_max_endpoints must be positive")
        endpoints = endpoints[:max_endpoints]
        if not endpoints:
            raise ValueError("No valid proxies available" + (f": {'; '.join(errors)}" if errors else ""))
        checker = None
        if config.get("check_proxies", True):
            checker = ProxyHealthChecker(
                str(config.get("proxy_check_url", "https://icanhazip.com/")),
                float(config.get("proxy_check_timeout", 10)),
                int(config.get("proxy_failure_threshold", 2)),
            )
        pool = cls(endpoints, checker)
        if checker and refresh:
            pool.refresh_health()
        return pool

    def refresh_health(self) -> None:
        if not self.health_checker:
            return
        workers = min(16, max(1, len(self.endpoints)))
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="proxy-check") as executor:
            results = executor.map(self.health_checker.check, self.endpoints)
        for endpoint, status in zip(self.endpoints, results, strict=True):
            previous = self.health[endpoint.key]
            status.failures = 0 if status.online else previous.failures + 1
            status.checked_at = datetime.now(timezone.utc).replace(tzinfo=None)
            if not status.online and status.failures >= self.health_checker.failure_threshold:
                status.cooldown_until = monotonic() + 60
            self.health[endpoint.key] = status

    def restore_from_db(self, session) -> None:
        """Restore durable health state for endpoints already in the database."""

        from scrapcore.database import Proxy

        for endpoint in self.endpoints:
            record = (
                session.query(Proxy)
                .filter(Proxy.ip == endpoint.host, Proxy.port == endpoint.port)
                .first()
            )
            if not record:
                continue
            self.health[endpoint.key] = ProxyHealth(
                online=bool(record.online),
                latency_ms=record.latency_ms,
                failures=int(record.failure_count or 0),
                last_error=record.last_error or "",
                cooldown_until=float(record.cooldown_until or 0),
                checked_at=record.checked_at,
            )

    def persist(self, session, search_engines: list[str]) -> None:
        """Upsert endpoint health and engine-specific availability."""

        from scrapcore.database import Proxy, SearchEngine, SearchEngineProxyStatus

        engines = {
            engine.name: engine
            for engine in session.query(SearchEngine).filter(SearchEngine.name.in_(search_engines)).all()
        }
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for endpoint in self.endpoints:
            health = self.health[endpoint.key]
            record = (
                session.query(Proxy)
                .filter(Proxy.ip == endpoint.host, Proxy.port == endpoint.port)
                .first()
            )
            if record is None:
                record = Proxy(ip=endpoint.host, port=endpoint.port)
            record.proto = endpoint.proto
            record.username = endpoint.username
            record.password = endpoint.password
            record.source = endpoint.source
            record.online = health.online
            record.status = "online" if health.online else "offline"
            record.checked_at = health.checked_at or now
            record.latency_ms = health.latency_ms
            record.failure_count = health.failures
            record.cooldown_until = health.cooldown_until
            record.last_error = health.last_error
            session.add(record)
            session.flush()
            for _engine_name, engine in engines.items():
                status = (
                    session.query(SearchEngineProxyStatus)
                    .filter(
                        SearchEngineProxyStatus.proxy_id == record.id,
                        SearchEngineProxyStatus.search_engine_id == engine.id,
                    )
                    .first()
                )
                if status is None:
                    status = SearchEngineProxyStatus(
                        proxy_id=record.id, search_engine_id=engine.id
                    )
                status.available = health.online and health.cooldown_until <= monotonic()
                status.last_check = health.checked_at or now
                status.latency_ms = health.latency_ms
                status.last_error = health.last_error
                session.add(status)
        session.commit()

    def available(self) -> list[ProxyEndpoint]:
        now = monotonic()
        return [
            endpoint for endpoint in self.endpoints
            if self.health[endpoint.key].online and self.health[endpoint.key].cooldown_until <= now
        ] or ([endpoint for endpoint in self.endpoints if not self.health[endpoint.key].cooldown_until] if not self.health_checker else [])

    def select(
        self, search_engine: str, exclude: ProxyEndpoint | None = None
    ) -> ProxyEndpoint:
        excluded = exclude.key if exclude else None
        candidates = [endpoint for endpoint in self.available() if endpoint.key != excluded]
        if not candidates and exclude is None:
            candidates = self.available()
        if not candidates:
            raise ValueError(f"No healthy proxy available for {search_engine}")
        index = self._cursor.get(search_engine, 0) % len(candidates)
        self._cursor[search_engine] = index + 1
        return candidates[index]

    def mark_failure(self, proxy: ProxyEndpoint, error: Exception) -> None:
        """Record a transient worker failure and put the endpoint on cooldown."""

        health = self.health[proxy.key]
        health.online = False
        health.failures += 1
        health.last_error = str(error)[:300]
        health.cooldown_until = monotonic() + 60
        health.checked_at = datetime.now(timezone.utc).replace(tzinfo=None)

    def mark_success(self, proxy: ProxyEndpoint) -> None:
        """Clear transient failure state after a successful capture."""

        health = self.health[proxy.key]
        health.online = True
        health.failures = 0
        health.last_error = ""
        health.cooldown_until = 0.0
        health.checked_at = datetime.now(timezone.utc).replace(tzinfo=None)
