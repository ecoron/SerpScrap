from pathlib import Path

from serpscrap.api_server import MAX_REQUEST_BYTES

ROOT = Path(__file__).resolve().parents[1]


def test_release_metadata_is_consistent():
    expected = "2.0.0-alpha.3"
    release_files = (
        ROOT / "pyproject.toml",
        ROOT / "README.rst",
        ROOT / "docs" / "conf.py",
        ROOT / "docs" / "index.rst",
        ROOT / "docs" / "docker.rst",
        ROOT / "docker" / "README.md",
        ROOT / "docker" / "compose.yml",
        ROOT / "ui" / "app.py",
    )

    assert f'version = "{expected}"' in (ROOT / "pyproject.toml").read_text()
    assert all(expected in path.read_text(encoding="utf-8") for path in release_files)
    assert f"## [{expected}] - 2026-09-02" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def test_latest_changes_are_recorded_in_alpha_three_release():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    release_start = changelog.index("## [2.0.0-alpha.3] - 2026-09-02")
    next_release = changelog.index("## [2.0.0-alpha.2]", release_start)
    release_body = changelog[release_start:next_release]
    assert "Extended UI proxy-operation timeouts" in release_body
    assert "Updated the pinned development toolchain" in release_body


def test_api_request_limit_is_positive_and_bounded():
    assert MAX_REQUEST_BYTES >= 1024
    assert "API_MAX_REQUEST_BYTES" in (ROOT / "serpscrap" / "api_server.py").read_text()


def test_api_defaults_to_ui_origin_instead_of_wildcard_cors():
    source = ROOT / "serpscrap" / "api_server.py"
    content = source.read_text(encoding="utf-8")
    assert "http://localhost:8080" in content
    assert 'os.getenv("CORS_ORIGIN", "*")' not in content
