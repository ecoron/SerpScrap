"""Offline Google SERP parser with ordered selector fallbacks."""

from __future__ import annotations

import logging
from urllib.parse import parse_qs, unquote, urlparse

import lxml.html

from scrapcore.parser.parser import Parser

logger = logging.getLogger(__name__)


class GoogleParser(Parser):
    """Parse normal and image Google result pages without a WebDriver dependency."""

    search_engine = "google"
    search_types = ["normal", "image"]
    result_container_selectors = (
        "#search div.MjjYud",
        "#search div.g",
        "#rso div.MjjYud",
        "#rso div.g",
    )
    snippet_selectors = (".VwiC3b", ".aCOpRe", "[data-sncf]", ".IsZvec")
    result_stats_selectors = ("#result-stats", "#resultStats")

    def parse(self, html: str | None = None) -> None:
        if html is not None:
            self.html = html
        self.search_results = {"results": []}
        self.related_keywords = {"related": []}
        self.num_results = 0
        self.num_results_for_query = ""
        self.effective_query = ""
        self.page_number = -1
        self.no_results = False
        if not self.html:
            self.dom = None
            return

        parser = lxml.html.HTMLParser(encoding="utf-8")
        self.dom = lxml.html.document_fromstring(self.html, parser=parser)
        if self.searchtype == "image":
            self._parse_images()
        else:
            self._parse_normal()
        self.no_results = self.num_results == 0
        html_lower = self.html.lower()
        if "did not match any documents" in html_lower or "no results found for" in html_lower:
            self.no_results = True

    def _select_first_text(self, element, selectors: tuple[str, ...]) -> str | None:
        for selector in selectors:
            matches = element.cssselect(selector)
            if matches:
                text = " ".join(matches[0].text_content().split())
                if text:
                    return text
        return None

    def _normal_result_nodes(self) -> list:
        for selector in self.result_container_selectors:
            nodes = self.dom.cssselect(selector)
            candidates = [node for node in nodes if node.cssselect("h3")]
            if candidates:
                return candidates
        return self.dom.xpath("//a[.//h3]/ancestor::div[1]")

    @staticmethod
    def _normalize_url(href: str | None) -> str | None:
        if not href or href.startswith(("javascript:", "#")):
            return None
        if href.startswith("/url?"):
            params = parse_qs(urlparse(href).query)
            href = (params.get("q") or params.get("url") or [None])[0]
        if not href:
            return None
        href = unquote(href)
        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"}:
            return None
        if parsed.netloc.endswith("google.com") and parsed.path.startswith("/search"):
            return None
        return href

    def _parse_normal(self) -> None:
        stats = self._select_first_text(self.dom, self.result_stats_selectors)
        self.num_results_for_query = stats or ""
        seen: set[str] = set()
        for node in self._normal_result_nodes():
            headings = node.cssselect("h3")
            if not headings:
                continue
            anchors = headings[0].xpath("ancestor::a[1]") or node.cssselect("a[href]")
            href = self._normalize_url(anchors[0].get("href") if anchors else None)
            if not href or href in seen:
                continue
            seen.add(href)
            title = " ".join(headings[0].text_content().split())
            snippet = self._select_first_text(node, self.snippet_selectors)
            visible = self._select_first_text(node, ("cite",))
            self.search_results["results"].append(
                {
                    "link": href,
                    "title": title,
                    "snippet": snippet,
                    "visible_link": visible,
                    "rating": None,
                    "sitelinks": None,
                    "rank": len(seen),
                }
            )
        self.num_results = len(self.search_results["results"])

    def _parse_images(self) -> None:
        seen: set[str] = set()
        for anchor in self.dom.cssselect('a[href*="imgres?"]'):
            params = parse_qs(urlparse(anchor.get("href", "")).query)
            href = (params.get("imgurl") or [None])[0]
            href = self._normalize_url(href)
            if not href or href in seen:
                continue
            seen.add(href)
            image = anchor.cssselect("img")
            title = image[0].get("alt") if image else None
            self.search_results["results"].append(
                {
                    "link": href,
                    "title": title,
                    "snippet": None,
                    "visible_link": urlparse(href).netloc,
                    "rating": None,
                    "sitelinks": None,
                    "rank": len(seen),
                }
            )
        self.num_results = len(self.search_results["results"])
