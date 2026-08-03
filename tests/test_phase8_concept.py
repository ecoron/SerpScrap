from pathlib import Path


def test_phase8_concept_documents_multicontainer_boundaries_and_acceptance():
    document = (
        Path(__file__).resolve().parents[1] / "docs" / "refactoring2026.md"
    ).read_text(encoding="utf-8")

    required_sections = (
        "## Refactoring Phase 8 - Multicontainer Application and Search Archive Analysis",
        "### Architecture and Responsibilities",
        "### User Interface",
        "### MCP Server",
        "### Persistence and Local Mounts",
        "### Test and Acceptance Strategy",
        "### Acceptance Criteria",
    )
    for section in required_sections:
        assert section in document

    for container in ("`serpscrap-app`", "`serpscrap-db`", "`serpscrap-ui`", "`serpscrap-mcp`"):
        assert container in document

    assert "./data/postgres" in document
    assert "Historical hits can be filtered" in document
    assert "no duplicated scraping or persistence" in document
