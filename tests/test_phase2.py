import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from scrapcore.tools import ConfigurationError
from serpscrap import JsonOutputError, JsonResultWriter, SearchRequest, SerpScrap
from serpscrap.application import SearchApplication


def _link(rank, url, title, link_type="results"):
    return SimpleNamespace(
        rank=rank,
        link=url,
        title=title,
        link_type=link_type,
        rating=None,
        domain=url.split("/")[2],
        visible_link=url,
        snippet=None,
        sitelinks=None,
    )


def _serp(query, page, links=(), status="successful"):
    return SimpleNamespace(
        query=query,
        page_number=page,
        search_engine_name="google",
        status=status,
        num_results_for_query="About 2 results",
        num_results=len(links),
        screenshot=None,
        links=list(links),
        related_keywords=[],
    )


class FakeRunner:
    def __init__(self, serps):
        self.serps = serps
        self.config = None

    def run(self, config):
        self.config = config
        now = datetime(2026, 8, 1, 12, 0, 0)
        return SimpleNamespace(serps=self.serps, started_searching=now, stopped_searching=now)


def test_application_returns_native_deterministically_ordered_rows():
    runner = FakeRunner(
        [
            _serp("second", 1, [_link(1, "https://second.example/", "Second")]),
            _serp(
                "first",
                1,
                [
                    _link(2, "https://b.example/", "B"),
                    _link(1, "https://a.example/", "A"),
                ],
            ),
        ]
    )
    request = SearchRequest.create(["first", "second"], {"do_caching": False})

    report = SearchApplication(runner=runner).execute(request)

    assert [row["query"] for row in report.results] == ["first", "first", "second"]
    assert [row["serp_rank"] for row in report.results] == [1, 2, 1]
    assert isinstance(report.results[0]["serp_rank"], int)
    assert report.results[0]["serp_rating"] is None
    assert json.loads(json.dumps(report.results)) == report.results


def test_application_keeps_results_and_reports_page_failure():
    failed = _serp("query", 2, status="timeout: page did not load")
    failed.failure_url = "https://google.example/search"
    failed.failure_retryable = True
    failed.correlation_id = "job-1"
    runner = FakeRunner(
        [_serp("query", 1, [_link(1, "https://example.com/", "Example")]), failed]
    )

    report = SearchApplication(runner=runner).execute(SearchRequest.create("query"))

    assert len(report.results) == 1
    assert report.failures[0].to_dict() == {
        "query": "query",
        "search_engine": "google",
        "page_number": 2,
        "url": "https://google.example/search",
        "category": "timeout",
        "message": "page did not load",
        "retryable": True,
        "correlation_id": "job-1",
    }


def test_application_reports_optional_history_failure_without_losing_rows():
    runner = FakeRunner([_serp("query", 1, [_link(1, "https://example.com/", "Example")])])
    original_run = runner.run

    def run_with_failure(config):
        search = original_run(config)
        search.persistence_failures = ["history disk unavailable"]
        return search

    runner.run = run_with_failure
    report = SearchApplication(runner=runner).execute(SearchRequest.create("query"))

    assert len(report.results) == 1
    assert report.failures[0].category == "persistence"
    assert report.failures[0].retryable is True


def test_json_writer_round_trips_unicode_and_native_types(tmp_path):
    rows = [{"title": "Bienenkönigin", "rank": 1, "rating": None, "featured": False}]

    target = JsonResultWriter().write(tmp_path / "nested" / "results", rows)

    assert target == (tmp_path / "nested" / "results.json").resolve()
    assert json.loads(target.read_text(encoding="utf-8")) == rows
    assert "Bienenkönigin" in target.read_text(encoding="utf-8")


def test_json_writer_refuses_existing_file_without_overwrite(tmp_path):
    target = tmp_path / "results.json"
    target.write_text("old", encoding="utf-8")

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        JsonResultWriter().write(target, [])

    assert target.read_text(encoding="utf-8") == "old"
    JsonResultWriter().write(target, [{"new": True}], overwrite=True)
    assert json.loads(target.read_text(encoding="utf-8")) == [{"new": True}]


def test_json_writer_rejects_csv_path():
    with pytest.raises(JsonOutputError, match="CSV is unsupported"):
        JsonResultWriter().write(Path("results.csv"), [])


def test_direct_public_search_and_save_use_canonical_list(tmp_path):
    runner = FakeRunner([_serp("query", 1, [_link(1, "https://example.com/", "Example")])])
    scraper = SerpScrap(application=SearchApplication(runner=runner))

    results = scraper.search("query", pages=2, workers=3)
    target = scraper.save_json(tmp_path / "results")

    assert isinstance(results, list) and isinstance(results[0], dict)
    assert json.loads(target.read_text(encoding="utf-8")) == results
    assert runner.config["num_pages_for_keyword"] == 2
    assert runner.config["num_workers"] == 3


def test_removed_output_configuration_has_migration_error():
    with pytest.raises(ConfigurationError, match="results.json"):
        SearchRequest.create("query", {"output_filename": "results.csv"})


def test_search_request_is_deeply_immutable_and_returns_isolated_config():
    request = SearchRequest.create("query")

    with pytest.raises(TypeError):
        request.settings["headers"]["Accept"] = "changed"

    config = request.to_config()
    config["headers"]["Accept"] = "changed"
    assert request.settings["headers"]["Accept"] != "changed"


def test_csv_api_is_not_exported_or_available():
    import serpscrap

    assert not hasattr(serpscrap, "CsvWriter")
    assert not hasattr(SerpScrap(), "as_csv")
