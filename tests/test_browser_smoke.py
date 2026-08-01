import os

import pytest

from scrapcore.jobs import ScrapeJob
from scrapcore.scraper.selenium import SelScrape
from serpscrap.config import Config


@pytest.mark.browser
@pytest.mark.skipif(
    os.environ.get("SERPSCRAP_RUN_BROWSER") != "1",
    reason="set SERPSCRAP_RUN_BROWSER=1 to run the Chrome/network smoke test",
)
def test_headless_chrome_captures_google_serp():
    config = Config().get()
    config.update({"do_caching": False, "screenshot": False, "wait_timeout": 20})

    result = SelScrape(config, ScrapeJob(query="python programming language")).retrieve()

    assert result.pages, result.failures
    assert "<html" in result.pages[0].html.lower()

