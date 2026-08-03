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
    assert compose.count("image: ${SERPSCRAP_IMAGE:-serpscrap:2.0.0-alpha.1}") == 3
    assert compose.count("dockerfile: docker/Dockerfile") == 1
    assert "entrypoint: [\"python\"]" in compose
    assert "--directory\", \"/app/ui" in compose
    assert "../data/postgres:/var/lib/postgresql/data" in compose
    assert "../logs:/var/log/serpscrap" in compose


def test_shared_image_contains_all_runtime_payloads_and_safe_defaults():
    dockerfile = (ROOT / "docker" / "Dockerfile").read_text(encoding="utf-8")

    for payload in ("COPY serpscrap ./serpscrap", "COPY scrapcore ./scrapcore", "COPY ui ./ui"):
        assert payload in dockerfile
    assert "USER serpscrap" in dockerfile
    assert "EXPOSE 8000 8001 8080" in dockerfile
