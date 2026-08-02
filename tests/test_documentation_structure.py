from pathlib import Path


def test_refactoring_plan_has_no_non_consecutive_heading_jumps() -> None:
    """Keep MyST heading levels consecutive for warning-as-error builds."""
    document = Path(__file__).parents[1] / "docs" / "refactoring2026.md"
    previous_level = 0

    for line in document.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            continue
        marker, _, _ = line.partition(" ")
        if not marker or set(marker) != {"#"}:
            continue
        level = len(marker)
        if previous_level:
            assert level <= previous_level + 1, line
        previous_level = level
