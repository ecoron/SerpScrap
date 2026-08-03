from pathlib import Path


def test_phase81_plan_covers_configuration_defaults_and_refresh():
    document = (
        Path(__file__).resolve().parents[1] / "docs" / "refactoring2026.md"
    ).read_text(encoding="utf-8")

    required_sections = (
        "## Refactoring Phase 8.1 - Persisted Engine Configuration and Automatic Result Refresh",
        "### Source of Truth and Default Semantics",
        "### Persisted Configuration Model",
        "### API Contract",
        "### Configuration Page",
        "### Automatic Result Refresh",
        "### Test and Acceptance Strategy",
        "### Acceptance Criteria",
    )
    for section in required_sections:
        assert section in document

    for endpoint in ("GET /configuration", "PUT /configuration", "POST /configuration/reset", "GET /engines"):
        assert endpoint in document

    assert "all currently available and enabled registry" in document
    assert "bounded backoff" in document
