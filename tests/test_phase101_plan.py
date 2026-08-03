from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase101_mcp_hardening_plan_is_documented():
    document = (ROOT / "docs" / "refactoring2026.md").read_text(encoding="utf-8")
    required_sections = (
            "# Refactoring Phase 10.3 - MCP Server Best-Practice Hardening",
        "## Source-Derived Principles",
        "## Target MCP Contract",
        "## Implementation Slices",
        "## Verification Strategy",
            "## Phase 10.3 Acceptance Criteria",
        "## Out of Scope",
        "## Source Basis",
    )
    for section in required_sections:
        assert section in document

    for concept in (
        "structured output",
        "least privilege",
        "untrusted search content",
        "deterministic pagination",
        "authentication",
        "schema_version",
    ):
        assert concept in document
