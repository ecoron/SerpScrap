"""In-tree News and Shopping MVP adapters."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

import lxml.html

from serpscrap.plugins.searchengines.base import SearchEnginePlugin
from serpscrap.topics import TopicCapabilities, TopicPlugin, TopicRequest, TopicResult


def _text(node: ET.Element | None) -> str | None:
    return " ".join("".join(node.itertext()).split()) if node is not None else None


class SearchTopicPlugin(TopicPlugin):
    """Compatibility view of an existing SearchEnginePlugin."""

    topic_id = "search"
    display_name = "Web Search"
    capabilities = TopicCapabilities(transport="browser", pagination="page")

    def __init__(self, engine: SearchEnginePlugin) -> None:
        self.engine = engine

    def build_url(self, request: TopicRequest, *, page: int) -> str:
        return self.engine.build_url(request.query, page, request.country or "", "normal")

    def parse(self, payload: str, *, request: TopicRequest, page: int) -> list[TopicResult]:
        return [
            TopicResult(
                item.url,
                item.title or "",
                item.snippet,
                item.source or self.engine.engine_id,
                item.rank,
                extras={"result_type": item.result_type, **item.extras},
            )
            for item in self.engine.parse(
                payload, query=request.query, page=page, search_type="normal"
            )
        ]


class NewsSourcePlugin(TopicPlugin):
    topic_id = "news"
    display_name = "News"
    capabilities = TopicCapabilities(transport="feed", pagination="none")

    def build_url(self, request: TopicRequest, *, page: int) -> str:
        custom_feed = next(
            (source for source in request.sources if source.startswith(("http://", "https://"))),
            None,
        )
        return (
            custom_feed
            if custom_feed
            else "https://news.google.com/rss/search?q=" + request.query.replace(" ", "+")
        )

    def parse(self, payload: str, *, request: TopicRequest, page: int) -> list[TopicResult]:
        root = ET.fromstring(payload)
        rows: list[TopicResult] = []
        for item in root.findall(".//item") + root.findall(".//{*}entry"):
            title = _text(item.find("title"))
            link = item.findtext("link") or ""
            if not link:
                link_node = item.find("{*}link")
                link = link_node.get("href", "") if link_node is not None else ""
            if not title or not link:
                continue
            raw_date = (
                item.findtext("pubDate")
                or item.findtext("{*}published")
                or item.findtext("{*}updated")
            )
            published = None
            if raw_date:
                try:
                    published = parsedate_to_datetime(raw_date)
                except (TypeError, ValueError):
                    try:
                        published = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    except ValueError:
                        pass
            if published and published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            if request.since and published and published < request.since:
                continue
            if request.until and published and published > request.until:
                continue
            source = item.findtext("source") or item.findtext("{*}source")
            rows.append(
                TopicResult(
                    link,
                    title,
                    _text(item.find("description")),
                    source,
                    len(rows) + 1,
                    published,
                    _text(item.find("{*}creator")),
                    language=request.language,
                )
            )
        return rows


class ConfiguredNewsSourcePlugin(NewsSourcePlugin):
    """A named public RSS source for the News topic."""

    source_id = ""
    display_name = ""
    feed_url = ""

    def build_url(self, request: TopicRequest, *, page: int) -> str:
        return self.feed_url


class AnsaNewsPlugin(ConfiguredNewsSourcePlugin):
    source_id = "ansa"
    display_name = "ANSA"
    feed_url = "https://www.ansa.it/english/news/english_nr_rss.xml"
    capabilities = TopicCapabilities(transport="feed", pagination="none")


class DeutscheWelleNewsPlugin(ConfiguredNewsSourcePlugin):
    source_id = "dw"
    display_name = "Deutsche Welle"
    feed_url = "https://rss.dw.com/rdf/rss-de-all"
    capabilities = TopicCapabilities(transport="feed", pagination="none")


class EuronewsNewsPlugin(ConfiguredNewsSourcePlugin):
    source_id = "euronews"
    display_name = "Euronews"
    feed_url = "https://www.euronews.com/rss?format=mrss&level=theme&name=news"
    capabilities = TopicCapabilities(transport="feed", pagination="none")


class France24NewsPlugin(ConfiguredNewsSourcePlugin):
    source_id = "france24"
    display_name = "France 24"
    feed_url = "https://www.france24.com/en/rss"
    capabilities = TopicCapabilities(transport="feed", pagination="none")


class LeMondeNewsPlugin(ConfiguredNewsSourcePlugin):
    source_id = "lemonde"
    display_name = "Le Monde"
    feed_url = "https://www.lemonde.fr/en/europe/rss_full.xml"
    capabilities = TopicCapabilities(transport="feed", pagination="none")


class GuardianNewsPlugin(ConfiguredNewsSourcePlugin):
    source_id = "guardian"
    display_name = "The Guardian"
    feed_url = "https://www.theguardian.com/world/europe-news/rss"
    capabilities = TopicCapabilities(transport="feed", pagination="none")


class ShoppingSourcePlugin(TopicPlugin):
    """Base contract for public shopping search result pages."""

    topic_id = "shopping"
    display_name = "Shopping"
    source_id = "shopping"
    capabilities = TopicCapabilities(transport="browser", pagination="page")
    search_url = ""
    card_selectors = ("article", "li", "div")
    title_selectors = ("h2", "h3", "h4", "[data-testid*='title']")

    def build_url(self, request: TopicRequest, *, page: int) -> str:
        values = self.query_parameters(request, page=page)
        return f"{self.search_url}?{urlencode(values)}"

    def query_parameters(self, request: TopicRequest, *, page: int) -> dict[str, str | int]:
        return {"q": request.query, "page": page}

    def parse(self, payload: str, *, request: TopicRequest, page: int) -> list[TopicResult]:
        if not payload:
            return []
        dom = lxml.html.fromstring(payload)
        rows: list[TopicResult] = []
        seen: set[str] = set()
        for selector in self.card_selectors:
            cards = dom.cssselect(selector)
            for card in cards:
                anchor = next((item for item in card.cssselect("a[href]") if item.get("href", "").startswith(("http://", "https://"))), None)
                title_node = next((item for title_selector in self.title_selectors for item in card.cssselect(title_selector)), anchor)
                if anchor is None:
                    continue
                url = anchor.get("href", "").strip()
                title = _html_text(title_node.text_content())
                if not title or url in seen:
                    continue
                seen.add(url)
                text = _html_text(card.text_content())
                snippet = _card_snippet(card, text, title)
                price = _price(text)
                rows.append(TopicResult(url, title, snippet, self.display_name, len(rows) + 1, extras={
                    "price": price,
                    "currency": _currency(price),
                    "availability": "in_stock" if re.search(r"in stock|auf lager|sofort lieferbar", text, re.I) else None,
                    "merchant": _merchant(card, text),
                    "source_id": self.source_id,
                }))
            if rows:
                break
        return rows


class GeizhalsShoppingPlugin(ShoppingSourcePlugin):
    source_id = "geizhals"
    display_name = "Geizhals"
    search_url = "https://geizhals.de/"
    card_selectors = ("article", "div.productlist__item", "div[class*='product']", "li")

    def query_parameters(self, request: TopicRequest, *, page: int) -> dict[str, str | int]:
        return {"fs": request.query, "page": page}


class IdealoShoppingPlugin(ShoppingSourcePlugin):
    source_id = "idealo"
    display_name = "idealo"
    search_url = "https://www.idealo.de/preisvergleich/MainSearchProductCategory.html"
    card_selectors = ("article", "div[class*='offer']", "div[class*='product']", "li")

    def query_parameters(self, request: TopicRequest, *, page: int) -> dict[str, str | int]:
        return {"q": request.query, "page": page}


class BilligerShoppingPlugin(ShoppingSourcePlugin):
    source_id = "billiger"
    display_name = "billiger.de"
    search_url = "https://www.billiger.de/search"
    card_selectors = ("article", "div[class*='product']", "div[class*='offer']", "li")

    def query_parameters(self, request: TopicRequest, *, page: int) -> dict[str, str | int]:
        return {"searchTerm": request.query, "page": page}


class _LocalizedShoppingPlugin(ShoppingSourcePlugin):
    """Shopping page source whose public host follows the requested market."""

    locales = {"DE": "de", "AT": "at", "FR": "fr", "IT": "it", "ES": "es", "NL": "nl", "PL": "pl"}

    def market_code(self, request: TopicRequest) -> str:
        return str(request.filters.get("marketplace") or request.country or "DE").upper()


class FruugoShoppingPlugin(_LocalizedShoppingPlugin):
    source_id = "fruugo"
    display_name = "Fruugo"
    capabilities = TopicCapabilities(transport="browser", pagination="page", supported_countries=frozenset({"AT", "DE", "ES", "FR", "IT", "NL", "PL"}))
    card_selectors = ("article", "div[class*='product']", "div[class*='Product']", "li")

    def build_url(self, request: TopicRequest, *, page: int) -> str:
        locale = self.locales.get(self.market_code(request), "de")
        return f"https://www.fruugo.{locale}/search?{urlencode({'q': request.query, 'page': page})}"


class KauflandShoppingPlugin(_LocalizedShoppingPlugin):
    source_id = "kaufland"
    display_name = "Kaufland Marketplace"
    capabilities = TopicCapabilities(transport="browser", pagination="page", supported_countries=frozenset({"AT", "CZ", "DE", "ES", "FR", "IT", "NL", "PL", "SK"}))
    card_selectors = ("article", "div[class*='product']", "div[class*='offer']", "li")

    def build_url(self, request: TopicRequest, *, page: int) -> str:
        locale = self.locales.get(self.market_code(request), "de")
        return f"https://www.kaufland.{locale}/search?{urlencode({'search_value': request.query, 'page': page})}"


class AllegroShoppingPlugin(_LocalizedShoppingPlugin):
    source_id = "allegro"
    display_name = "Allegro"
    capabilities = TopicCapabilities(transport="browser", pagination="page", supported_countries=frozenset({"CZ", "HU", "PL", "SK"}))
    locales = {"PL": "pl", "CZ": "cz", "SK": "sk", "HU": "hu"}
    card_selectors = ("article", "div[class*='listing']", "div[class*='offer']", "li")

    def build_url(self, request: TopicRequest, *, page: int) -> str:
        locale = self.locales.get(self.market_code(request), "pl")
        return f"https://allegro.{locale}/listing?{urlencode({'string': request.query, 'p': page})}"


class EtsyShoppingPlugin(ShoppingSourcePlugin):
    source_id = "etsy"
    display_name = "Etsy"
    search_url = "https://www.etsy.com/search"
    card_selectors = ("li.wt-list-unstyled", "article", "div[data-search-results-container] li", "li")

    def query_parameters(self, request: TopicRequest, *, page: int) -> dict[str, str | int]:
        return {"q": request.query, "page": page}


def _html_text(value: str) -> str:
    return " ".join(value.split())


def _card_snippet(card: lxml.html.HtmlElement, text: str, title: str) -> str | None:
    """Extract a short safe excerpt without fetching product detail pages."""
    for selector in (
        "meta[name='description']",
        "meta[property='og:description']",
        "[class*='snippet']",
        "[class*='description']",
        "p",
    ):
        for node in card.cssselect(selector):
            value = node.get("content") if node.tag == "meta" else node.text_content()
            value = _html_text(value or "")
            if value and value.lower() != title.lower():
                return value[:320]
    fallback = _html_text(text)
    if title and fallback.lower().startswith(title.lower()):
        fallback = fallback[len(title):].strip(" ·-|:")
    return fallback[:320] or None


def _price(value: str) -> str | None:
    match = re.search(r"(?:€|\$|£)\s?[\d.]+(?:[,\.]\d{2})?|[\d.]+[,\.]\d{2}\s?(?:EUR|USD|GBP)", value, re.I)
    return match.group(0) if match else None


def _merchant(card: lxml.html.HtmlElement, text: str) -> str | None:
    for selector in ("[class*='merchant']", "[class*='seller']", "[class*='shop']"):
        node = next(iter(card.cssselect(selector)), None)
        if node is not None and _html_text(node.text_content()):
            return _html_text(node.text_content())
    return None


def _currency(value: str | None) -> str | None:
    if not value:
        return None
    return {"€": "EUR", "$": "USD", "£": "GBP"}.get(
        value.strip()[0],
        re.search(r"\b(EUR|USD|GBP)\b", value, re.I).group(1).upper()
        if re.search(r"\b(EUR|USD|GBP)\b", value, re.I)
        else None,
    )
