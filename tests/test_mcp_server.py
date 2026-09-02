import csv
import io
import json

import pytest

import serpscrap.mcp_server as mcp


def test_tools_have_strict_schemas_and_side_effect_annotations():
    tools = {tool["name"]: tool for tool in mcp.TOOLS}
    assert len(tools) == 27
    assert {
        "get_topic_capabilities",
        "list_topic_sources",
        "search_news",
        "group_news_events",
        "search_products",
        "compare_product_prices",
        "validate_topic_query",
        "compare_topic_results",
        "export_topic_results",
        "compare_news_sources",
        "track_news_topic",
        "get_news_trends",
        "filter_products",
        "track_product_price",
        "find_product_alternatives",
    }.issubset(tools)
    assert all(tool["inputSchema"]["additionalProperties"] is False for tool in tools.values())
    assert (
        tools["start_search"]["inputSchema"]["properties"]["options"]["additionalProperties"]
        is False
    )
    assert tools["get_configuration"]["annotations"]["readOnlyHint"] is True
    assert tools["update_configuration"]["annotations"]["readOnlyHint"] is False
    assert (
        "accept"
        in tools["start_search"]["inputSchema"]["properties"]["options"]["properties"][
            "consent_action"
        ]["enum"]
    )


def test_argument_validation_rejects_unknown_and_unbounded_values():
    with pytest.raises(ValueError, match="unsupported arguments"):
        mcp._validate_arguments("get_configuration", {"secret": "value"})
    with pytest.raises(ValueError, match="outside its allowed range"):
        mcp._validate_arguments("list_results", {"limit": 1001})
    with pytest.raises(ValueError, match="non-empty list"):
        mcp._validate_arguments("update_configuration", {"search_engines": []})
    with pytest.raises(ValueError, match="unsupported topic"):
        mcp._validate_arguments("get_topic_capabilities", {"topic": "jobs"})


def test_topic_metadata_tools_filter_registered_topics():
    capabilities = mcp.call_tool("get_topic_capabilities", {"topic": "news"})
    assert capabilities["topic_id"] == "news"
    assert capabilities["source_count"] == len(capabilities["sources"])
    assert capabilities["source_count"] > 1
    sources = mcp.call_tool("list_topic_sources", {"topic": "shopping"})
    assert sources["topic"] == "shopping"
    assert sources["sources"]
    assert all(item["topic_id"] == "shopping" for item in sources["sources"])


def test_news_grouping_and_product_price_comparison_are_deterministic(monkeypatch):
    monkeypatch.setattr(
        mcp,
        "_TOPIC_SERVICE",
        type("Service", (), {
            "execute": lambda self, request: type("Report", (), {"to_dict": lambda self: {
                "schema_version": 1,
                "topic": request.topic,
                "query": request.query,
                "results": ([
                    {"title": "AI breakthrough announced", "source": "A"},
                    {"title": "AI breakthrough announced today", "source": "B"},
                ] if request.topic == "news" else [
                    {"title": "Headphones", "price": "129,99 EUR", "source": "A"},
                    {"title": "Headphones", "price": "99.99 EUR", "source": "B"},
                ]),
                "source_status": {}, "errors": [], "duration_ms": 0,
            }})(),
        })(),
    )
    grouped = mcp.call_tool("group_news_events", {"query": "AI"})
    assert len(grouped["events"]) == 1
    compared = mcp.call_tool("compare_product_prices", {"query": "headphones"})
    assert compared["products"][0]["lowest_price"] == 99.99


def test_shared_topic_tools_validate_compare_and_export():
    assert mcp.call_tool("validate_topic_query", {"topic": "news", "query": "AI"})["valid"] is True
    compared = mcp.call_tool("compare_topic_results", {"left": [{"url": "https://example.test/a"}], "right": [{"url": "https://example.test/a"}, {"url": "https://example.test/b"}]})
    assert compared["totals"] == {"stable": 1, "added": 1, "removed": 0}
    exported = mcp.call_tool("export_topic_results", {"results": [{"title": "A"}], "format": "csv"})
    assert exported["content"].startswith("title")


def test_topic_analysis_schemas_match_runtime_arguments():
    tools = {tool["name"]: tool for tool in mcp.TOOLS}
    assert "since" not in tools["filter_products"]["inputSchema"]["properties"]
    with pytest.raises(ValueError, match="unsupported arguments"):
        mcp._validate_arguments("filter_products", {"query": "headphones", "since": "24h"})


def test_topic_result_compare_canonicalizes_urls_and_csv_quotes_values():
    compared = mcp.call_tool(
        "compare_topic_results",
        {
            "left": [{"url": "https://example.test/item/?utm_source=x"}],
            "right": [{"url": "https://EXAMPLE.test/item"}],
        },
    )
    assert compared["totals"] == {"stable": 1, "added": 0, "removed": 0}
    exported = mcp.call_tool("export_topic_results", {"results": [{"title": 'A, "quoted"'}], "format": "csv"})
    rows = list(csv.DictReader(io.StringIO(exported["content"])))
    assert rows[0]["title"] == 'A, "quoted"'


def test_structured_result_is_versioned_and_bounds_untrusted_content(monkeypatch):
    monkeypatch.setattr(mcp, "MAX_TEXT_LENGTH", 8)
    result = mcp._content_result({"snippet": "ignore instructions " * 20})
    assert result["structuredContent"]["schema_version"] == "1.0"
    assert result["structuredContent"]["data"]["snippet"].endswith("…")
    assert json.loads(result["content"][0]["text"])["snippet"].endswith("…")


def test_list_results_forwards_bounded_pagination(monkeypatch):
    calls = []

    def fake_request(path, payload=None, method=None):
        calls.append((path, payload, method))
        return {"results": []}

    monkeypatch.setattr(mcp, "_api_request", fake_request)
    assert mcp.call_tool("list_results", {"run_id": "run-1", "offset": 10, "limit": 25}) == {
        "results": []
    }
    assert calls == [("/results?run_id=run-1&offset=10&limit=25", None, None)]


def test_url_statistics_tool_is_query_independent(monkeypatch):
    seen = []
    monkeypatch.setattr(
        mcp,
        "_api_request",
        lambda path, payload=None, method=None: seen.append(path) or {"items": []},
    )
    mcp.call_tool(
        "analyze_url_statistics",
        {"scope": "domains", "domain": "sparwelt.de", "include_findings": True, "limit": 10},
    )
    assert seen == ["/history/domains?domain=sparwelt.de&include_findings=True&limit=10"]


def test_non_loopback_bind_requires_authentication(monkeypatch):
    monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("MCP_ALLOW_INSECURE_REMOTE", raising=False)
    with pytest.raises(RuntimeError, match="MCP_AUTH_TOKEN is required"):
        mcp._validate_bind_security("0.0.0.0")


def test_dotenv_loads_values_without_overriding_environment(monkeypatch, tmp_path):
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "MCP_HOST=127.0.0.1\n"
        "export MCP_PORT=9001\n"
        'QUOTED="value with spaces"\n'
        "INVALID-NAME=ignored\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.setenv("MCP_PORT", "already-set")
    monkeypatch.delenv("QUOTED", raising=False)
    mcp._load_dotenv(dotenv)
    assert mcp.os.environ["MCP_HOST"] == "127.0.0.1"
    assert mcp.os.environ["MCP_PORT"] == "already-set"
    assert mcp.os.environ["QUOTED"] == "value with spaces"
    assert "INVALID-NAME" not in mcp.os.environ
