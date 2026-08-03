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
