"""Minimal MCP-compatible JSON-RPC gateway backed by the application API."""

from __future__ import annotations

import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlencode


TOOLS = [
    {"name": "start_search", "description": "Start a SerpScrap search.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "get_search_status", "description": "Get the status of a search job.", "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
    {"name": "list_results", "description": "List normalized search results.", "inputSchema": {"type": "object", "properties": {"run_id": {"type": "string"}}}},
    {"name": "list_search_history", "description": "List historical search runs.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "analyze_history", "description": "Analyze historical search results.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "list_engines", "description": "List registry-backed search engines.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "get_configuration", "description": "Get the effective search configuration.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "update_configuration", "description": "Persist a validated search configuration.", "inputSchema": {"type": "object", "properties": {"search_engines": {"type": "array", "items": {"type": "string"}}}, "required": ["search_engines"]}},
    {"name": "reset_configuration", "description": "Reset the persisted configuration to defaults.", "inputSchema": {"type": "object", "properties": {}}},
]


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


def call_tool(name: str, arguments: dict[str, Any]) -> Any:
    if name == "start_search":
        return _api_request("/searches", arguments)
    if name == "get_search_status":
        return _api_request(f"/searches/{arguments['id']}")
    if name == "list_results":
        query = "?" + urlencode({"run_id": arguments["run_id"]}) if arguments.get("run_id") else ""
        return _api_request(f"/results{query}")
    if name == "list_search_history":
        return _api_request("/history/searches")
    if name == "analyze_history":
        return _api_request("/history/analytics")
    if name == "list_engines":
        return _api_request("/engines")
    if name == "get_configuration":
        return _api_request("/configuration")
    if name == "update_configuration":
        return _api_request("/configuration", arguments, method="PUT")
    if name == "reset_configuration":
        return _api_request("/configuration/reset", {}, method="POST")
    raise ValueError(f"Unknown tool: {name}")


class McpHandler(BaseHTTPRequestHandler):
    def _send(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/healthz":
            return self._send({"status": "ok"})
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length) or b"{}")
            method = request.get("method")
            if method == "initialize":
                result = {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "serpscrap-mcp", "version": "1.0"}}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                params = request.get("params") or {}
                result = {"content": [{"type": "text", "text": json.dumps(call_tool(params["name"], params.get("arguments") or {}), ensure_ascii=False)}]}
            else:
                raise ValueError(f"Unsupported method: {method}")
            return self._send({"jsonrpc": "2.0", "id": request.get("id"), "result": result})
        except Exception as exc:
            return self._send({"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(exc)}})

    def log_message(self, format: str, *args: Any) -> None:
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(
        (os.getenv("MCP_HOST", "0.0.0.0"), int(os.getenv("MCP_PORT", "8001"))),
        McpHandler,
    )
    server.serve_forever()
