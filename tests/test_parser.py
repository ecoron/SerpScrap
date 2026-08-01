from pathlib import Path

from scrapcore.parser.google_parser import GoogleParser
from serpscrap.config import Config

FIXTURE = Path(__file__).parent / "fixtures" / "google_normal.html"


def test_google_parser_extracts_and_normalizes_organic_results():
    parser = GoogleParser(config=Config().get(), query="serpscrap example")

    parser.parse(FIXTURE.read_text(encoding="utf-8"))

    results = parser.search_results["results"]
    assert parser.num_results == 2
    assert parser.num_results_for_query == "About 42 results"
    assert [result["rank"] for result in results] == [1, 2]
    assert results[0]["link"] == "https://example.com/guide"
    assert results[0]["snippet"] == "A deterministic first result snippet."
    assert results[1]["link"] == "https://python.org/"


def test_google_parser_deduplicates_links():
    html = FIXTURE.read_text(encoding="utf-8").replace(
        "https%3A%2F%2Fpython.org%2F", "https%3A%2F%2Fexample.com%2Fguide"
    )
    parser = GoogleParser(config=Config().get())

    parser.parse(html)

    assert parser.num_results == 1
