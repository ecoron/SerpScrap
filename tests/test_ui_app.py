from http.server import ThreadingHTTPServer
from threading import Thread

from serpscrap.api_server import ApiHandler
from serpscrap.api_service import SearchJobService
from serpscrap.history_store import SearchHistoryStore
from ui.app import create_app


def test_flask_ui_renders_shell_and_healthcheck():
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    page = client.get("/")
    assert page.status_code == 200
    assert b"Explore your search data" in page.data
    assert b"static/css/tokens.css" in page.data
    assert b"static/js/app.js" in page.data
    for path, marker in (("/search", b"Search workspace"), ("/history", b"History & analysis"), ("/configuration", b"Configuration")):
        response = client.get(path)
        assert response.status_code == 200
        assert marker in response.data

    search_page = client.get("/search").data
    history_page = client.get("/history").data
    assert b"current-detail" in search_page
    assert b"search-settings-overlay" in search_page
    assert b"search-settings-toggle" in page.data
    assert b"historical-result-detail" not in history_page
    assert b"result-list" in search_page

    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json == {"service": "serpscrap-ui", "status": "ok"}


def test_flask_ui_serves_modular_assets():
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    assert client.get("/static/css/components.css").status_code == 200
    assert client.get("/static/js/views/results.js").status_code == 200


def test_ui_result_contract_keeps_all_result_kinds_and_awaits_refresh_callbacks():
    results_source = open("ui/static/js/views/results.js", encoding="utf-8").read()
    api_source = open("ui/static/js/api-client.js", encoding="utf-8").read()
    polling_source = open("ui/static/js/polling.js", encoding="utf-8").read()
    app_source = open("ui/static/js/app.js", encoding="utf-8").read()
    assert "rows.filter(row => row.result_kind !== 'image')" not in results_source
    assert "&kind=organic" not in api_source
    assert "await onUpdate(status)" in polling_source
    assert "await refreshCurrent(); await refreshOverview();" in app_source
    assert "result-sort" in app_source
    assert "result-snippet" in results_source
    assert "await startSearch({preventDefault() {}})" in app_source
    assert "createHistoricalDetailRow" in app_source
    assert "if (searchSubmitting) return" in app_source
    assert "finally { searchSubmitting = false" in app_source
    assert ".search-settings-overlay[hidden]" in open("ui/static/css/pages.css", encoding="utf-8").read()


def test_ui_proxy_reads_database_backed_history(monkeypatch, tmp_path):
    store = SearchHistoryStore(f"sqlite:///{tmp_path / 'history.db'}")
    store.create_run("run-ui", "database-backed query", {"search_engines": ["bing"]})
    service = SearchJobService(store=store, max_active_jobs=1, max_queued_jobs=1)
    handler = type("TestApiHandler", (ApiHandler,), {"service": service})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("SERPSCRAP_API_URL", f"http://127.0.0.1:{server.server_port}/api/v1")
    try:
        app = create_app()
        app.config.update(TESTING=True)
        client = app.test_client()
        response = client.get("/api/v1/history/searches")
        assert response.status_code == 200
        assert response.json["searches"][0]["query"] == "database-backed query"
        analytics = client.get("/api/v1/history/analytics")
        assert analytics.status_code == 200
        assert analytics.json["run_count"] == 1
    finally:
        server.shutdown()
        service.close(wait=False)


def test_ui_proxy_preserves_query_string(monkeypatch):
    captured = {}

    class FakeResponse:
        status = 200

        class Headers:
            def get(self, name, default=None):
                return default

        headers = Headers()

        def read(self):
            return b'{"results": []}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        return FakeResponse()

    monkeypatch.setattr("ui.app.urllib.request.urlopen", fake_urlopen)
    app = create_app()
    app.config.update(TESTING=True)
    response = app.test_client().get("/api/v1/results?run_id=run-ui&limit=10")
    assert response.status_code == 200
    assert captured["url"].endswith("/api/v1/results?run_id=run-ui&limit=10")
