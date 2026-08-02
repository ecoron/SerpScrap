from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase92_plugin_structure_plan_is_documented():
    document = (ROOT / "docs" / "refactoring2026.md").read_text(encoding="utf-8")
    required_sections = (
        "# Refactoring Phase 9.2 - Developer-Friendly Search-Engine Plugin Structure",
        "## Target Plugin Contract",
        "## Implementation Slices",
        "## Verification Strategy",
        "## Phase 9.2 Acceptance Criteria",
    )
    for section in required_sections:
        assert section in document

    assert "typed capability and metadata models" in document
    assert "new minimal fixture-backed example engine" in document
    assert "No engine-specific branch" in document
