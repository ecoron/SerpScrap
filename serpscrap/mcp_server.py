"""MCP-compatible JSON-RPC gateway backed by the application API.

The gateway deliberately keeps the MCP surface small. Search content is
returned as inert data, while configuration tools are explicitly marked as
state-changing operations and may be protected with ``MCP_AUTH_TOKEN``.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _load_dotenv(path: str | Path = ".env") -> None:
    """Load simple KEY=VALUE entries without overriding real environment vars."""
    dotenv_path = Path(path)
    if not dotenv_path.is_file():
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        name, separator, value = line.partition("=")
        name = name.strip()
        if not separator or not _ENV_NAME.fullmatch(name):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(name, value)


_load_dotenv()

SCHEMA_VERSION = "1.0"
MAX_OUTPUT_BYTES = int(os.getenv("MCP_MAX_OUTPUT_BYTES", "100000"))
MAX_TEXT_LENGTH = 4000


def _string_schema(description: str, *, max_length: int = 500) -> dict[str, Any]:
    return {"type": "string", "description": description, "minLength": 1, "maxLength": max_length}


_SEARCH_OPTIONS_SCHEMA = {
    "type": "object",
    "description": "Optional bounded search settings.",
    "properties": {
        "search_engines": {
            "type": "array",
            "description": "Engine IDs to use for this search.",
            "items": _string_schema("Registered search-engine ID.", max_length=80),
            "minItems": 1,
            "maxItems": 32,
            "uniqueItems": True,
        },
        "country_code": {
            "type": "string",
            "description": "Two-letter country code such as DE.",
            "pattern": "^[A-Za-z]{2}$",
        },
        "num_pages_for_keyword": {
            "type": "integer",
            "description": "Number of result pages per query.",
            "minimum": 1,
            "maximum": 10,
        },
        "num_results_per_page": {
            "type": "integer",
            "description": "Maximum results requested per page.",
            "minimum": 1,
            "maximum": 100,
        },
        "consent_action": {
            "type": "string",
            "description": "Consent action for this search; accept is an explicit diagnostic mode.",
            "enum": ["necessary", "reject", "accept", "disabled"],
        },
    },
    "additionalProperties": False,
}


TOOLS = [
    {
        "name": "start_search",
        "description": "Start an asynchronous SerpScrap search. Returns a job ID; poll get_search_status, then read list_results.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": _string_schema("Search query to submit.", max_length=1000),
                "options": _SEARCH_OPTIONS_SCHEMA,
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True},
    },
    {
        "name": "get_search_status",
        "description": "Read bounded progress, terminal state, failures, and result count for a search job.",
        "inputSchema": {"type": "object", "properties": {"id": _string_schema("Search job ID.", max_length=128)}, "required": ["id"], "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "list_results",
        "description": "Read normalized, provenance-preserving search results with deterministic offset/limit pagination.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _string_schema("Optional search job ID.", max_length=128),
                "offset": {"type": "integer", "description": "Zero-based result offset.", "minimum": 0, "maximum": 100000},
                "limit": {"type": "integer", "description": "Number of results to return.", "minimum": 1, "maximum": 1000},
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "list_search_history",
        "description": "Read persisted search-run summaries, optionally filtered and bounded by limit.",
        "inputSchema": {"type": "object", "properties": {"query": _string_schema("Optional query filter.", max_length=1000), "limit": {"type": "integer", "minimum": 1, "maximum": 1000}}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "analyze_history",
        "description": "Read aggregate analytics for persisted search history.",
        "inputSchema": {"type": "object", "properties": {"query": _string_schema("Optional query filter.", max_length=1000)}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "list_engines",
        "description": "Read registry metadata, capabilities, readiness, and browser contracts for search engines.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "get_configuration",
        "description": "Read the effective persisted/default search configuration. Does not modify state.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "update_configuration",
        "description": "Persist a validated search-engine configuration. This changes shared state and requires explicit approval.",
        "inputSchema": {
            "type": "object",
            "properties": {"search_engines": {"type": "array", "description": "Non-empty registered engine IDs.", "items": _string_schema("Registered search-engine ID.", max_length=80), "minItems": 1, "maxItems": 32, "uniqueItems": True}},
            "required": ["search_engines"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "reset_configuration",
        "description": "Reset shared search configuration to defaults. This changes state and requires explicit approval.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    },
]

_TOOL_NAMES = {tool["name"] for tool in TOOLS}
_MUTATING_TOOLS = {"update_configuration", "reset_configuration"}


def _api_request(path: str, payload: dict[str, Any] | None = None, method: str | None = None) -> Any:
    base = os.getenv("SERPSCRAP_API_URL", "http://serpscrap-app:8000/api/v1").rstrip("/")
    body = None
    headers = {"Accept": "application/json"}
    method = method or ("POST" if payload is not None else "GET")
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(base + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def _validate_arguments(name: str, arguments: dict[str, Any]) -> None:
    if name not in _TOOL_NAMES:
        raise ValueError(f"unknown tool: {name}")
    if not isinstance(arguments, dict):
        raise ValueError("tool arguments must be an object")
    allowed_options: dict[str, set[str]] = {
        "start_search": {"query", "options"}, "get_search_status": {"id"},
        "list_results": {"run_id", "offset", "limit"}, "list_search_history": {"query", "limit"},
        "analyze_history": {"query"}, "list_engines": set(), "get_configuration": set(),
        "update_configuration": {"search_engines"}, "reset_configuration": set(),
    }
    allowed = allowed_options[name]
    unknown = set(arguments) - allowed
    if unknown:
        raise ValueError(f"unsupported arguments for {name}: {sorted(unknown)}")
    required_options: dict[str, set[str]] = {
        "start_search": {"query"},
        "get_search_status": {"id"},
        "update_configuration": {"search_engines"},
    }
    required = required_options.get(name, set())
    missing = required - set(arguments)
    if missing:
        raise ValueError(f"missing required arguments for {name}: {sorted(missing)}")
    for field in ("query", "id", "run_id"):
        if field in arguments and (not isinstance(arguments[field], str) or not arguments[field].strip() or len(arguments[field]) > (1000 if field == "query" else 128)):
            raise ValueError(f"{field} must be a non-empty bounded string")
    for field in ("offset", "limit"):
        if field in arguments and (not isinstance(arguments[field], int) or isinstance(arguments[field], bool) or arguments[field] < (0 if field == "offset" else 1) or arguments[field] > (100000 if field == "offset" else 1000)):
            raise ValueError(f"{field} is outside its allowed range")
    if "search_engines" in arguments:
        engines = arguments["search_engines"]
        if not isinstance(engines, list) or not engines or len(engines) > 32 or len(set(engines)) != len(engines) or any(not isinstance(engine, str) or not engine.strip() for engine in engines):
            raise ValueError("search_engines must be a non-empty list of unique IDs")
    if "options" in arguments and not isinstance(arguments["options"], dict):
        raise ValueError("options must be an object")


def call_tool(name: str, arguments: dict[str, Any]) -> Any:
    _validate_arguments(name, arguments)
    if name == "start_search":
        return _api_request("/searches", arguments)
    if name == "get_search_status":
        return _api_request(f"/searches/{arguments['id']}")
    if name == "list_results":
        params = {key: arguments[key] for key in ("run_id", "offset", "limit") if key in arguments}
        return _api_request("/results?" + urlencode(params) if params else "/results")
    if name == "list_search_history":
        params = {key: arguments[key] for key in ("query", "limit") if key in arguments}
        return _api_request("/history/searches?" + urlencode(params) if params else "/history/searches")
    if name == "analyze_history":
        query = ("?" + urlencode({"query": arguments["query"]})) if arguments.get("query") else ""
        return _api_request(f"/history/analytics{query}")
    if name == "list_engines":
        return _api_request("/engines")
    if name == "get_configuration":
        return _api_request("/configuration")
    if name == "update_configuration":
        return _api_request("/configuration", arguments, method="PUT")
    if name == "reset_configuration":
        return _api_request("/configuration/reset", {}, method="POST")
    raise ValueError(f"unknown tool: {name}")


def _bound(value: Any, depth: int = 0) -> Any:
    """Bound untrusted provider data before exposing it through MCP."""
    if depth > 8:
        return "[truncated]"
    if isinstance(value, str):
        return value[:MAX_TEXT_LENGTH] + ("…" if len(value) > MAX_TEXT_LENGTH else "")
    if isinstance(value, list):
        return [_bound(item, depth + 1) for item in value[:1000]]
    if isinstance(value, dict):
        return {str(key)[:200]: _bound(item, depth + 1) for key, item in list(value.items())[:200]}
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:MAX_TEXT_LENGTH]


def _structured_result(value: Any) -> dict[str, Any]:
    data = _bound(value)
    envelope = {"schema_version": SCHEMA_VERSION, "data": data}
    encoded = json.dumps(envelope, ensure_ascii=False)
    if len(encoded.encode("utf-8")) > MAX_OUTPUT_BYTES:
        envelope["data"] = {"truncated": True, "message": "MCP output exceeded the configured size limit."}
    return envelope


def _content_result(value: Any) -> dict[str, Any]:
    structured = _structured_result(value)
    text = json.dumps(structured["data"], ensure_ascii=False)
    return {"content": [{"type": "text", "text": text}], "structuredContent": structured}


class McpHandler(BaseHTTPRequestHandler):
    def _authorized(self) -> bool:
        configured = os.getenv("MCP_AUTH_TOKEN")
        if not configured:
            return True
        supplied = self.headers.get("Authorization", "")
        return secrets.compare_digest(supplied, f"Bearer {configured}")

    def _send(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/healthz":
            return self._send({"status": "ok", "schema_version": SCHEMA_VERSION})
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        request_id: Any = None
        try:
            if not self._authorized():
                return self._send({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32001, "message": "authentication required"}}, 401)
            length = int(self.headers.get("Content-Length", "0"))
            if length > MAX_OUTPUT_BYTES:
                raise ValueError("request body exceeds configured size limit")
            request = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(request, dict):
                raise ValueError("JSON-RPC request must be an object")
            request_id = request.get("id")
            method = request.get("method")
            result: Any
            if method == "initialize":
                result = {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "serpscrap-mcp", "version": SCHEMA_VERSION}}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                params = request.get("params") or {}
                if not isinstance(params, dict) or not isinstance(params.get("name"), str):
                    raise ValueError("tools/call requires a tool name")
                result = _content_result(call_tool(params["name"], params.get("arguments") or {}))
            else:
                raise ValueError(f"unsupported method: {method}")
            return self._send({"jsonrpc": "2.0", "id": request_id, "result": result})
        except ValueError as exc:
            return self._send({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": str(exc)}})
        except Exception as exc:
            return self._send({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": "MCP backend request failed", "data": {"type": type(exc).__name__}}})

    def log_message(self, format: str, *args: Any) -> None:
        return


def _validate_bind_security(host: str) -> None:
    loopback = host in {"127.0.0.1", "localhost", "::1"}
    if not loopback and not os.getenv("MCP_AUTH_TOKEN") and os.getenv("MCP_ALLOW_INSECURE_REMOTE") != "1":
        raise RuntimeError("MCP_AUTH_TOKEN is required for non-loopback MCP_HOST; set MCP_ALLOW_INSECURE_REMOTE=1 only for explicit local-network development")


if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "0.0.0.0")
    _validate_bind_security(host)
    server = ThreadingHTTPServer((host, int(os.getenv("MCP_PORT", "8001"))), McpHandler)
    server.serve_forever()
