"""MCP-compatible JSON-RPC gateway backed by the application API.

The gateway deliberately keeps the MCP surface small. Search content is
returned as inert data, while configuration tools are explicitly marked as
state-changing operations and may be protected with ``MCP_AUTH_TOKEN``.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import secrets
import urllib.request
from difflib import SequenceMatcher
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from serpscrap.config import Config
from serpscrap.topic_service import TopicService
from serpscrap.topics import TopicRequest, canonical_url

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
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    },
    {
        "name": "get_search_status",
        "description": "Read bounded progress, terminal state, failures, and result count for a search job.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": _string_schema("Search job ID.", max_length=128)},
            "required": ["id"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "list_results",
        "description": "Read normalized, provenance-preserving search results with deterministic offset/limit pagination.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": _string_schema("Optional search job ID.", max_length=128),
                "offset": {
                    "type": "integer",
                    "description": "Zero-based result offset.",
                    "minimum": 0,
                    "maximum": 100000,
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return.",
                    "minimum": 1,
                    "maximum": 1000,
                },
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "list_search_history",
        "description": "Read persisted search-run summaries, optionally filtered and bounded by limit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": _string_schema("Optional query filter.", max_length=1000),
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000},
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "analyze_history",
        "description": "Read aggregate analytics for persisted search history.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": _string_schema("Optional query filter.", max_length=1000)},
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "analyze_url_statistics",
        "description": "Read URL or domain statistics across all persisted searches, independent of search query.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scope": {"type": "string", "enum": ["domains", "urls"]},
                "domain": _string_schema("Optional domain filter.", max_length=253),
                "include_findings": {
                    "type": "boolean",
                    "description": "Include individual finding details.",
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000},
                "offset": {"type": "integer", "minimum": 0, "maximum": 100000},
            },
            "additionalProperties": False,
        },
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
            "properties": {
                "search_engines": {
                    "type": "array",
                    "description": "Non-empty registered engine IDs.",
                    "items": _string_schema("Registered search-engine ID.", max_length=80),
                    "minItems": 1,
                    "maxItems": 32,
                    "uniqueItems": True,
                }
            },
            "required": ["search_engines"],
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "reset_configuration",
        "description": "Reset shared search configuration to defaults. This changes state and requires explicit approval.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "list_topics",
        "description": "List registered thematic sources and their capabilities.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "topic_search",
        "description": "Run a bounded thematic search through the shared TopicService.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "enum": ["news", "shopping"]},
                "query": _string_schema("Topic query.", max_length=1000),
                "sources": {
                    "type": "array",
                    "items": _string_schema("Source ID or feed URL.", max_length=500),
                    "maxItems": 16,
                    "uniqueItems": True,
                },
                "country": {"type": "string", "pattern": "^[A-Za-z]{2}$"},
                "language": {"type": "string", "pattern": "^[A-Za-z][A-Za-z-]{1,15}$"},
                "since": {"type": "string", "maxLength": 40},
                "until": {"type": "string", "maxLength": 40},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    },
    {
        "name": "get_topic_capabilities",
        "description": "Read capabilities and supported filters for one registered topic.",
        "inputSchema": {
            "type": "object",
            "properties": {"topic": {"type": "string", "enum": ["news", "shopping"]}},
            "required": ["topic"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "list_topic_sources",
        "description": "List registered sources for an optional topic, including capabilities and readiness.",
        "inputSchema": {
            "type": "object",
            "properties": {"topic": {"type": "string", "enum": ["news", "shopping"]}},
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False},
    },
    {
        "name": "search_news",
        "description": "Run a news-focused search with source, locale, and time-window filters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": _string_schema("News query.", max_length=1000),
                "sources": {"type": "array", "items": _string_schema("News source ID or feed URL.", max_length=500), "maxItems": 16, "uniqueItems": True},
                "country": {"type": "string", "pattern": "^[A-Za-z]{2}$"},
                "language": {"type": "string", "pattern": "^[A-Za-z][A-Za-z-]{1,15}$"},
                "since": {"type": "string", "maxLength": 40},
                "until": {"type": "string", "maxLength": 40},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True},
    },
    {
        "name": "group_news_events",
        "description": "Search news and group near-identical headlines into source-aware events.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": _string_schema("News query.", max_length=1000),
                "sources": {"type": "array", "items": _string_schema("News source ID or feed URL.", max_length=500), "maxItems": 16, "uniqueItems": True},
                "country": {"type": "string", "pattern": "^[A-Za-z]{2}$"},
                "language": {"type": "string", "pattern": "^[A-Za-z][A-Za-z-]{1,15}$"},
                "since": {"type": "string", "maxLength": 40},
                "until": {"type": "string", "maxLength": 40},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True},
    },
    {
        "name": "search_products",
        "description": "Run a shopping-focused product search with source and marketplace filters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": _string_schema("Product query.", max_length=1000),
                "sources": {"type": "array", "items": _string_schema("Shopping source ID.", max_length=80), "maxItems": 16, "uniqueItems": True},
                "country": {"type": "string", "pattern": "^[A-Za-z]{2}$"},
                "language": {"type": "string", "pattern": "^[A-Za-z][A-Za-z-]{1,15}$"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True},
    },
    {
        "name": "compare_product_prices",
        "description": "Search products and group comparable offers with normalized price information.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": _string_schema("Product query.", max_length=1000),
                "sources": {"type": "array", "items": _string_schema("Shopping source ID.", max_length=80), "maxItems": 16, "uniqueItems": True},
                "country": {"type": "string", "pattern": "^[A-Za-z]{2}$"},
                "language": {"type": "string", "pattern": "^[A-Za-z][A-Za-z-]{1,15}$"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True},
    },
]

_TOPIC_FILTER_PROPERTIES = {
    "sources": {"type": "array", "items": _string_schema("Topic source ID or URL.", max_length=500), "maxItems": 16, "uniqueItems": True},
    "country": {"type": "string", "pattern": "^[A-Za-z]{2}$"},
    "language": {"type": "string", "pattern": "^[A-Za-z][A-Za-z-]{1,15}$"},
    "since": {"type": "string", "maxLength": 40},
    "until": {"type": "string", "maxLength": 40},
}


def _topic_analysis_tool(name: str, description: str, *, topic: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    filters = _TOPIC_FILTER_PROPERTIES.copy()
    if topic == "shopping":
        filters.pop("since")
        filters.pop("until")
    properties = {"query": _string_schema("Topic query.", max_length=1000), **filters, **(extra or {})}
    return {
        "name": name,
        "description": description,
        "inputSchema": {"type": "object", "properties": properties, "required": ["query"], "additionalProperties": False},
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True},
    }


TOOLS.extend([
    {"name": "validate_topic_query", "description": "Validate a topic query and filters without fetching sources.", "inputSchema": {"type": "object", "properties": {"topic": {"type": "string", "enum": ["news", "shopping"]}, "query": _string_schema("Topic query.", max_length=1000), **_TOPIC_FILTER_PROPERTIES}, "required": ["topic", "query"], "additionalProperties": False}, "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}},
    {"name": "compare_topic_results", "description": "Compare two bounded topic result lists by canonical URL.", "inputSchema": {"type": "object", "properties": {"left": {"type": "array", "maxItems": 1000, "items": {"type": "object"}}, "right": {"type": "array", "maxItems": 1000, "items": {"type": "object"}}}, "required": ["left", "right"], "additionalProperties": False}, "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}},
    {"name": "export_topic_results", "description": "Export a bounded topic result list as JSON or CSV text.", "inputSchema": {"type": "object", "properties": {"results": {"type": "array", "maxItems": 1000, "items": {"type": "object"}}, "format": {"type": "string", "enum": ["json", "csv"]}}, "required": ["results"], "additionalProperties": False}, "annotations": {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}},
    _topic_analysis_tool("compare_news_sources", "Search news and compare result counts and headlines by source.", topic="news"),
    _topic_analysis_tool("track_news_topic", "Run a bounded news tracking snapshot for a topic and return source-aware results.", topic="news"),
    _topic_analysis_tool("get_news_trends", "Search news and summarize publication volume by source and day.", topic="news"),
    _topic_analysis_tool("filter_products", "Search products and filter offers by price and availability.", topic="shopping", extra={"max_price": {"type": "number", "minimum": 0}, "availability": {"type": "string", "maxLength": 40}}),
    _topic_analysis_tool("track_product_price", "Run a bounded product price snapshot across selected sources.", topic="shopping"),
    _topic_analysis_tool("find_product_alternatives", "Search products and return alternative offers grouped by normalized product identity.", topic="shopping"),
])

_TOOL_NAMES = {tool["name"] for tool in TOOLS}
_MUTATING_TOOLS = {"update_configuration", "reset_configuration"}
_TOPIC_SERVICE = TopicService(config=Config().get())


def _api_request(
    path: str, payload: dict[str, Any] | None = None, method: str | None = None
) -> Any:
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
        "start_search": {"query", "options"},
        "get_search_status": {"id"},
        "list_results": {"run_id", "offset", "limit"},
        "list_search_history": {"query", "limit"},
        "analyze_history": {"query"},
        "analyze_url_statistics": {"scope", "domain", "include_findings", "limit", "offset"},
        "list_engines": set(),
        "get_configuration": set(),
        "update_configuration": {"search_engines"},
        "reset_configuration": set(),
        "list_topics": set(),
        "topic_search": {"topic", "query", "sources", "country", "language", "since", "until"},
        "get_topic_capabilities": {"topic"},
        "list_topic_sources": {"topic"},
        "search_news": {"query", "sources", "country", "language", "since", "until"},
        "group_news_events": {"query", "sources", "country", "language", "since", "until"},
        "search_products": {"query", "sources", "country", "language"},
        "compare_product_prices": {"query", "sources", "country", "language"},
        "validate_topic_query": {"topic", "query", "sources", "country", "language", "since", "until"},
        "compare_topic_results": {"left", "right"},
        "export_topic_results": {"results", "format"},
        "compare_news_sources": {"query", "sources", "country", "language", "since", "until"},
        "track_news_topic": {"query", "sources", "country", "language", "since", "until"},
        "get_news_trends": {"query", "sources", "country", "language", "since", "until"},
        "filter_products": {"query", "sources", "country", "language", "max_price", "availability"},
        "track_product_price": {"query", "sources", "country", "language"},
        "find_product_alternatives": {"query", "sources", "country", "language"},
    }
    allowed = allowed_options[name]
    unknown = set(arguments) - allowed
    if unknown:
        raise ValueError(f"unsupported arguments for {name}: {sorted(unknown)}")
    required_options: dict[str, set[str]] = {
        "start_search": {"query"},
        "get_search_status": {"id"},
        "update_configuration": {"search_engines"},
        "topic_search": {"query"},
        "get_topic_capabilities": {"topic"},
        "search_news": {"query"},
        "group_news_events": {"query"},
        "search_products": {"query"},
        "compare_product_prices": {"query"},
        "validate_topic_query": {"topic", "query"},
        "compare_topic_results": {"left", "right"},
        "export_topic_results": {"results"},
        "compare_news_sources": {"query"},
        "track_news_topic": {"query"},
        "get_news_trends": {"query"},
        "filter_products": {"query"},
        "track_product_price": {"query"},
        "find_product_alternatives": {"query"},
    }
    required = required_options.get(name, set())
    missing = required - set(arguments)
    if missing:
        raise ValueError(f"missing required arguments for {name}: {sorted(missing)}")
    for field in ("query", "id", "run_id", "domain"):
        if field in arguments and (
            not isinstance(arguments[field], str)
            or not arguments[field].strip()
            or len(arguments[field]) > (1000 if field == "query" else 128)
        ):
            raise ValueError(f"{field} must be a non-empty bounded string")
    if "scope" in arguments and arguments["scope"] not in {"domains", "urls"}:
        raise ValueError("scope must be domains or urls")
    for field in ("offset", "limit"):
        if field in arguments and (
            not isinstance(arguments[field], int)
            or isinstance(arguments[field], bool)
            or arguments[field] < (0 if field == "offset" else 1)
            or arguments[field] > (100000 if field == "offset" else 1000)
        ):
            raise ValueError(f"{field} is outside its allowed range")
    if "search_engines" in arguments:
        engines = arguments["search_engines"]
        if (
            not isinstance(engines, list)
            or not engines
            or len(engines) > 32
            or len(set(engines)) != len(engines)
            or any(not isinstance(engine, str) or not engine.strip() for engine in engines)
        ):
            raise ValueError("search_engines must be a non-empty list of unique IDs")
    if "options" in arguments and not isinstance(arguments["options"], dict):
        raise ValueError("options must be an object")
    for field in ("left", "right", "results"):
        if field in arguments and (
            not isinstance(arguments[field], list)
            or len(arguments[field]) > 1000
            or any(not isinstance(item, dict) for item in arguments[field])
        ):
            raise ValueError(f"{field} must be a bounded list")
    if "format" in arguments and arguments["format"] not in {"json", "csv"}:
        raise ValueError("format must be json or csv")
    if "max_price" in arguments and (not isinstance(arguments["max_price"], (int, float)) or isinstance(arguments["max_price"], bool) or arguments["max_price"] < 0):
        raise ValueError("max_price must be a non-negative number")
    if "availability" in arguments and (not isinstance(arguments["availability"], str) or not arguments["availability"].strip() or len(arguments["availability"]) > 40):
        raise ValueError("availability must be a bounded string")
    if "topic" in arguments and arguments["topic"] not in {"news", "shopping"}:
        raise ValueError("unsupported topic")
    if "sources" in arguments:
        sources = arguments["sources"]
        if (not isinstance(sources, list) or len(sources) > 16 or len(set(sources)) != len(sources)
                or any(not isinstance(source, str) or not source.strip() or len(source) > 500 for source in sources)):
            raise ValueError("sources must be a bounded list of unique strings")
    for field in ("country", "language", "since", "until"):
        if field in arguments and (not isinstance(arguments[field], str) or not arguments[field].strip() or len(arguments[field]) > 40):
            raise ValueError(f"{field} must be a bounded string")


def _execute_topic_request(topic: str, arguments: dict[str, Any]) -> dict[str, Any]:
    request = TopicRequest.create(
        arguments["query"],
        topic=topic,
        sources=arguments.get("sources") or (),
        country=arguments.get("country"),
        language=arguments.get("language"),
        since=arguments.get("since"),
        until=arguments.get("until"),
    )
    return _TOPIC_SERVICE.execute(request).to_dict()


def _headline_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (value or "").lower()).strip()


def _group_news_events(report: dict[str, Any]) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    for result in report.get("results", [])[:1000]:
        title = result.get("title") or result.get("snippet") or ""
        key = _headline_key(title)
        group = next(
            (item for item in groups if SequenceMatcher(None, key, item["_key"]).ratio() >= 0.72),
            None,
        )
        if group is None:
            group = {"event_id": f"event-{len(groups) + 1}", "headline": title, "sources": [], "articles": [], "_key": key}
            groups.append(group)
        group["articles"].append(result)
        source = result.get("source")
        if source and source not in group["sources"]:
            group["sources"].append(source)
    for group in groups:
        group.pop("_key", None)
        group["article_count"] = len(group["articles"])
    return {**report, "events": groups, "results": []}


def _price_value(result: dict[str, Any]) -> float | None:
    value = result.get("price_value") or result.get("price")
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    match = re.search(r"\d[\d.\s]*[,\.]\d{2}|\d+", value)
    if not match:
        return None
    raw = match.group(0).replace(" ", "")
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def _product_key(result: dict[str, Any]) -> str:
    for field in ("gtin", "product_id", "model_number"):
        if result.get(field):
            return f"{field}:{str(result[field]).strip().lower()}"
    title = _headline_key(result.get("title"))
    return f"title:{title}" if title else f"url:{result.get('canonical_url') or result.get('url', '')}"


def _compare_product_prices(report: dict[str, Any]) -> dict[str, Any]:
    products: dict[str, dict[str, Any]] = {}
    for result in report.get("results", [])[:1000]:
        key = _product_key(result)
        product = products.setdefault(key, {"product_id": key, "title": result.get("title"), "offers": []})
        offer = {**result, "price_value": _price_value(result)}
        product["offers"].append(offer)
    items = list(products.values())
    for item in items:
        priced = [offer["price_value"] for offer in item["offers"] if offer["price_value"] is not None]
        item["lowest_price"] = min(priced) if priced else None
        item["offer_count"] = len(item["offers"])
        item["offers"].sort(key=lambda offer: (offer["price_value"] is None, offer["price_value"] or 0, offer.get("source") or ""))
    items.sort(key=lambda item: (item["lowest_price"] is None, item["lowest_price"] or 0, item["title"] or ""))
    return {**report, "products": items, "results": []}


def _compare_topic_results(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> dict[str, Any]:
    def keyed(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {
            canonical_url(str(row.get("canonical_url") or row.get("url") or row.get("raw_url"))): row
            for row in rows
            if row.get("canonical_url") or row.get("url") or row.get("raw_url")
        }
    before, after = keyed(left), keyed(right)
    shared = sorted(set(before) & set(after))
    return {"schema_version": 1, "stable": [{"identity": key, "left": before[key], "right": after[key]} for key in shared], "added": [after[key] for key in sorted(set(after) - set(before))], "removed": [before[key] for key in sorted(set(before) - set(after))], "totals": {"stable": len(shared), "added": len(set(after) - set(before)), "removed": len(set(before) - set(after))}}


def _export_topic_results(rows: list[dict[str, Any]], fmt: str = "json") -> dict[str, Any]:
    if fmt == "json":
        return {"format": "json", "content": json.dumps(rows, ensure_ascii=False)}
    keys = sorted({key for row in rows for key in row})
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=keys, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return {"format": "csv", "content": stream.getvalue()}


def call_tool(name: str, arguments: dict[str, Any]) -> Any:
    _validate_arguments(name, arguments)
    if name == "start_search":
        return _api_request("/searches", arguments)
    if name == "list_topics":
        return {"topics": _TOPIC_SERVICE.registry.metadata()}
    if name == "validate_topic_query":
        TopicRequest.create(arguments["query"], topic=arguments["topic"], sources=arguments.get("sources") or (), country=arguments.get("country"), language=arguments.get("language"), since=arguments.get("since"), until=arguments.get("until"))
        return {"valid": True, "topic": arguments["topic"], "query": arguments["query"], "filters": {key: arguments[key] for key in arguments if key not in {"topic", "query"}}}
    if name == "compare_topic_results":
        return _compare_topic_results(arguments["left"], arguments["right"])
    if name == "export_topic_results":
        return _export_topic_results(arguments["results"], arguments.get("format", "json"))
    if name == "get_topic_capabilities":
        matches = [item for item in _TOPIC_SERVICE.registry.metadata() if item["topic_id"] == arguments["topic"]]
        if not matches:
            raise ValueError(f"unknown topic: {arguments['topic']}")
        return {
            "topic_id": arguments["topic"],
            "display_name": matches[0]["display_name"],
            "source_count": len(matches),
            "readiness": sorted({item["readiness"] for item in matches}),
            "sources": matches,
        }
    if name == "list_topic_sources":
        topic = arguments.get("topic")
        sources = [item for item in _TOPIC_SERVICE.registry.metadata() if not topic or item["topic_id"] == topic]
        return {"topic": topic, "sources": sources}
    if name == "topic_search":
        query = arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query is required")
        request = TopicRequest.create(
            query,
            topic=arguments.get("topic", "news"),
            sources=arguments.get("sources") or (),
            country=arguments.get("country"),
            language=arguments.get("language"),
            since=arguments.get("since"),
            until=arguments.get("until"),
        )
        return _TOPIC_SERVICE.execute(request).to_dict()
    if name in {"search_news", "group_news_events", "search_products", "compare_product_prices"}:
        topic = "news" if "news" in name else "shopping"
        report = _execute_topic_request(topic, arguments)
        if name == "group_news_events":
            return _group_news_events(report)
        if name == "compare_product_prices":
            return _compare_product_prices(report)
        return report
    if name in {"compare_news_sources", "track_news_topic", "get_news_trends"}:
        report = _execute_topic_request("news", arguments)
        if name == "track_news_topic":
            return {**report, "tracking": {"mode": "snapshot", "query": arguments["query"]}}
        if name == "compare_news_sources":
            by_source: dict[str, dict[str, Any]] = {}
            for row in report.get("results", []):
                source = str(row.get("source") or "unknown")
                item = by_source.setdefault(source, {"source": source, "result_count": 0, "headlines": []})
                item["result_count"] += 1
                if len(item["headlines"]) < 20:
                    item["headlines"].append(row.get("title"))
            return {**report, "sources": sorted(by_source.values(), key=lambda item: (-item["result_count"], item["source"]))}
        by_day: dict[str, int] = {}
        for row in report.get("results", []):
            day = str(row.get("published_at") or "unknown")[:10]
            by_day[day] = by_day.get(day, 0) + 1
        return {**report, "trends": [{"date": day, "result_count": by_day[day]} for day in sorted(by_day)]}
    if name in {"filter_products", "track_product_price", "find_product_alternatives"}:
        report = _compare_product_prices(_execute_topic_request("shopping", arguments))
        if name == "track_product_price":
            return {**report, "tracking": {"mode": "snapshot", "query": arguments["query"]}}
        if name == "filter_products":
            max_price = arguments.get("max_price")
            availability = arguments.get("availability")
            for product in report["products"]:
                product["offers"] = [offer for offer in product["offers"] if (max_price is None or offer.get("price_value") is None or offer["price_value"] <= max_price) and (not availability or offer.get("availability") == availability)]
                product["offer_count"] = len(product["offers"])
            report["products"] = [product for product in report["products"] if product["offer_count"]]
        else:
            report["products"] = [product for product in report["products"] if product["offer_count"] > 1]
        return report
    if name == "get_search_status":
        return _api_request(f"/searches/{arguments['id']}")
    if name == "list_results":
        params = {key: arguments[key] for key in ("run_id", "offset", "limit") if key in arguments}
        return _api_request("/results?" + urlencode(params) if params else "/results")
    if name == "list_search_history":
        params = {key: arguments[key] for key in ("query", "limit") if key in arguments}
        return _api_request(
            "/history/searches?" + urlencode(params) if params else "/history/searches"
        )
    if name == "analyze_history":
        query = ("?" + urlencode({"query": arguments["query"]})) if arguments.get("query") else ""
        return _api_request(f"/history/analytics{query}")
    if name == "analyze_url_statistics":
        scope = arguments.get("scope", "domains")
        params = {
            key: arguments[key]
            for key in ("domain", "include_findings", "limit", "offset")
            if key in arguments
        }
        return _api_request(
            f"/history/{scope}?{urlencode(params)}" if params else f"/history/{scope}"
        )
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
        envelope["data"] = {
            "truncated": True,
            "message": "MCP output exceeded the configured size limit.",
        }
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
                return self._send(
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32001, "message": "authentication required"},
                    },
                    401,
                )
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
                result = {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "serpscrap-mcp", "version": SCHEMA_VERSION},
                }
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
            return self._send(
                {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": str(exc)}}
            )
        except Exception as exc:
            return self._send(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32000,
                        "message": "MCP backend request failed",
                        "data": {"type": type(exc).__name__},
                    },
                }
            )

    def log_message(self, format: str, *args: Any) -> None:
        return


def _validate_bind_security(host: str) -> None:
    loopback = host in {"127.0.0.1", "localhost", "::1"}
    if (
        not loopback
        and not os.getenv("MCP_AUTH_TOKEN")
        and os.getenv("MCP_ALLOW_INSECURE_REMOTE") != "1"
    ):
        raise RuntimeError(
            "MCP_AUTH_TOKEN is required for non-loopback MCP_HOST; set MCP_ALLOW_INSECURE_REMOTE=1 only for explicit local-network development"
        )


if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "0.0.0.0")
    _validate_bind_security(host)
    server = ThreadingHTTPServer((host, int(os.getenv("MCP_PORT", "8001"))), McpHandler)
    server.serve_forever()
