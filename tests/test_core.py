from datetime import datetime, timezone
from pathlib import Path

from scrapcore.core import Core
from scrapcore.jobs import CapturedPage, ScrapeJobResult
from serpscrap.config import Config

FIXTURE = Path(__file__).parent / "fixtures" / "google_normal.html"


class FixtureWorkerFactory:
    def __init__(self, html):
        self.html = html

    def execute(self, job):
        pages = tuple(
            CapturedPage(
                query=job.query,
                search_engine=job.search_engine,
                page_number=page,
                url="https://www.google.com/search?q=test",
                html=self.html,
                requested_at=datetime.now(timezone.utc),
            )
            for page in job.pages
        )
        return ScrapeJobResult(job=job, pages=pages)


def test_core_parses_and_persists_captured_pages(tmp_path):
    config = Config().get()
    config.update(
        {
            "keywords": ["serpscrap example"],
            "database_name": str(tmp_path / "serpscrap"),
            "cachedir": str(tmp_path / "cache"),
            "do_caching": False,
            "num_pages_for_keyword": 1,
        }
    )
    factory = FixtureWorkerFactory(FIXTURE.read_text(encoding="utf-8"))

    search = Core(worker_factory=factory).run(config)

    assert len(search.serps) == 1
    assert search.serps[0].query == "serpscrap example"
    assert len(search.serps[0].links) == 2
    assert search.serps[0].links[0].title == "Example Guide"


def test_core_reuses_cached_result_without_browser(tmp_path):
    config = Config().get()
    config.update(
        {
            "keywords": ["cached query"],
            "database_name": str(tmp_path / "serpscrap"),
            "cachedir": str(tmp_path / "cache"),
            "do_caching": True,
        }
    )
    html = FIXTURE.read_text(encoding="utf-8")
    Core(worker_factory=FixtureWorkerFactory(html)).run(config)

    class BrowserMustNotRun:
        def execute(self, job):
            raise AssertionError("cache hit unexpectedly launched Chrome")

    cached_search = Core(worker_factory=BrowserMustNotRun()).run(config)

    assert len(cached_search.serps) == 1
    assert cached_search.serps[0].page_number == 1
    assert cached_search.serps[0].search_engine_name == "google"
