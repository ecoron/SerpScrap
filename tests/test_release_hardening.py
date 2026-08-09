from pathlib import Path

from serpscrap.api_server import MAX_REQUEST_BYTES

ROOT = Path(__file__).resolve().parents[1]


def test_release_metadata_is_consistent():
    expected = "2.0.0-alpha.2"
    assert f'version = "{expected}"' in (ROOT / "pyproject.toml").read_text()
    assert expected in (ROOT / "README.rst").read_text()
    assert expected in (ROOT / "docs" / "conf.py").read_text()


def test_api_request_limit_is_positive_and_bounded():
    assert MAX_REQUEST_BYTES >= 1024
    assert "API_MAX_REQUEST_BYTES" in (ROOT / "serpscrap" / "api_server.py").read_text()


def test_api_defaults_to_ui_origin_instead_of_wildcard_cors():
    source = ROOT / "serpscrap" / "api_server.py"
    content = source.read_text(encoding="utf-8")
    assert "http://localhost:8080" in content
    assert 'os.getenv("CORS_ORIGIN", "*")' not in content
