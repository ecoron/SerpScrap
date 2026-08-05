"""Container-friendly search history persistence and analysis."""

from __future__ import annotations

import csv
import io
import json
import os
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import DateTime, Integer, String, Text, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from serpscrap.models import SearchReport


class _Base(DeclarativeBase):
    pass


class SearchRun(_Base):
    __tablename__ = "search_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    options_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SearchResult(_Base):
    __tablename__ = "search_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    search_engine: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class SearchFailure(_Base):
    __tablename__ = "search_failures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class AppConfiguration(_Base):
    __tablename__ = "app_configurations"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def database_url_from_environment() -> str:
    """Return the configured database URL, defaulting to the mounted data dir."""

    configured = os.getenv("DATABASE_URL")
    if configured:
        return configured
    data_dir = Path(os.getenv("SERPSCRAP_DATA_DIR", "/var/lib/serpscrap"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{data_dir / 'history.db'}"


class SearchHistoryStore:
    """Persist job state and expose small, API-safe history queries."""

    def __init__(self, url: str | None = None) -> None:
        self.url = url or database_url_from_environment()
        connect_args = {"check_same_thread": False} if self.url.startswith("sqlite") else {}
        self.engine = create_engine(self.url, future=True, connect_args=connect_args)
        _Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    def healthcheck(self) -> bool:
        """Return whether the configured persistence backend accepts queries."""

        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception:
            return False
        return True

    def close(self) -> None:
        """Release pooled database connections during application shutdown."""

        self.engine.dispose()

    def create_run(self, run_id: str, query: str, options: dict[str, Any]) -> None:
        with self.sessions.begin() as session:
            session.add(
                SearchRun(
                    id=run_id,
                    query=query,
                    status="queued",
                    options_json=json.dumps(options, ensure_ascii=False, default=str),
                    created_at=_utc_now(),
                )
            )

    def mark_running(self, run_id: str, started_at: datetime | None = None) -> None:
        with self.sessions.begin() as session:
            run = session.get(SearchRun, run_id)
            if run:
                run.status = "running"
                run.started_at = started_at or _utc_now()

    def update_progress(self, run_id: str, total_jobs: int, completed_jobs: int, engine: str | None = None, state: str | None = None) -> None:
        with self.sessions.begin() as session:
            run = session.get(SearchRun, run_id)
            if not run:
                return
            options = json.loads(run.options_json)
            options["_progress"] = {
                "total_jobs": max(0, int(total_jobs)),
                "completed_jobs": max(0, min(int(completed_jobs), int(total_jobs) if total_jobs else 0)),
                "engine": engine or "",
                "state": state or "running",
                "updated_at": _utc_now().isoformat(),
            }
            run.options_json = json.dumps(options, ensure_ascii=False, default=str)

    def store_report(self, run_id: str, report: SearchReport) -> None:
        with self.sessions.begin() as session:
            run = session.get(SearchRun, run_id)
            if not run:
                raise KeyError(run_id)
            for result in report.results:
                session.add(
                    SearchResult(
                        run_id=run_id,
                        search_engine=str(result.get("search_engine") or "unknown"),
                        payload_json=json.dumps(result, ensure_ascii=False, default=str),
                    )
                )
            for failure in report.failures:
                payload = failure.to_dict()
                session.add(
                    SearchFailure(
                        run_id=run_id,
                        category=failure.category,
                        payload_json=json.dumps(payload, ensure_ascii=False, default=str),
                    )
                )
            run.status = "failed" if report.failures and not report.results else "completed"
            run.result_count = len(report.results)
            run.failure_count = len(report.failures)
            run.started_at = report.started_at
            run.stopped_at = report.stopped_at
            options = json.loads(run.options_json)
            progress = options.get("_progress", {})
            if progress.get("total_jobs"):
                progress["completed_jobs"] = progress["total_jobs"]
                progress["state"] = run.status
                options["_progress"] = progress
                run.options_json = json.dumps(options, ensure_ascii=False, default=str)

    def mark_failed(self, run_id: str, message: str) -> None:
        with self.sessions.begin() as session:
            run = session.get(SearchRun, run_id)
            if run:
                run.status = "failed"
                run.failure_count = 1
                run.stopped_at = _utc_now()
                session.add(
                    SearchFailure(
                        run_id=run_id,
                        category="application",
                        payload_json=json.dumps({"category": "application", "search_engine": "unknown", "message": message}),
                    )
                )

    def get_configuration(self, key: str = "default") -> dict[str, Any] | None:
        with self.sessions() as session:
            record = session.get(AppConfiguration, key)
            if record is None:
                return None
            return {
                "key": record.key,
                "revision": record.revision,
                "payload": json.loads(record.payload_json),
                "updated_at": record.updated_at.isoformat(),
            }

    def save_configuration(self, payload: dict[str, Any], key: str = "default") -> dict[str, Any]:
        with self.sessions.begin() as session:
            record = session.get(AppConfiguration, key)
            revision = (record.revision + 1) if record else 1
            if record is None:
                record = AppConfiguration(
                    key=key,
                    revision=revision,
                    payload_json=json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    updated_at=_utc_now(),
                )
                session.add(record)
            else:
                record.revision = revision
                record.payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
                record.updated_at = _utc_now()
            return {
                "key": record.key,
                "revision": record.revision,
                "payload": payload,
                "updated_at": record.updated_at.isoformat(),
            }

    def reset_configuration(self, key: str = "default") -> None:
        with self.sessions.begin() as session:
            record = session.get(AppConfiguration, key)
            if record is not None:
                session.delete(record)

    def delete_run(self, run_id: str) -> bool:
        """Delete one complete search run and all of its persisted children."""

        with self.sessions.begin() as session:
            run = session.get(SearchRun, run_id)
            if run is None:
                return False
            for row in session.scalars(select(SearchResult).where(SearchResult.run_id == run_id)):
                session.delete(row)
            for row in session.scalars(select(SearchFailure).where(SearchFailure.run_id == run_id)):
                session.delete(row)
            session.delete(run)
            return True

    def delete_all_runs(self) -> int:
        """Delete every search run and return the number of removed runs."""

        with self.sessions.begin() as session:
            runs = list(session.scalars(select(SearchRun)))
            session.query(SearchResult).delete(synchronize_session=False)
            session.query(SearchFailure).delete(synchronize_session=False)
            session.query(SearchRun).delete(synchronize_session=False)
            return len(runs)

    @staticmethod
    def _run_dict(run: SearchRun) -> dict[str, Any]:
        options = json.loads(run.options_json)
        return {
            "id": run.id,
            "query": run.query,
            "status": run.status,
            "options": options,
            "progress": options.get("_progress", {}),
            "result_count": run.result_count,
            "failure_count": run.failure_count,
            "created_at": run.created_at.isoformat(),
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "stopped_at": run.stopped_at.isoformat() if run.stopped_at else None,
        }

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            run = session.get(SearchRun, run_id)
            if not run:
                return None
            payload = self._run_dict(run)
            payload["failures"] = self._failure_dicts(session, run_id)
            return payload

    def list_runs(self, limit: int = 50, query: str | None = None) -> list[dict[str, Any]]:
        with self.sessions() as session:
            statement = select(SearchRun).order_by(SearchRun.created_at.desc()).limit(limit)
            if query:
                statement = statement.where(SearchRun.query.ilike(f"%{query}%"))
            return [{**self._run_dict(run), "failures": self._failure_dicts(session, run.id)} for run in session.scalars(statement)]

    @staticmethod
    def _failure_dicts(session: Session, run_id: str) -> list[dict[str, Any]]:
        return [json.loads(row.payload_json) for row in session.scalars(select(SearchFailure).where(SearchFailure.run_id == run_id).order_by(SearchFailure.id))]

    def list_failures(self, run_id: str) -> list[dict[str, Any]]:
        with self.sessions() as session:
            return self._failure_dicts(session, run_id)

    def list_results(
        self,
        run_id: str | None = None,
        engine: str | None = None,
        limit: int = 100,
        offset: int = 0,
        result_kind: str | None = None,
    ) -> list[dict[str, Any]]:
        with self.sessions() as session:
            statement = select(SearchResult).order_by(SearchResult.id)
            if run_id:
                statement = statement.where(SearchResult.run_id == run_id)
            if engine:
                statement = statement.where(SearchResult.search_engine == engine)
            # Result kind is stored inside the normalized JSON payload for
            # SQLite/PostgreSQL parity. Keep the fallback scan bounded while
            # applying that filter in Python.
            scan_limit = 10_000 if result_kind else max(1, offset + limit)
            statement = statement.limit(scan_limit)
            records = list(session.scalars(statement))
            rows = []
            for record in records:
                payload = json.loads(record.payload_json)
                payload.setdefault("search_engine", record.search_engine)
                rows.append(payload)
            if result_kind:
                rows = [row for row in rows if row.get("result_kind", "organic") == result_kind]
            return rows[max(0, offset) : max(0, offset) + max(0, limit)]

    @staticmethod
    def _parse_date(value: str | None, end: bool = False) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            parsed = datetime.combine(date.fromisoformat(value), datetime.min.time())
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed + (timedelta(days=1) if end and len(value) == 10 else timedelta())

    def _filtered(self, filters: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        filters = filters or {}
        runs = self.list_runs(limit=10000, query=filters.get("query"))
        start, finish = self._parse_date(filters.get("from")), self._parse_date(filters.get("to"), True)
        provider, status, kind, country, search_type = (filters.get(key) for key in ("provider", "status", "result_kind", "country", "search_type"))
        selected = []
        results = []
        for run in runs:
            created = self._parse_date(run["created_at"])
            if (start and created < start) or (finish and created >= finish) or (status and run["status"] != status):
                continue
            options = run.get("options", {})
            if country and str(options.get("country_code", "")).lower() != str(country).lower():
                continue
            if search_type and options.get("search_type") != search_type:
                continue
            selected.append(run)
            for result in self.list_results(run_id=run["id"], engine=provider, limit=10000, result_kind=kind):
                results.append({"run_id": run["id"], **result})
        return selected, results

    def analytics(self, query: str | None = None, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        filters = {**(filters or {}), "query": query or (filters or {}).get("query")}
        runs, results = self._filtered(filters)
        by_status: dict[str, int] = {}
        for run in runs:
            by_status[run["status"]] = by_status.get(run["status"], 0) + 1
        by_engine: dict[str, int] = {}
        for result in results:
            engine = str(result.get("search_engine") or "unknown")
            by_engine[engine] = by_engine.get(engine, 0) + 1
        return {
            "schema_version": 1,
            "scope": {key: value for key, value in filters.items() if value not in (None, "")},
            "semantics": {"run_count": "run-scoped", "result_count": "deduplicated provider-attributed rows", "failure_count": "run-scoped"},
            "run_count": len(runs),
            "result_count": len(results),
            "failure_count": sum(run["failure_count"] for run in runs),
            "runs_by_status": by_status,
            "results_by_engine": by_engine,
        }

    def timeseries(self, filters: dict[str, Any] | None = None, metric: str = "results") -> dict[str, Any]:
        runs, results = self._filtered(filters)
        buckets = defaultdict(lambda: {"searches": 0, "results": 0, "failures": 0})
        for run in runs:
            day = run["created_at"][:10]
            buckets[day]["searches"] += 1
            buckets[day]["failures"] += run["failure_count"]
        for result in results:
            day = next(run["created_at"][:10] for run in runs if run["id"] == result["run_id"])
            buckets[day]["results"] += 1
        keys = sorted(buckets)
        return {"schema_version": 1, "scope": filters or {}, "interval": "day", "metric": metric, "points": [{"date": key, **buckets[key]} for key in keys]}

    def aggregates(self, kind: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        runs, results = self._filtered(filters)
        rows = defaultdict(lambda: {"runs": set(), "results": 0, "failures": 0, "providers": set()})
        for run in runs:
            key = run["query"] if kind == "queries" else None
            if key:
                rows[key]["runs"].add(run["id"])
                rows[key]["failures"] += run["failure_count"]
        for result in results:
            if kind == "providers":
                key = str(result.get("search_engine") or "unknown")
            elif kind == "domains":
                key = urlparse(str(result.get("url") or result.get("link") or "")).netloc.lower() or "unknown"
            else:
                key = next(run["query"] for run in runs if run["id"] == result["run_id"])
            rows[key]["runs"].add(result["run_id"])
            rows[key]["results"] += 1
            rows[key]["providers"].add(result.get("search_engine", "unknown"))
        items = [{"name": key, "run_count": len(value["runs"]), "result_count": value["results"], "failure_count": value["failures"], "provider_count": len(value["providers"])} for key, value in rows.items()]
        items.sort(key=lambda item: (-item["result_count"], item["name"]))
        return {"schema_version": 1, "scope": filters or {}, "items": items[:1000], "total": len(items)}

    def compare(self, left: str, right: str, limit: int = 500) -> dict[str, Any]:
        def keyed(run_id):
            return {str(item.get("url") or item.get("link") or ""): item for item in self.list_results(run_id=run_id, limit=10000) if item.get("url") or item.get("link")}
        a, b = keyed(left), keyed(right)
        shared = sorted(set(a) & set(b))
        added = sorted(set(b) - set(a))
        removed = sorted(set(a) - set(b))
        return {"schema_version": 1, "scope": {"left": left, "right": right}, "left": left, "right": right, "shared": shared[:limit], "added": added[:limit], "removed": removed[:limit], "totals": {"shared": len(shared), "added": len(added), "removed": len(removed)}}

    def export(self, filters: dict[str, Any] | None = None, fmt: str = "json") -> tuple[str, str]:
        runs, results = self._filtered(filters)
        rows = [{"run_id": r["run_id"], "query": next(x["query"] for x in runs if x["id"] == r["run_id"]), "provider": r.get("search_engine"), "url": r.get("url") or r.get("link"), "result_kind": r.get("result_kind", "organic")} for r in results[:5000]]
        if fmt == "csv":
            stream = io.StringIO()
            fieldnames = list(rows[0]) if rows else ["run_id", "query", "provider", "url", "result_kind"]
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            return stream.getvalue(), "text/csv"
        return json.dumps({"schema_version": 1, "scope": filters or {}, "rows": rows}, ensure_ascii=False), "application/json"
