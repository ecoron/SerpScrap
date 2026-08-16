from pathlib import Path


def test_user_and_developer_documentation_is_exposed_in_full_navigation() -> None:
    docs = Path(__file__).parents[1] / "docs"
    index = (docs / "index.rst").read_text(encoding="utf-8")

    for page in ("install", "examples", "cli", "results", "configuration", "docker", "mcp", "topic-tools", "development"):
        assert f"   {page}" in index
        assert (docs / f"{page}.rst").is_file()

    assert "globaltoc.html" in (docs / "conf.py").read_text(encoding="utf-8")
    assert not (docs / "changelog-refactoring2026.md").exists()


def test_current_release_interfaces_are_documented() -> None:
    root = Path(__file__).parents[1]
    readme = (root / "README.rst").read_text(encoding="utf-8")
    mcp = (root / "docs" / "mcp.rst").read_text(encoding="utf-8")
    cli = (root / "docs" / "cli.rst").read_text(encoding="utf-8")
    topics = (root / "docs" / "topic-tools.rst").read_text(encoding="utf-8")

    assert "2.0.0-alpha.2" in readme
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
    for marker in ("TopicService", "topic-search", "/api/v1/topics/search", "topic_search"):
        assert marker in topics


def test_alpha_topic_tools_plan_documents_standardized_extension_points() -> None:
    plan = Path(__file__).parents[1] / "docs" / "alpaha-2.0.0-tools.md"
    content = plan.read_text(encoding="utf-8")

    assert "TopicPlugin" in content
    assert "News-Umsetzung" in content
    assert "Shopping-Umsetzung" in content
    assert "TopicPluginRegistry" in content
    assert "Umsetzungsplan" in content
