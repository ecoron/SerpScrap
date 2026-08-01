from datetime import datetime, timezone
from pathlib import Path

from scrapcore.core import Core
from scrapcore.jobs import CapturedPage, ScrapeJobResult
from serpscrap.config import Config

FIXTURE = Path(__file__).parent / "fixtures" / "google_normal.html"
MIXED_FIXTURE = Path(__file__).parent / "fixtures" / "google_mixed.html"


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
            "search_engines": ["google"],
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
            "search_engines": ["google"],
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


def test_core_persists_type_specific_result_fields(tmp_path):
    config = Config().get()
    config.update(
        {
            "keywords": ["mixed query"],
            "search_engines": ["google"],
            "database_name": str(tmp_path / "serpscrap"),
            "cachedir": str(tmp_path / "cache"),
            "do_caching": False,
            "store_history": False,
        }
    )

    search = Core(
        worker_factory=FixtureWorkerFactory(MIXED_FIXTURE.read_text(encoding="utf-8"))
    ).run(config)
    links = {link.link_type: link for link in search.serps[0].links}

    assert links["news"].source == "Example News"
    assert links["shopping"].price == "EUR 19.99"
    assert links["videos"].duration == "03:21"


def test_core_can_disable_persistent_sqlite_history(tmp_path):
    config = Config().get()
    database = tmp_path / "must-not-exist"
    config.update(
        {
            "keywords": ["ephemeral query"],
            "search_engines": ["google"],
            "database_name": str(database),
            "cachedir": str(tmp_path / "cache"),
            "do_caching": False,
            "store_history": False,
        }
    )

    search = Core(worker_factory=FixtureWorkerFactory(FIXTURE.read_text(encoding="utf-8"))).run(
        config
    )

    assert len(search.serps) == 1
    assert not database.with_suffix(".db").exists()


def test_optional_history_failure_preserves_assembled_results(tmp_path):
    class BrokenHistory:
        def persist(self, config, search):
            raise OSError("history disk unavailable")

    config = Config().get()
    config.update(
        {
            "keywords": ["durable result"],
            "search_engines": ["google"],
            "database_name": str(tmp_path / "history"),
            "cachedir": str(tmp_path / "cache"),
            "do_caching": False,
            "store_history": True,
        }
    )
    core = Core(
        worker_factory=FixtureWorkerFactory(FIXTURE.read_text(encoding="utf-8")),
        history_repository=BrokenHistory(),
    )

    search = core.run(config)

    assert len(search.serps[0].links) == 2
    assert search.persistence_failures == ["history disk unavailable"]
