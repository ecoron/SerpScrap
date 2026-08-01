"""Public SerpScrap API."""

from __future__ import annotations

import argparse

from scrapcore.core import Core
from serpscrap.config import Config
from serpscrap.csv_writer import CsvWriter
from serpscrap.urlscrape import UrlScrape


class SerpScrap:
    """Execute SERP and optional result-URL scrape tasks."""

    def __init__(self) -> None:
        self.args = []
        self.serp_query: list[str] | None = None
        self.results: list[dict] = []
        self.related: list[dict] = []
        self.config: dict | None = None

    def cli(self, args=None):
        parser = argparse.ArgumentParser(prog="serpscrap")
        parser.add_argument("-k", "--keyword", help="keyword for scraping", nargs="+")
        self.args = parser.parse_args(args)
        if not self.args.keyword:
            raise ValueError("No keywords provided via CLI")
        self.init(keywords=" ".join(self.args.keyword))
        return self.run()

    def init(self, config: dict | None = None, keywords=None) -> None:
        """Initialize configuration and queries without starting a browser."""

        merged = Config()
        if config is not None:
            merged.apply(config)
        self.config = merged.get()
        if isinstance(keywords, str) and keywords.strip():
            self.serp_query = [keywords.strip()]
        elif isinstance(keywords, (list, tuple)) and keywords:
            self.serp_query = [str(keyword).strip() for keyword in keywords if str(keyword).strip()]
        else:
            raise ValueError("No keywords given")
        if not self.serp_query:
            raise ValueError("No non-empty keywords given")

    def run(self) -> list[dict]:
        if self.config is None or self.serp_query is None:
            raise RuntimeError("Call init() before run()")
        self.results = self.scrap_serps()
        if self.config.get("scrape_urls"):
            for index, result in enumerate(self.results):
                url = result.get("serp_url")
                if url:
                    self.results[index].update(self.scrap_url(url))
        return self.results

    def as_csv(self, file_path: str) -> None:
        self.results = self.run()
        CsvWriter().write(file_path + ".csv", self.results)

    def scrap_serps(self) -> list[dict]:
        search = self.scrap()
        results: list[dict] = []
        self.related = []
        for serp in getattr(search, "serps", []):
            for related_keyword in getattr(serp, "related_keywords", []):
                self.related.append(
                    {"keyword": related_keyword.keyword, "rank": related_keyword.rank}
                )
            for link in getattr(serp, "links", []):
                results.append(
                    {
                        "query_num_results_total": serp.num_results_for_query or "",
                        "query_num_results_page": serp.num_results,
                        "query_page_number": serp.page_number,
                        "query": serp.query,
                        "serp_rank": link.rank,
                        "serp_type": link.link_type,
                        "serp_url": link.link,
                        "serp_rating": link.rating,
                        "serp_title": link.title,
                        "serp_domain": link.domain,
                        "serp_visible_link": link.visible_link,
                        "serp_snippet": link.snippet,
                        "serp_sitelinks": link.sitelinks,
                        "screenshot": getattr(serp, "screenshot", None),
                    }
                )
        self.results = results
        return results

    def scrap(self):
        if self.config is None or self.serp_query is None:
            raise RuntimeError("Call init() before scrap()")
        self.config["keywords"] = list(self.serp_query)
        return Core().run(self.config)

    def scrap_url(self, url: str):
        if self.config is None:
            raise RuntimeError("Call init() before scrap_url()")
        return UrlScrape(self.config).scrap_url(url)

    def get_related(self) -> list[dict]:
        return self.related
