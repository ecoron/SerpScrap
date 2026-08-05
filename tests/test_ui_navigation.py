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
