# ruff: noqa: I001

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_docker_files_are_grouped_and_compose_uses_repository_contexts():
    docker_dir = ROOT / "docker"
    assert (docker_dir / "compose.yml").is_file()
    assert (docker_dir / "app" / "Dockerfile").is_file()
    assert (docker_dir / "ui" / "Dockerfile").is_file()
    assert (docker_dir / "mcp" / "Dockerfile").is_file()
    assert not (ROOT / "Dockerfile").exists()
    assert not (ROOT / "docker-compose.yml").exists()

    compose = (docker_dir / "compose.yml").read_text(encoding="utf-8")
    assert "context: .." in compose
    assert "dockerfile: docker/app/Dockerfile" in compose
    assert "../data/postgres:/var/lib/postgresql/data" in compose
    assert "../logs:/var/log/serpscrap" in compose
