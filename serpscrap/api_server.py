"""Small dependency-light HTTP API for the Phase 8 containers."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from serpscrap.api_service import SearchJobService
from serpscrap.models import SearchRequest


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, default=str).encode("utf-8")


class ApiHandler(BaseHTTPRequestHandler):
    service: SearchJobService

    def _send(self, status: int, payload: Any) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", os.getenv("CORS_ORIGIN", "*"))
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(HTTPStatus.NO_CONTENT, {})

    def _read_payload(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(payload, dict):
            raise ValueError("request body must be an object")
        return payload

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = parse_qs(parsed.query)
        if path == "/healthz":
            return self._send(HTTPStatus.OK, {"status": "ok"})
        if path == "/readyz":
            readiness = self.service.readiness()
            return self._send(
                HTTPStatus.OK if readiness["status"] == "ready" else HTTPStatus.SERVICE_UNAVAILABLE,
                readiness,
            )
        if path == "/api/v1/engines":
            return self._send(HTTPStatus.OK, {"engines": self.service.configuration.engines()})
        if path == "/api/v1/configuration":
            return self._send(HTTPStatus.OK, self.service.configuration.get())
        if path == "/api/v1/results":
            limit = min(max(int((query.get("limit") or [100])[0]), 0), 1000)
            offset = max(int((query.get("offset") or [0])[0]), 0)
            return self._send(
                HTTPStatus.OK,
                {"results": self.service.store.list_results(
                    run_id=(query.get("run_id") or [None])[0],
                    engine=(query.get("engine") or [None])[0],
                    limit=limit,
                    offset=offset,
                    result_kind=(query.get("kind") or [None])[0],
                )},
            )
        if path == "/api/v1/history/searches":
            return self._send(
                HTTPStatus.OK,
                {"searches": self.service.store.list_runs(
                    limit=min(int((query.get("limit") or [50])[0]), 1000),
                    query=(query.get("query") or [None])[0],
                )},
            )
        if path == "/api/v1/history/analytics":
            return self._send(HTTPStatus.OK, self.service.store.analytics((query.get("query") or [None])[0]))
        prefix = "/api/v1/searches/"
        if path.startswith(prefix):
            remainder = path[len(prefix):]
            run_id, _, suffix = remainder.partition("/")
            if suffix == "events":
                events = self.service.events(run_id)
                return self._send(HTTPStatus.OK if events else HTTPStatus.NOT_FOUND, {"events": events})
            if suffix == "failures":
                return self._send(HTTPStatus.OK, {"failures": self.service.store.list_failures(run_id)})
            status = self.service.status(run_id)
            return self._send(HTTPStatus.OK if status else HTTPStatus.NOT_FOUND, status or {"error": "not found"})
        return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.rstrip("/")
        if path == "/api/v1/configuration/reset":
            return self._send(HTTPStatus.OK, self.service.configuration.reset())
        if path != "/api/v1/searches":
            return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
        try:
            payload = self._read_payload()
            queries = payload.get("queries") or payload.get("query")
            options, configuration = self.service.resolve_options(payload.get("options") or {})
            request = SearchRequest.create(queries, options)
            run_id = self.service.submit(request, configuration)
        except Exception as exc:
            status = HTTPStatus.SERVICE_UNAVAILABLE if "capacity" in str(exc) or "shutting down" in str(exc) else HTTPStatus.BAD_REQUEST
            return self._send(status, {"error": str(exc)})
        return self._send(
            HTTPStatus.ACCEPTED,
            {
                "id": run_id,
                "status": "queued",
                "search_engines": options["search_engines"],
                "configuration_revision": configuration["revision"],
            },
        )

    def do_PUT(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/api/v1/configuration":
            return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
        try:
            return self._send(HTTPStatus.OK, self.service.configuration.save(self._read_payload()))
        except Exception as exc:
            return self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def do_DELETE(self) -> None:  # noqa: N802
        path = self.path.rstrip("/")
        if path == "/api/v1/history/searches":
            return self._send(HTTPStatus.OK, {"deleted": self.service.store.delete_all_runs()})
        prefix = "/api/v1/searches/"
        if path.startswith(prefix):
            run_id = path[len(prefix):].split("/", 1)[0]
            if self.service.store.delete_run(run_id):
                return self._send(HTTPStatus.OK, {"id": run_id, "deleted": True})
            return self._send(HTTPStatus.NOT_FOUND, {"error": "search not found"})
        return self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def log_message(self, format: str, *args: Any) -> None:
        return


def serve(host: str | None = None, port: int | None = None, service: SearchJobService | None = None) -> None:
    configured_service = service or SearchJobService()
    handler = type("ConfiguredApiHandler", (ApiHandler,), {"service": configured_service})
    server = ThreadingHTTPServer(
        (host or os.getenv("API_HOST", "0.0.0.0"), port or int(os.getenv("API_PORT", "8000"))),
        handler,
    )
    server.daemon_threads = True
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        configured_service.close()


if __name__ == "__main__":
    serve()
