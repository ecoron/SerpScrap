# ruff: noqa: I001

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_docker_uses_one_project_dockerfile_and_shared_image():
    docker_dir = ROOT / "docker"
    assert (docker_dir / "compose.yml").is_file()
    assert (docker_dir / "Dockerfile").is_file()
    assert list(docker_dir.rglob("Dockerfile")) == [docker_dir / "Dockerfile"]
    assert not (ROOT / "Dockerfile").exists()
    assert not (ROOT / "docker-compose.yml").exists()

    compose = (docker_dir / "compose.yml").read_text(encoding="utf-8")
    assert "context: .." in compose
    assert compose.count("image: ${SERPSCRAP_IMAGE:-serpscrap:2.0.0-alpha.2}") == 3
    assert compose.count("dockerfile: docker/Dockerfile") == 1
    assert 'entrypoint: ["python", "-m", "ui.app"]' in compose
    assert "http://localhost:8080/healthz" in compose
    assert "../data/postgres:/var/lib/postgresql/data" in compose
    assert "../logs:/var/log/serpscrap" in compose
    assert "searxng-valkey:" in compose
    assert "profiles: [searxng]" not in compose
    assert "SERPSCRAP_SEARXNG_URL" in compose
    assert "POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD" in compose
    assert "SEARXNG_SECRET:?Set SEARXNG_SECRET" in compose
    assert "127.0.0.1:8000" in compose
    assert "127.0.0.1:8001" in compose
    searxng_settings = (docker_dir / "searxng" / "settings.yml").read_text(encoding="utf-8")
    limiter = (docker_dir / "searxng" / "limiter.toml").read_text(encoding="utf-8")
    for engine in ("ahmia", "torch", "wikidata", "startpage", "arxiv", "pubmed", "openalex", "crossref", "stackoverflow", "askubuntu", "superuser", "reuters"):
        assert f"name: {engine}" in searxng_settings
        assert "inactive: true" in searxng_settings
    assert "[botdetection.ip_limit]" in limiter
    assert '"127.0.0.1/32"' in limiter
    assert '"172.16.0.0/12"' in limiter
    assert "name: semantic scholar" in searxng_settings


def test_shared_image_contains_all_runtime_payloads_and_safe_defaults():
    dockerfile = (ROOT / "docker" / "Dockerfile").read_text(encoding="utf-8")

    for payload in ("COPY serpscrap ./serpscrap", "COPY scrapcore ./scrapcore", "COPY ui ./ui"):
        assert payload in dockerfile
    assert "USER serpscrap" in dockerfile
    assert "EXPOSE 8000 8001 8080" in dockerfile
