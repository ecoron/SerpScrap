from pathlib import Path

from scrapcore.parser.google_parser import GoogleParser
from serpscrap.config import Config

FIXTURE = Path(__file__).parent / "fixtures" / "google_normal.html"
MIXED_FIXTURE = Path(__file__).parent / "fixtures" / "google_mixed.html"
IMAGE_FIXTURE = Path(__file__).parent / "fixtures" / "google_images.html"


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


def test_google_parser_covers_all_mixed_result_formats():
    parser = GoogleParser(config=Config().get())

    parser.parse(MIXED_FIXTURE.read_text(encoding="utf-8"))

    assert {key: len(value) for key, value in parser.search_results.items()} == {
        "results": 1,
        "image": 1,
        "news": 1,
        "shopping": 1,
        "videos": 1,
    }
    assert parser.search_results["news"][0]["source"] == "Example News"
    assert parser.search_results["image"][0]["image_url"].endswith("result.jpg")
    assert parser.search_results["shopping"][0]["price"] == "EUR 19.99"
    assert parser.search_results["videos"][0]["duration"] == "03:21"


def test_google_image_parser_uses_image_result_contract():
    config = Config().get()
    config["search_type"] = "image"
    parser = GoogleParser(config=config)

    parser.parse(IMAGE_FIXTURE.read_text(encoding="utf-8"))

    assert not parser.search_results["results"]
    assert parser.search_results["image"][0]["image_url"].endswith("cat.jpg")
    assert parser.search_results["image"][0]["thumbnail_url"].endswith("cat.jpg")


def test_google_parser_deduplicates_the_same_url_across_result_types():
    html = """
    <main id="search"><div id="rso">
      <div class="MjjYud"><a href="https://example.com/item"><h3>Organic</h3></a></div>
      <div data-serp-type="news"><a href="https://example.com/item"><h3>News</h3></a></div>
    </div></main>
    """
    parser = GoogleParser(config=Config().get())

    parser.parse(html)

    assert parser.num_results == 1
    assert not parser.search_results["results"]
    assert parser.search_results["news"][0]["title"] == "News"
