from pathlib import Path


def test_proxy_plan_documents_architecture_safety_and_acceptance_criteria():
    document = (Path(__file__).resolve().parents[1] / "docs" / "a2ui-proxy.md").read_text(
        encoding="utf-8"
    )

    for section in (
        "## Existing fragments and target architecture",
        "## Implementation phases",
        "### Phase 3: Proxy sources",
        "### Phase 4: Pool and health checks",
        "### Phase 5: Engine-aware selection",
        "## Test and acceptance strategy",
        "## Recommended order",
    ):
        assert section in document

    for term in ("SSRF protection", "ProxyPool", "proxy_file", "credentials"):
        assert term in document
