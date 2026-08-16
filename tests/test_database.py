from scrapcore.database import SearchEngineResultsPage


def test_set_values_from_parser_tolerates_missing_snippet_key():
    # A parser result dict may omit optional keys such as 'snippet' (the base
    # Parser builds result dicts only from its configured selectors). Populating
    # the SERP from such a parser must not raise KeyError.
    class _FakeParser:
        num_results_for_query = ""
        num_results = 1
        effective_query = ""
        no_results = False
        search_results = {"results": [{"link": "http://example.com", "rank": 1}]}
        related_keywords = {"related": []}

    serp = SearchEngineResultsPage()
    serp.set_values_from_parser(_FakeParser())  # must not raise KeyError

    assert serp.links[0].link == "http://example.com"
    assert serp.links[0].snippet is None
