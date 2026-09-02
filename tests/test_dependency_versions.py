from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_dependency_versions_are_consistent():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    pipfile = (ROOT / "Pipfile").read_text(encoding="utf-8")
    runtime_lock = (ROOT / "requirements.lock").read_text(encoding="utf-8")
    dev_lock = (ROOT / "requirements-dev.lock").read_text(encoding="utf-8")
    dockerfile = (ROOT / "docker" / "Dockerfile").read_text(encoding="utf-8")

    assert '"Flask>=3.1.3,<4"' in pyproject
    assert 'flask = "==3.1.3"' in pipfile
    assert "Flask==3.1.3" in runtime_lock
    assert 'pip = "==26.2.1"' in pipfile
    assert "pip==26.2.1" in dev_lock
    assert '"pip==26.2.1"' in dockerfile
    assert 'build = "==1.6.0"' in pipfile
    assert "build==1.6.0" in dev_lock
    assert 'mypy = "==2.3.1"' in pipfile
    assert "mypy==2.3.1" in dev_lock
    assert 'ruff = "==0.16.5"' in pipfile
    assert "ruff==0.16.5" in dev_lock
