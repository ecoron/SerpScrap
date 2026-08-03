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

    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json == {"service": "serpscrap-ui", "status": "ok"}


def test_flask_ui_serves_modular_assets():
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    assert client.get("/static/css/components.css").status_code == 200
    assert client.get("/static/js/views/results.js").status_code == 200


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
