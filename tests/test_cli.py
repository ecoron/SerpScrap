import json

from click.testing import CliRunner

from serpscrap.cli import main
from serpscrap.config import Config


def test_cli_lists_click_commands():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "search" in result.output
    assert "browser-check" in result.output


def test_search_command_writes_results_and_logs(monkeypatch):
    expected = [{"query": "example", "serp_url": "https://example.com"}]
    monkeypatch.setattr("serpscrap.cli.SerpScrap.search", lambda self, *args, **kwargs: expected)

    result = CliRunner().invoke(
        main,
        [
            "--log-level",
            "DEBUG",
            "--log-format",
            "json",
            "search",
            "--keyword",
            "example",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == expected
    assert "Starting 1 query job(s)" in result.stderr
    assert '"level": "INFO"' in result.stderr


def test_search_command_passes_json_output_options(monkeypatch, tmp_path):
    called = {}

    def fake_search(self, keywords, **kwargs):
        called.update({"keywords": keywords, **kwargs})
        return []

    monkeypatch.setattr("serpscrap.cli.SerpScrap.search", fake_search)
    target = tmp_path / "results.json"

    result = CliRunner().invoke(
        main,
        [
            "search",
            "-k",
            "one",
            "--search-type",
            "news",
            "--output",
            str(target),
            "--overwrite",
            "--no-history",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []
    assert called["keywords"] == ["one"]
    assert called["output"] == str(target)
    assert called["overwrite"] is True
    assert called["config"].get()["store_history"] is False
    assert called["config"].get()["search_type"] == "news"


def test_search_command_uses_config_defaults_when_options_are_omitted(monkeypatch):
    called = {}

    def fake_search(self, keywords, **kwargs):
        called.update(kwargs)
        return []

    monkeypatch.setattr("serpscrap.cli.SerpScrap.search", fake_search)
    result = CliRunner().invoke(main, ["search", "-k", "Balkonkraftwerk"])

    assert result.exit_code == 0
    config = called["config"].get()
    defaults = Config().get()
    for key in ("search_engines", "country_code", "num_workers", "num_pages_for_keyword", "search_type", "do_caching", "store_history"):
        assert config[key] == defaults[key]
