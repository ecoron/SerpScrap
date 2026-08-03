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
    search_types = ["normal", "image", "news", "shopping", "videos"]
    result_container_selectors = (
        "#search div.MjjYud",
        "#search div.g",
        "#rso div.MjjYud",
        "#rso div.g",
    )
    snippet_selectors = (".VwiC3b", ".aCOpRe", "[data-sncf]", ".IsZvec")
    result_stats_selectors = ("#result-stats", "#resultStats")
    specialized_selectors = {
        "image": ("[data-serp-type='image']", "[data-image-url]"),
        "news": ("[data-serp-type='news']", "[data-news-url]", "div.SoaBEf"),
        "shopping": (
            "[data-serp-type='shopping']",
            "[data-product-url]",
            ".sh-dgr__grid-result",
            ".pla-unit",
        ),
        "videos": (
            "[data-serp-type='videos']",
            "[data-serp-type='video']",
            "[data-video-url]",
        ),
    }

    def parse(self, html: str | None = None) -> None:
        if html is not None:
            self.html = html
        self.search_results = {
            "results": [],
            "image": [],
            "news": [],
            "shopping": [],
            "videos": [],
        }
        self.related_keywords = {"related": []}
        self.num_results = 0
        self.num_results_for_query = ""
        self.effective_query = ""
        self.page_number = -1
        self.no_results = False
        self.unsupported_result_types: list[str] = []
        if not self.html:
            self.dom = None
            return

        parser = lxml.html.HTMLParser(encoding="utf-8")
        self.dom = lxml.html.document_fromstring(self.html, parser=parser)
        documented = {"news", "shopping", "videos", "video", "image", "results"}
        self.unsupported_result_types = sorted(
            {
                value
                for value in self.dom.xpath("//*[@data-serp-type]/@data-serp-type")
                if value not in documented
            }
        )
        if self.unsupported_result_types:
            logger.warning(
                "Unsupported Google result modules: %s",
                ", ".join(self.unsupported_result_types),
            )
        if self.searchtype == "image":
            self._parse_images()
        elif self.searchtype in self.specialized_selectors:
            self._parse_specialized(self.searchtype)
        else:
            self._parse_normal()
        self._deduplicate_across_types()
        self.num_results = sum(len(items) for items in self.search_results.values())
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
            candidates = [
                node
                for node in nodes
                if node.cssselect("h3") and not node.xpath("ancestor-or-self::*[@data-serp-type]")
            ]
            if candidates:
                return candidates
        return [
            node
            for node in self.dom.xpath("//a[.//h3]/ancestor::div[1]")
            if not node.xpath("ancestor-or-self::*[@data-serp-type]")
        ]

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
                self._result(href, title, snippet, visible, len(seen))
            )
        for result_type in self.specialized_selectors:
            self._parse_specialized(result_type)
        self.num_results = sum(len(items) for items in self.search_results.values())

    @staticmethod
    def _attribute_or_text(node, attribute: str, selectors: tuple[str, ...]) -> str | None:
        value = node.get(attribute)
        if value:
            return " ".join(value.split())
        for selector in selectors:
            matches = node.cssselect(selector)
            if matches:
                value = " ".join(matches[0].text_content().split())
                if value:
                    return value
        return None

    @staticmethod
    def _result(
        href: str,
        title: str | None,
        snippet: str | None,
        visible_link: str | None,
        rank: int,
        **values,
    ) -> dict:
        result = {
            "link": href,
            "title": title,
            "snippet": snippet,
            "visible_link": visible_link,
            "rating": None,
            "sitelinks": None,
            "rank": rank,
            "source": None,
            "published_at": None,
            "price": None,
            "merchant": None,
            "duration": None,
            "image_url": None,
            "thumbnail_url": None,
        }
        result.update(values)
        return result

    def _nodes_for_type(self, result_type: str) -> list:
        seen: set[int] = set()
        nodes = []
        for selector in self.specialized_selectors[result_type]:
            for node in self.dom.cssselect(selector):
                identity = id(node)
                if identity not in seen:
                    seen.add(identity)
                    nodes.append(node)
        return nodes

    def _parse_specialized(self, result_type: str) -> None:
        results = self.search_results[result_type]
        seen = {item["link"] for item in results}
        for node in self._nodes_for_type(result_type):
            headings = node.cssselect("h3, [role='heading']")
            anchors = (headings[0].xpath("ancestor::a[1]") if headings else []) or node.cssselect(
                "a[href]"
            )
            raw_href = (
                node.get("data-image-url")
                or node.get("data-news-url")
                or node.get("data-product-url")
                or node.get("data-video-url")
                or node.get("data-url")
                or (anchors[0].get("href") if anchors else None)
            )
            href = self._normalize_url(raw_href)
            if not href or href in seen:
                continue
            seen.add(href)
            title = self._attribute_or_text(node, "data-title", ("h3", "[role='heading']"))
            snippet = self._attribute_or_text(node, "data-snippet", self.snippet_selectors)
            visible = self._attribute_or_text(node, "data-visible-link", ("cite",))
            values = {
                "source": self._attribute_or_text(node, "data-source", (".source",)),
                "published_at": self._attribute_or_text(node, "data-date", ("time", ".date")),
                "price": self._attribute_or_text(node, "data-price", (".price",)),
                "merchant": self._attribute_or_text(node, "data-merchant", (".merchant",)),
                "duration": self._attribute_or_text(node, "data-duration", (".duration",)),
            }
            image = node.cssselect("img")
            if image:
                values["thumbnail_url"] = image[0].get("src") or image[0].get("data-src")
            if result_type == "image":
                values["image_url"] = href
            results.append(
                self._result(href, title, snippet, visible, len(results) + 1, **values)
            )
        self.num_results = sum(len(items) for items in self.search_results.values())

    def _deduplicate_across_types(self) -> None:
        seen: set[str] = set()
        for result_type in ("image", "news", "shopping", "videos", "results"):
            unique = []
            for item in self.search_results[result_type]:
                if item["link"] in seen:
                    continue
                seen.add(item["link"])
                item["rank"] = len(unique) + 1
                unique.append(item)
            self.search_results[result_type] = unique

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
            thumbnail = image[0].get("src") if image else None
            self.search_results["image"].append(
                self._result(
                    href,
                    title,
                    None,
                    urlparse(href).netloc,
                    len(seen),
                    image_url=href,
                    thumbnail_url=thumbnail,
                )
            )
        self.num_results = len(self.search_results["image"])
