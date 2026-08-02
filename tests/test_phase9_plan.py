from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase9_plan_and_audience_split_are_documented():
    plan = (ROOT / "docs" / "refactoring2026.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.rst").read_text(encoding="utf-8")

    for section in (
        "# Refactoring Phase 9 - Project Quality, Performance, and Documentation Structure",
        "## Documentation Audience and Structure",
        "## Performance and Reliability Goals",
        "## Release and Version 2 Communication",
        "## Test and Acceptance Strategy",
        "## Acceptance Criteria",
    ):
        assert section in plan

    assert "completely reworked" in readme
    assert "not yet" in readme and "PyPI" in readme
    assert "docker pull ecoron/serpscrap:<pre-release-tag>" in readme
    assert (ROOT / "docs" / "docker.rst").is_file()
    assert (ROOT / "docs" / "development.rst").is_file()
