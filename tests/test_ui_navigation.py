from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ui_navigation_uses_separate_pages_and_global_header_search():
    base = (ROOT / "ui" / "templates" / "base.html").read_text(encoding="utf-8")
    app = (ROOT / "ui" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    for endpoint in ("search_page", "history_page", "configuration_page"):
        assert endpoint in base
    assert 'id="global-search-form"' in base
    assert 'id="sidebar-toggle"' in base
    assert "sidebar-collapsed" in app
    assert "localStorage" in app
    assert "api.engines()" in app
    assert "provider_count" in app
    assert "Search again" in app
    assert "renderProviderHealth" in app
    assert "className = 'toolbar-actions'" in app
    assert "attributed results" in app
    history_view = (ROOT / "ui" / "static" / "js" / "views" / "history.js").read_text(encoding="utf-8")
    assert "serp_title" in history_view
    assert "serp_snippet" in history_view
    assert "canonical_url" in history_view
    assert "description" in history_view
    assert "summary" in history_view
    assert "Choose two different runs" in history_view
    assert "toFixed(1)" in history_view
    assert "status-badge" in history_view
    assert "search-again" in history_view
    assert "/search?q=" in history_view
    assert "history?run" not in history_view
