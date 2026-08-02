from pathlib import Path


def test_phase82_plan_covers_views_failures_and_canonical_urls():
    document = (
        Path(__file__).resolve().parents[1] / "docs" / "refactoring2026.md"
    ).read_text(encoding="utf-8")

    assert "## Refactoring Phase 8.2 - Current and Historical Result Views with Canonical URLs" in document
    assert "Title, URL, Relevance, Engine" in document
    assert "canonical_url" in document
    assert "engine-attributed failures" in document
    assert "Image-detail URLs" in document
