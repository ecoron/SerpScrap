from threading import current_thread

import pytest

from serpscrap.models import SearchRequest
from serpscrap.plugins.searchengines.fusion import ResultFusion, canonical_url
from serpscrap.plugins.searchengines.multi import MultiEngineRunner
from serpscrap.plugins.searchengines.registry import default_registry

HTML = """
<html><body><ul>
<li class="result"><h2><a href="https://example.test/a?utm_source=x">Shared</a></h2><p class="snippet">A shared result</p></li>
<li class="result"><h2><a href="https://example.test/b">Only one</a></h2><p class="snippet">A second result</p></li>
</ul></body></html>
"""


def test_registry_contains_google_and_ten_alternatives():
    assert default_registry().ids() == (
        "google", "altpower", "blackle", "kiddle", "kidrex", "poper",
        "bing", "yandex", "yahoo", "duckduckgo", "ecosia",
        "qwant", "startpage", "brave", "swisscows", "mojeek",
        "metager", "good", "xprivo", "marginalia", "etools",
    )


def test_url_canonicalization_removes_tracking_noise_only():
    assert canonical_url("HTTPS://Example.test/a/?utm_source=x&x=1#fragment") == "https://example.test/a?x=1"


def test_fusion_rewards_frequency_and_position_deterministically():
    rows = [
        {"serp_url": "https://example.test/a", "serp_rank": 2, "search_engine": "bing", "country_code": "DE", "query": "q"},
        {"serp_url": "https://example.test/a?utm_medium=x", "serp_rank": 1, "search_engine": "duckduckgo", "country_code": "DE", "query": "q"},
        {"serp_url": "https://example.test/b", "serp_rank": 1, "search_engine": "bing", "country_code": "DE", "query": "q"},
    ]
    ranked = ResultFusion().fuse(rows, {"bing": 0.5, "duckduckgo": 0.5})
    assert ranked[0]["serp_url"] == "https://example.test/a"
    assert ranked[0]["engine_match_count"] == 2
    assert ranked[0]["matched_engines"] == ["bing", "duckduckgo"]


def test_fusion_uses_searxng_upstream_source_for_relevance():
    rows = [
        {"query": "q", "serp_url": "https://example.test", "serp_rank": 1, "search_engine": "searxng", "serp_source": "SearXNG:brave"},
        {"query": "q", "serp_url": "https://example.test", "serp_rank": 5, "search_engine": "searxng", "serp_source": "SearXNG:duckduckgo"},
    ]
    ranked = ResultFusion().fuse(rows, {"brave": 0.8, "duckduckgo": 0.2}, {"brave": "brave", "duckduckgo": "bing"})

    assert ranked[0]["relevance_score"] == pytest.approx(0.8 / 61 + 0.2 / 65)
    assert ranked[0]["matched_engines"] == ["SearXNG:brave", "SearXNG:duckduckgo"]


def test_multi_engine_runner_preserves_provenance_and_partial_failures():
    threads = set()

    def capture(plugin, query, country_code, page, config):
        threads.add(current_thread().name)
        if plugin.engine_id == "yahoo":
            raise RuntimeError("blocked: test block")
        from serpscrap.plugins.searchengines.base import EnginePage

        return EnginePage(
            url=plugin.build_url(query, page, country_code, "normal"),
            html=HTML,
            query=query,
            engine=plugin.engine_id,
            country_code=country_code,
            page=page,
        )

    request = SearchRequest.create(
        "phase four",
        search_engines=["bing", "duckduckgo", "yahoo"],
        country_code="DE",
        num_workers=3,
    )
    report = MultiEngineRunner(capture=capture).execute(request)
    assert report.results
    assert {row["search_engine"] for row in report.results} <= {"bing", "duckduckgo"}
    assert all(row["country_code"] == "DE" for row in report.results)
    assert [row["fusion_rank"] for row in report.results] == list(range(1, len(report.results) + 1))
    assert report.failures[0].search_engine == "yahoo"
    assert len(threads) >= 2
