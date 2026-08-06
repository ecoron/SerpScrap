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
    for configuration_marker in (
        "Claude Code",
        '"mcpServers"',
        '"type": "mcp"',
        'model="gpt-5"',
        '"model": "claude-sonnet-4-20250514"',
        "OpenAI remote MCP",
    ):
        assert configuration_marker in mcp
    for option in ("--keyword", "--engine", "--search-type", "--output", "--diagnostic-html"):
        assert option in cli


def test_alpha_ui_development_plan_covers_research_limits_and_delivery_gates() -> None:
    document = Path(__file__).parents[1] / "docs" / "a2ui-development.md"
    content = document.read_text(encoding="utf-8")

    assert document.is_file()
    for marker in (
        "## Capability Assessment",
        "## Best-Practice Review",
        "## Detailed Functional Requirements",
        "## API and Data Contract Work",
        "## Implementation Slices",
        "## Test Plan",
        "## Acceptance Gates",
        "heuristic",
        "canonical URL",
        "identity_key_version",
        "stable/moved/new/lost",
    ):
        assert marker in content


def test_configuration_ui_plan_covers_full_defaults_persistence_grouping_and_reset() -> None:
    document = Path(__file__).parents[1] / "docs" / "a2ui-configuration.md"
    content = document.read_text(encoding="utf-8")

    for marker in (
        "## Configuration Inventory and Grouping",
        "## API and Persistence Contract",
        "## Validation and Safety Rules",
        "## Implementation Slices",
        "## Acceptance Criteria",
        "initial_defaults",
        "schema_version",
        "Reset deletes the persisted record",
        "Sensitive values are redacted",
    ):
        assert marker in content


def test_internal_alpha_ui_plans_are_excluded_from_readthedocs() -> None:
    conf = (Path(__file__).parents[1] / "docs" / "conf.py").read_text(encoding="utf-8")
    assert '"alpha-2.0.0-ui.md"' in conf
    assert '"a2ui-*.md"' in conf
