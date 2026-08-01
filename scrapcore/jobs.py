"""Typed values exchanged by the scraping pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ScrapeJob:
    """A complete browser job for one query and search engine."""

    query: str
    search_engine: str = "google"
    search_type: str = "normal"
    pages: tuple[int, ...] = (1,)
    proxy: Any = field(default=None, compare=False, repr=False)
    correlation_id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(frozen=True, slots=True)
class CapturedPage:
    """HTML and request metadata captured from a loaded SERP."""

    query: str
    search_engine: str
    page_number: int
    url: str
    html: str
    requested_at: datetime
    requested_by: str = "localhost"
    screenshot: str | None = None


@dataclass(frozen=True, slots=True)
class ScrapeFailure:
    """A structured failure for one requested SERP page."""

    query: str
    search_engine: str
    page_number: int
    url: str
    category: str
    message: str
    retryable: bool
    correlation_id: str | None = None
    attempt_count: int = 1


@dataclass(frozen=True, slots=True)
class ScrapeJobResult:
    """The partial or complete result of a browser job."""

    job: ScrapeJob
    pages: tuple[CapturedPage, ...] = ()
    failures: tuple[ScrapeFailure, ...] = ()
