import json

from click.testing import CliRunner

from serpscrap.cli import main


def test_cli_lists_click_commands():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "search" in result.output
    assert "browser-check" in result.output


def test_search_command_writes_results_and_logs(monkeypatch):
    expected = [{"query": "example", "serp_url": "https://example.com"}]
    monkeypatch.setattr("serpscrap.cli.SerpScrap.run", lambda self: expected)

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
