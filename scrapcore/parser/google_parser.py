# -*- coding: utf-8 -*-
import json
import logging
import re
from urllib.parse import unquote

from scrapcore.parser.parser import Parser

logger = logging.getLogger(__name__)

SELECTORS = {
    "results_container": [
        'div[data-header-feature]',
        'div.g',
        'div[role="main"]',
    ],
    "result": [
        'div.g',                            # Standard-Suchergebnis
        'div[data-header-feature]',         # Featured Snippet & Boxen
        'div[jscontroller]',                # Universal Results/Boxen
        'div[role="heading"]',              # H1/H2 in Boxen
    ],
    "title": [
        'h3',                              # Standard-Titel
        'div[role="heading"]',             # Snippet-Titel
        'span.BNeawe.vvjwJb.AP7Wnd',       # Title in Universal Results
    ],
    "url": [
        'a[jsname="UWckNb"]',              # Hauptlink
        'a[href^="https://"]',             # Standard-Link
        'div > cite',                      # Zitiert-URL/Feature
    ],
    "snippet": [
        'div.VwiC3b',                      # Haupt-Snippet
        'span.aCOpRe',                     # Alternativ-Snippet
        'div[data-header-feature] .VwiC3b' # Featured Snippet Text
    ],
    "nav": 'div[role="navigation"]',       # Seiten-Navigation
    "images": 'g-img',                     # Bilder Boxen
    "videos": 'g-scrolling-carousel',      # Videos Boxen
    "news_box": 'g-card',                  # News Card Boxen
    "shopping_box": 'div[data-attrid="shopping"]',
    "entertainment_box": 'div[data-attrid*="entertainment"]'
}

MD5 = "55198771a3246be6d1715dc4f5fd205a"


class GoogleParser(Parser):
    """Parses SERP pages of the Google search engine for normal and image search types."""

    search_engine = 'google'
    search_types = ['normal', 'image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selectors = SELECTORS

    def get_results_container(self, soup):
        logger.debug("Trying to find results container with selectors: %s", self.selectors["results_container"])
        for selector in self.selectors["results_container"]:
            container = soup.select_one(selector)
            if container:
                logger.debug("Found results container with selector: %s", selector)
                return container
        logger.warning("No results container found.")
        return None

    def get_result_items(self, container):
        logger.debug("Extracting result items from container using selectors: %s", self.selectors["result"])
        items = []
        for selector in self.selectors["result"]:
            found = container.select(selector)
            logger.debug("Selector '%s' found %d items", selector, len(found))
            items.extend(found)
        logger.info("Total result items found: %d", len(items))
        return items

    def extract_title(self, item):
        for selector in self.selectors["title"]:
            el = item.select_one(selector)
            if el:
                logger.debug("Title found with selector: %s", selector)
                return el.get_text(strip=True)
        logger.debug("No title found for item.")
        return None

    def extract_url(self, item):
        for selector in self.selectors["url"]:
            el = item.select_one(selector)
            if el and el.has_attr('href'):
                logger.debug("URL found with selector: %s", selector)
                return el['href']
            elif el and el.name == 'cite':
                logger.debug("Cite URL found with selector: %s", selector)
                return el.get_text(strip=True)
        logger.debug("No URL found for item.")
        return None

    def extract_snippet(self, item):
        for selector in self.selectors["snippet"]:
            el = item.select_one(selector)
            if el:
                logger.debug("Snippet found with selector: %s", selector)
                return el.get_text(strip=True)
        logger.debug("No snippet found for item.")
        return None

    def parse_results(self, soup):
        logger.info("Parsing results from soup object.")
        results = []
        container = self.get_results_container(soup)
        if not container:
            logger.warning("No results container found. Returning empty results.")
            return results
        for item in self.get_result_items(container):
            title = self.extract_title(item)
            url = self.extract_url(item)
            snippet = self.extract_snippet(item)
            if title or url or snippet:
                logger.debug("Appending result: title=%s, url=%s", title, url)
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet
                })
        logger.info("Total parsed results: %d", len(results))
        return results

    def after_parsing(self):
        """Clean and normalize Google SERP result URLs and handle no-results logic."""
        super().after_parsing()
        if self.searchtype == 'normal':
            self.no_results = self.num_results <= 0
            if 'No results found for' in self.html or 'did not match any documents' in self.html:
                self.no_results = True
            if self.no_results:
                for key, i in self.iter_serp_items():
                    snippet = self.search_results[key][i].get('snippet')
                    if snippet and self.query and self.query.replace('"', '') in snippet:
                        self.no_results = False
        if self.searchtype == 'image':
            for key, i in self.iter_serp_items():
                if self.search_results[key][i]:
                    meta_dict = json.loads(self.search_results[key][i]['snippet'])
                    rank = self.search_results[key][i]['rank']
                    self.search_results[key][i] = {
                        'link': meta_dict.get('ou'),
                        'snippet': meta_dict.get('s'),
                        'title': meta_dict.get('pt'),
                        'visible_link': meta_dict.get('isu'),
                        'rating': None,
                        'sitelinks': None,
                        'rank': rank
                    }
        clean_regexes = {
            'normal': r'/url\\?q=(?P<url>.*?)&sa=U&ei=',
            'image': r'imgres\\?imgurl=(?P<url>.*?)&'
        }
        for key, i in self.iter_serp_items():
            link = self.search_results[key][i].get('link')
            if link:
                result = re.search(clean_regexes[self.searchtype], link)
                if result:
                    self.search_results[key][i]['link'] = unquote(result.group('url'))
