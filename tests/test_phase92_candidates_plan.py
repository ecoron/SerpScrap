from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase92_candidate_research_and_rollout_plan_are_documented():
    searchengines = (ROOT / "docs" / "searchengines.md").read_text(encoding="utf-8")
    refactoring = (ROOT / "docs" / "refactoring2026.md").read_text(encoding="utf-8")

    for candidate in (
        "MetaGer",
        "GOOD",
        "xPrivo",
        "Marginalia",
        "SearXNG",
        "eTools.ch",
    ):
        assert candidate in searchengines

    for section in (
        "## Phase 9.2 Candidate Expansion: Additional European Engines",
        "### Selection scope and evidence",
        "### Reconnaissance matrix",
        "### Candidate-specific implementation notes",
    ):
        assert section in searchengines

    for section in (
        "## Phase 9.2 European Candidate Rollout Plan",
        "### Prioritization",
        "### Implementation steps",
        "### Acceptance criteria",
    ):
        assert section in refactoring

    assert "without an API key" in refactoring
    assert "Marginalia API" in refactoring
    assert "SearXNG selection is instance-scoped" in refactoring
