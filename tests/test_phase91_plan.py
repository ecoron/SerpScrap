from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase91_plan_documents_provider_specific_safe_consent_strategy():
    document = (ROOT / "docs" / "refactoring2026.md").read_text(encoding="utf-8")
    searchengines = (ROOT / "docs" / "searchengines.md").read_text(encoding="utf-8")

    required_sections = (
        "# Refactoring Phase 9.1 - Google and Ecosia Consent and Browser-Flow Completion",
        "## Research Findings",
        "## Solution Decision",
        "## Provider-Specific Implementation Plan",
        "## Shared State Machine and Safety Rules",
        "## Test and Acceptance Strategy",
        "## Acceptance Criteria",
    )
    for section in required_sections:
        assert section in document

    assert "Custom Search JSON API" in document
    assert "consent_required" in document
    assert "undocumented provider JavaScript API" in document
    assert "Provider safety" in searchengines
    assert "xPrivo" in searchengines
    assert "Phase 9.1" not in searchengines
