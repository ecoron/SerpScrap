"""Public request and report values for SerpScrap."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any

from serpscrap.config import Config
from serpscrap.exceptions import ConfigurationError

SCHEMA_VERSION = 2


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, frozenset):
        return {_thaw(item) for item in value}
    return value


def _queries(value: str | Iterable[str]) -> tuple[str, ...]:
    items = [value] if isinstance(value, str) else list(value)
    normalized = tuple(dict.fromkeys(str(item).strip() for item in items if str(item).strip()))
    if not normalized:
        raise ConfigurationError("At least one non-empty query is required")
    return normalized


@dataclass(frozen=True, slots=True)
class SearchRequest:
    """A complete, validated request passed to the application service."""

    queries: tuple[str, ...]
    settings: Mapping[str, Any] = field(repr=False)

    @classmethod
    def create(
        cls,
        queries: str | Iterable[str],
        config: Config | Mapping[str, Any] | None = None,
        **options: Any,
    ) -> SearchRequest:
        merged = Config()
        if isinstance(config, Config):
            merged.apply(config.get())
        elif config is not None:
            merged.apply(dict(config))
        if options:
            merged.apply(options)
        settings = dict(merged.get())
        settings["keywords"] = list(_queries(queries))
        from scrapcore.scraper.browser import ChromeIdentityProvider

        settings["user_agent"] = ChromeIdentityProvider().resolve(
            settings.get("user_agent") or None,
            settings.get("chrome_binary") or None,
        )
        from scrapcore.validator_config import ValidatorConfig

        ValidatorConfig().validate(settings)
        return cls(queries=tuple(settings["keywords"]), settings=_freeze(settings))

    def to_config(self) -> dict[str, Any]:
        """Return an isolated legacy configuration for infrastructure adapters."""

        config = _thaw(self.settings)
        config["keywords"] = list(self.queries)
        return config


@dataclass(frozen=True, slots=True)
class FailureRecord:
    """JSON-compatible description of a failed SERP page."""

    query: str
    search_engine: str
    page_number: int
    url: str | None
    category: str
    message: str
    retryable: bool
    correlation_id: str | None = None
    attempt_count: int = 1
    country_code: str | None = None
    plugin_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "query": self.query,
            "search_engine": self.search_engine,
            "page_number": self.page_number,
            "url": self.url,
            "category": self.category,
            "message": self.message,
            "retryable": self.retryable,
            "correlation_id": self.correlation_id,
            "attempt_count": self.attempt_count,
        }
        if self.country_code is not None:
            payload["country_code"] = self.country_code
        if self.plugin_version is not None:
            payload["plugin_version"] = self.plugin_version
        return payload


@dataclass(slots=True)
class SearchReport:
    """Complete outcome while keeping the primary response as ``list[dict]``."""

    results: list[dict[str, Any]] = field(default_factory=list)
    related_keywords: list[dict[str, Any]] = field(default_factory=list)
    failures: list[FailureRecord] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stopped_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: int = SCHEMA_VERSION
    report_metadata: dict[str, Any] = field(default_factory=dict)

    def metadata(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "started_at": self.started_at.isoformat(),
            "stopped_at": self.stopped_at.isoformat(),
            "failures": [failure.to_dict() for failure in self.failures],
            "related_keywords": [dict(item) for item in self.related_keywords],
            **self.report_metadata,
        }
