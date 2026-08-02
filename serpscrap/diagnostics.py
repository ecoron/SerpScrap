"""Opt-in progress reporting and safe rendered-HTML diagnostics."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import sys
import threading
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Protocol
from urllib.parse import quote, quote_plus, urlsplit


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    """One correlated state transition emitted by a search job."""

    run_id: str
    correlation_id: str
    total_jobs: int
    completed_jobs: int
    sequence: int
    engine: str
    page: int
    state: str
    attempt: int = 1
    elapsed_ms: int = 0
    url_host_path: str | None = None
    selector_key: str | None = None
    artifact_path: str | None = None
    error_category: str | None = None
    result_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProgressSink(Protocol):
    def emit(self, event: ProgressEvent) -> None: ...


class NullProgressSink:
    """No-op sink used by the library unless progress is explicitly enabled."""

    def emit(self, event: ProgressEvent) -> None:
        del event


class LoggingProgressSink:
    """Thread-safe progress sink using the application's existing logger."""

    def __init__(self, logger: logging.Logger, *, output_format: str = "text") -> None:
        self.logger = logger
        self.output_format = output_format

    def emit(self, event: ProgressEvent) -> None:
        self.logger.info(
            "progress %s %s page=%d completed=%d/%d results=%s category=%s correlation_id=%s",
            event.engine,
            event.state,
            event.page,
            event.completed_jobs,
            event.total_jobs,
            event.result_count if event.result_count is not None else "-",
            event.error_category or "-",
            event.correlation_id,
            extra={"progress_event": event.to_dict(), "progress_format": self.output_format},
        )


class JsonLinesProgressSink:
    """Write one JSON progress event per line to stderr."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def emit(self, event: ProgressEvent) -> None:
        line = json.dumps(event.to_dict(), ensure_ascii=False)
        with self._lock:
            print(line, file=sys.stderr, flush=True)


class ProgressCoordinator:
    """Assign ordered sequence/completion values before handing events to a sink."""

    def __init__(self, run_id: str, total_jobs: int, sink: ProgressSink | None = None) -> None:
        self.run_id = run_id
        self.total_jobs = total_jobs
        self.sink = sink or NullProgressSink()
        self._lock = threading.Lock()
        self._sequence = 0
        self._completed = 0

    def emit(
        self,
        *,
        correlation_id: str,
        engine: str,
        page: int,
        state: str,
        attempt: int = 1,
        elapsed_ms: int = 0,
        url: str | None = None,
        selector_key: str | None = None,
        artifact_path: str | None = None,
        error_category: str | None = None,
        result_count: int | None = None,
        terminal: bool = False,
    ) -> ProgressEvent:
        with self._lock:
            self._sequence += 1
            if terminal:
                self._completed += 1
            parsed = urlsplit(url or "")
            host_path = None
            if parsed.netloc:
                host_path = parsed.netloc + (parsed.path or "/")
            event = ProgressEvent(
                run_id=self.run_id,
                correlation_id=correlation_id,
                total_jobs=self.total_jobs,
                completed_jobs=self._completed,
                sequence=self._sequence,
                engine=engine,
                page=page,
                state=state,
                attempt=attempt,
                elapsed_ms=elapsed_ms,
                url_host_path=host_path,
                selector_key=selector_key,
                artifact_path=artifact_path,
                error_category=error_category,
                result_count=result_count,
            )
        self.sink.emit(event)
        return event

    @property
    def completed_jobs(self) -> int:
        with self._lock:
            return self._completed


_SENSITIVE_VALUE = re.compile(
    r"(?i)(cookie|set-cookie|authorization|proxy-authorization|csrf|xsrf|session(?:id)?|api[_-]?key|secret|token)"
    r"(\s*[=:]\s*)([\"']?)([^\"'\s<;&]+)"
)


class DiagnosticArtifactStore:
    """Bounded, atomic, redacted HTML artifact storage for one run."""

    def __init__(
        self,
        root: str | Path,
        run_id: str,
        *,
        max_bytes_per_file: int = 2 * 1024 * 1024,
        max_total_bytes: int = 20 * 1024 * 1024,
        max_artifacts_per_job: int = 10,
    ) -> None:
        self.root = Path(root) / run_id
        self.run_id = run_id
        self.max_bytes_per_file = max_bytes_per_file
        self.max_total_bytes = max_total_bytes
        self.max_artifacts_per_job = max_artifacts_per_job
        self._lock = threading.Lock()
        self._total_bytes = 0
        self._job_counts: dict[str, int] = {}
        self._manifest: list[dict[str, Any]] = []
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "manifest.json"

    @staticmethod
    def _redact(html: str, query: str) -> str:
        redacted = html.replace(query, "[REDACTED_QUERY]")
        encoded = quote(query, safe="")
        if encoded != query:
            redacted = redacted.replace(encoded, "[REDACTED_QUERY]")
        plus_encoded = quote_plus(query)
        if plus_encoded != query:
            redacted = redacted.replace(plus_encoded, "[REDACTED_QUERY]")
        return _SENSITIVE_VALUE.sub(r"\1=[REDACTED]", redacted)

    @staticmethod
    def _safe_token(value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_.-]", "-", value)[:40] or "unknown"

    def _write_manifest(self) -> None:
        payload = {"run_id": self.run_id, "artifacts": list(self._manifest)}
        self.root.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.root, delete=False) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            temporary = Path(handle.name)
        temporary.replace(self.manifest_path)

    def capture(
        self,
        *,
        html: str,
        query: str,
        engine: str,
        page: int,
        state: str,
        correlation_id: str,
        url: str | None = None,
        selector_key: str | None = None,
    ) -> str | None:
        redacted = self._redact(html, query)
        content = redacted.encode("utf-8")
        digest = hashlib.sha256(correlation_id.encode("utf-8")).hexdigest()[:12]
        filename = f"{self._safe_token(engine)}-p{page}-{self._safe_token(state)}-{digest}.html"
        relative = str(Path(filename))
        with self._lock:
            job_count = self._job_counts.get(correlation_id, 0)
            if len(content) > self.max_bytes_per_file:
                reason = "max_bytes_per_file"
            elif job_count >= self.max_artifacts_per_job:
                reason = "max_artifacts_per_job"
            elif self._total_bytes + len(content) > self.max_total_bytes:
                reason = "max_total_bytes"
            else:
                destination = self.root / filename
                with NamedTemporaryFile("wb", dir=self.root, delete=False) as handle:
                    handle.write(content)
                    temporary = Path(handle.name)
                temporary.replace(destination)
                self._total_bytes += len(content)
                self._job_counts[correlation_id] = job_count + 1
                self._manifest.append({
                    "path": relative,
                    "engine": engine,
                    "page": page,
                    "state": state,
                    "correlation_id": correlation_id,
                    "url_host_path": self._url_host_path(url),
                    "selector_key": selector_key,
                    "bytes": len(content),
                    "redaction_version": "1",
                    "status": "written",
                })
                self._write_manifest()
                return str(destination)
            self._manifest.append({
                "path": relative,
                "engine": engine,
                "page": page,
                "state": state,
                "correlation_id": correlation_id,
                "selector_key": selector_key,
                "bytes": len(content),
                "status": "skipped",
                "reason": reason,
            })
            self._write_manifest()
            return None

    def record_terminal(
        self,
        *,
        engine: str,
        page: int,
        correlation_id: str,
        state: str,
        result_count: int | None = None,
        error_category: str | None = None,
        url: str | None = None,
    ) -> None:
        """Record a terminal job summary even when no final HTML was written."""

        with self._lock:
            self._manifest.append({
                "engine": engine,
                "page": page,
                "correlation_id": correlation_id,
                "state": state,
                "result_count": result_count,
                "error_category": error_category,
                "url_host_path": self._url_host_path(url),
                "status": "terminal",
            })
            self._write_manifest()

    @staticmethod
    def _url_host_path(url: str | None) -> str | None:
        parsed = urlsplit(url or "")
        return parsed.netloc + (parsed.path or "/") if parsed.netloc else None


def new_run_id() -> str:
    return uuid.uuid4().hex[:16]
