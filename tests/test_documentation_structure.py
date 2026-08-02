from pathlib import Path


def test_refactoring_plan_has_no_non_consecutive_heading_jumps() -> None:
    """Keep MyST heading levels consecutive for warning-as-error builds."""
    document = Path(__file__).parents[1] / "docs" / "refactoring2026.md"
    previous_level = 0

    for line in document.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            continue
        marker, _, _ = line.partition(" ")
        if not marker or set(marker) != {"#"}:
            continue
        level = len(marker)
        if previous_level:
            assert level <= previous_level + 1, line
        previous_level = level


def test_user_and_developer_documentation_is_exposed_in_full_navigation() -> None:
    docs = Path(__file__).parents[1] / "docs"
    index = (docs / "index.rst").read_text(encoding="utf-8")

    for page in ("install", "examples", "cli", "results", "configuration", "docker", "mcp", "development"):
        assert f"   {page}" in index
        assert (docs / f"{page}.rst").is_file()

    assert "globaltoc.html" in (docs / "conf.py").read_text(encoding="utf-8")
    assert not (docs / "changelog-refactoring2026.md").exists()


def test_current_release_interfaces_are_documented() -> None:
    root = Path(__file__).parents[1]
    readme = (root / "README.rst").read_text(encoding="utf-8")
    mcp = (root / "docs" / "mcp.rst").read_text(encoding="utf-8")
    cli = (root / "docs" / "cli.rst").read_text(encoding="utf-8")

    assert "2.0.0-alpha.1" in readme
    for tool in ("start_search", "get_search_status", "list_results", "list_engines"):
        assert tool in mcp
    for option in ("--keyword", "--engine", "--search-type", "--output", "--diagnostic-html"):
        assert option in cli
