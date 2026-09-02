"""Shared contracts and deterministic processing for thematic sources."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, ClassVar
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class TopicReadiness(str, Enum):
    ENABLED = "enabled"
    EXPERIMENTAL = "experimental"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class TopicCapabilities:
    search_types: tuple[str, ...] = ("search",)
    supported_countries: frozenset[str] = frozenset()
    supported_languages: frozenset[str] = frozenset()
    transport: str = "http"
    pagination: str = "none"
    readiness: TopicReadiness = TopicReadiness.ENABLED

    def to_dict(self) -> dict[str, Any]:
        return {
            "search_types": list(self.search_types),
            "supported_countries": sorted(self.supported_countries),
            "supported_languages": sorted(self.supported_languages),
            "transport": self.transport,
            "pagination": self.pagination,
            "readiness": self.readiness.value,
        }


@dataclass(frozen=True, slots=True)
class TopicRequest:
    query: str
    topic: str
    sources: tuple[str, ...] = ()
    country: str | None = None
    language: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    page: int = 1

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("query must not be empty")
        if self.page < 1:
            raise ValueError("page must be at least 1")
        if self.country:
            object.__setattr__(self, "country", self.country.upper())
        if self.language:
            object.__setattr__(self, "language", self.language.lower())
        if self.since and self.until and self.since > self.until:
            raise ValueError("since must not be after until")

    @classmethod
    def create(
        cls,
        query: str,
        *,
        topic: str,
        sources: list[str] | tuple[str, ...] = (),
        country: str | None = None,
        language: str | None = None,
        since: str | datetime | None = None,
        until: str | datetime | None = None,
        filters: dict[str, Any] | None = None,
    ) -> TopicRequest:
        return cls(
            query.strip(),
            topic,
            tuple(dict.fromkeys(sources)),
            country,
            language,
            _parse_time(since),
            _parse_time(until),
            dict(filters or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "topic": self.topic,
            "sources": list(self.sources),
            "country": self.country,
            "language": self.language,
            "since": self.since.isoformat() if self.since else None,
            "until": self.until.isoformat() if self.until else None,
            "filters": dict(self.filters),
            "page": self.page,
        }


@dataclass(frozen=True, slots=True)
class TopicResult:
    url: str
    title: str
    snippet: str | None = None
    source: str | None = None
    rank: int = 0
    published_at: datetime | None = None
    author: str | None = None
    category: str | None = None
    language: str | None = None
    raw_url: str | None = None
    canonical_url: str | None = None
    extras: dict[str, Any] = field(default_factory=dict, compare=False)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "url": self.url,
            "raw_url": self.raw_url or self.url,
            "canonical_url": self.canonical_url or canonical_url(self.url),
            "title": self.title,
            "snippet": self.snippet,
            "source": self.source,
            "rank": self.rank,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "author": self.author,
            "category": self.category,
            "language": self.language,
            **self.extras,
        }
        return payload


@dataclass(slots=True)
class TopicReport:
    topic: str
    query: str
    results: list[TopicResult] = field(default_factory=list)
    source_status: dict[str, dict[str, Any]] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "topic": self.topic,
            "query": self.query,
            "results": [result.to_dict() for result in self.results],
            "source_status": self.source_status,
            "errors": self.errors,
            "duration_ms": round(self.duration_ms, 3),
        }


class TopicPlugin(ABC):
    contract_version: ClassVar[str] = "1"
    topic_id: ClassVar[str]
    source_id: ClassVar[str | None] = None
    display_name: ClassVar[str]
    capabilities: ClassVar[TopicCapabilities] = TopicCapabilities()

    def build_request(self, request: TopicRequest) -> TopicRequest:
        return request

    @abstractmethod
    def build_url(self, request: TopicRequest, *, page: int) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse(self, payload: str, *, request: TopicRequest, page: int) -> list[TopicResult]:
        raise NotImplementedError

    def normalize(self, result: TopicResult) -> TopicResult:
        return replace(
            result,
            url=canonical_url(result.url),
            canonical_url=canonical_url(result.url),
            raw_url=result.raw_url or result.url,
        )

    def classify(self, payload: str) -> str | None:
        return None

    def validate_contract(self) -> tuple[str, ...]:
        errors: list[str] = []
        if (
            not self.topic_id
            or self.topic_id != self.topic_id.lower()
            or not re.fullmatch(r"[a-z0-9_-]+", self.topic_id)
        ):
            errors.append("topic_id must be lowercase ASCII")
        if not self.display_name:
            errors.append("display_name is required")
        if self.source_id is not None and not re.fullmatch(r"[a-z0-9_-]+", self.source_id):
            errors.append("source_id must be lowercase ASCII")
        if self.capabilities.transport not in {"http", "browser", "feed", "hybrid"}:
            errors.append("unsupported transport")
        if self.capabilities.pagination not in {"none", "page", "offset", "cursor"}:
            errors.append("unsupported pagination")
        if self.capabilities.readiness != TopicReadiness.ENABLED and not getattr(
            self, "disable_reason", None
        ):
            errors.append("disable_reason is required when plugin is not enabled")
        return tuple(errors)

    def metadata(self) -> dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "source_id": self.source_id or self.topic_id,
            "display_name": self.display_name,
            "contract_version": self.contract_version,
            "capabilities": self.capabilities.to_dict(),
            "readiness": self.capabilities.readiness.value,
        }


def canonical_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"}:
        return value.strip()
    query = [
        (key, val)
        for key, val in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith(("utm_", "gclid", "fbclid"))
    ]
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/") or "/",
            urlencode(query),
            "",
        )
    )


def deduplicate(results: list[TopicResult]) -> list[TopicResult]:
    seen: set[str] = set()
    output: list[TopicResult] = []
    for result in results:
        identity = (
            result.extras.get("dedupe_key") or result.canonical_url or canonical_url(result.url)
        )
        if identity in seen:
            continue
        seen.add(identity)
        output.append(result)
    return [replace(item, rank=index) for index, item in enumerate(output, 1)]


def _parse_time(value: str | datetime | None) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    match = re.fullmatch(r"(\d+)\s*(m|h|d|w)", value.strip().lower())
    if match:
        amount, unit = int(match.group(1)), match.group(2)
        if unit == "m":
            return datetime.now(timezone.utc) - timedelta(minutes=amount)
        if unit == "h":
            return datetime.now(timezone.utc) - timedelta(hours=amount)
        return datetime.now(timezone.utc) - timedelta(days=amount * (7 if unit == "w" else 1))
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
