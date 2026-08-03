from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase102_dynamic_ui_concept_is_documented():
    document = (ROOT / "docs" / "refactoring2026.md").read_text(encoding="utf-8")

    for section in (
        "## Rough Product and Interaction Concept",
        "### Application Shell",
        "### Dynamic Data Model in the Frontend",
        "### Search and Result Exploration",
        "### History and Analysis Workspace",
        "### Visual and Usability Direction",
        "### Frontend Technical Setup",
        "### Conceptual Delivery Order",
        "## Research-Based Template Decision",
    ):
        assert section in document

    for requirement in (
        "bounded polling and backoff",
        "side-by-side comparison",
        "accessible tabular alternatives",
        "typed visual variants",
        "Flask as the UI delivery layer",
        "Jinja as the server-side template",
        "tokens.css",
        "api-client.js",
        "Tabler",
        "CHANGELOG.md",
    ):
        assert requirement in document
