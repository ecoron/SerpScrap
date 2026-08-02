# ruff: noqa: I001

import json
import threading
import urllib.request
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer

from serpscrap.api_server import ApiHandler
from serpscrap.api_service import SearchJobService
from serpscrap.configuration_service import SearchConfigurationService
from serpscrap.history_store import SearchHistoryStore
from serpscrap.mcp_server import TOOLS
from serpscrap.models import SearchReport, SearchRequest


def _request() -> SearchRequest:
    return SearchRequest(queries=("example",), settings={"keywords": ["example"]})


class FakeApplication:
    def execute(self, request: SearchRequest) -> SearchReport:
        now = datetime.now(timezone.utc)
        return SearchReport(
            results=[
                {
                    "query": request.queries[0],
                    "search_engine": "fixture",
                    "serp_title": "Example result",
                    "serp_url": "https://example.test",
                }
            ],
            started_at=now,
            stopped_at=now,
        )


def test_history_store_persists_runs_and_returns_analysis(tmp_path):
    store = SearchHistoryStore(f"sqlite:///{tmp_path / 'history.db'}")
    service = SearchJobService(FakeApplication(), store)

    run_id = service.submit(_request())
    for _ in range(50):
        status = service.status(run_id)
        if status and status["status"] == "completed":
            break
        threading.Event().wait(0.01)

    assert status["result_count"] == 1
    assert store.list_results(run_id=run_id)[0]["serp_title"] == "Example result"
    assert store.analytics()["results_by_engine"] == {"fixture": 1}


def test_api_search_and_history_endpoints_use_shared_service(tmp_path):
    store = SearchHistoryStore(f"sqlite:///{tmp_path / 'history.db'}")
    service = SearchJobService(FakeApplication(), store)
    handler = type("TestApiHandler", (ApiHandler,), {"service": service})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        request = urllib.request.Request(
            base + "/api/v1/searches",
            data=json.dumps({"query": "example"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            created = json.loads(response.read())
        assert response.status == 202
        for _ in range(50):
            with urllib.request.urlopen(base + f"/api/v1/searches/{created['id']}") as response:
                status = json.loads(response.read())
            if status["status"] == "completed":
                break
            threading.Event().wait(0.01)
        with urllib.request.urlopen(base + "/api/v1/history/analytics") as response:
            analytics = json.loads(response.read())
        assert analytics["result_count"] == 1
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_configuration_defaults_persist_and_explicit_search_selection_overrides(tmp_path):
    store = SearchHistoryStore(f"sqlite:///{tmp_path / 'history.db'}")
    configuration = SearchConfigurationService(store)

    defaults = configuration.get()
    assert defaults["source"] == "defaults"
    assert len(defaults["configuration"]["search_engines"]) == len(defaults["engines"])

    saved = configuration.save({"search_engines": ["bing", "google"]})
    assert saved["source"] == "persisted"
    assert saved["revision"] == 1
    assert configuration.get()["configuration"]["search_engines"] == ["bing", "google"]

    resolved, metadata = configuration.resolve_options({})
    assert resolved["search_engines"] == ["bing", "google"]
    assert metadata["revision"] == 1
    resolved, metadata = configuration.resolve_options({"search_engines": ["duckduckgo"]})
    assert resolved["search_engines"] == ["duckduckgo"]
    assert metadata["source"] == "explicit"

    try:
        configuration.save({"search_engines": []})
    except ValueError:
        pass
    else:
        raise AssertionError("empty engine selections must be rejected")
    assert configuration.get()["configuration"]["search_engines"] == ["bing", "google"]
    reset = configuration.reset()
    assert reset["source"] == "defaults"
    assert len(reset["configuration"]["search_engines"]) == len(reset["engines"])


def test_api_configuration_endpoints_expose_registry_and_persist_selection(tmp_path):
    store = SearchHistoryStore(f"sqlite:///{tmp_path / 'history.db'}")
    service = SearchJobService(FakeApplication(), store)
    handler = type("TestApiHandler", (ApiHandler,), {"service": service})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urllib.request.urlopen(base + "/api/v1/configuration") as response:
            defaults = json.loads(response.read())
        assert defaults["source"] == "defaults"
        request = urllib.request.Request(
            base + "/api/v1/configuration",
            data=json.dumps({"search_engines": ["bing"]}).encode(),
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        with urllib.request.urlopen(request) as response:
            saved = json.loads(response.read())
        assert saved["configuration"]["search_engines"] == ["bing"]
        with urllib.request.urlopen(base + "/api/v1/engines") as response:
            engines = json.loads(response.read())
        assert any(engine["engine_id"] == "bing" for engine in engines["engines"])
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_mcp_exposes_phase81_configuration_tools():
    names = {tool["name"] for tool in TOOLS}
    assert {"list_engines", "get_configuration", "update_configuration", "reset_configuration"} <= names
