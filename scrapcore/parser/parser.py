# -*- coding: utf-8 -*-
import logging
import pprint
import re

from cssselect import HTMLTranslator
import lxml.html
from lxml.html.clean import Cleaner


logger = logging.getLogger(__name__)


class Parser:
    """Base parser for extracting SERP data from HTML using configurable selectors."""

    no_results_selector = []
    effective_query_selector = []
    num_results_search_selectors = []
    page_number_selectors = []
    search_types = []

    def __init__(self, config: dict = {}, html: str = '', query: str = ''):
        """Create new Parser instance and parse all information."""
        self.config = config
        self.searchtype = self.config.get('search_type', 'normal')
        assert self.searchtype in self.search_types, (
            f'search type "{self.searchtype}" is not supported in {self.__class__.__name__}'
        )
        self.query = query
        self.html = html
        self.dom = None
        self.search_results = {}
        self.num_results_for_query = ''
        self.num_results = 0
        self.effective_query = ''
        self.page_number = -1
        self.no_results = False
        self.related_keywords = {}
        self.search_engine = ''
        self.css_to_xpath = HTMLTranslator().css_to_xpath
        if self.html:
            self.parse()

    def parse(self, html: str = None):
        """Start parsing the search engine results."""
        if html:
            self.html = html.encode('utf-8').decode('utf-8')
        self._parse()
        self.after_parsing()

    def _parse_lxml(self, cleaner=None):
        try:
            parser = lxml.html.HTMLParser(encoding='utf-8')
            if cleaner:
                self.dom = cleaner.clean_html(self.dom)
            self.dom = lxml.html.document_fromstring(self.html, parser=parser)
            self.dom.resolve_base_href()
        except Exception as e:
            logger.error(e)

    def _parse(self, cleaner=None):
        """Internal: parse the DOM according to the provided CSS selectors."""
        self.num_results = 0
        self._parse_lxml(cleaner)
        attr_name = self.searchtype + '_search_selectors'
        selector_dict = getattr(self, attr_name, None)
        num_results_selector = getattr(self, 'num_results_search_selectors', None)
        self.num_results_for_query = self.first_match(num_results_selector, self.dom)
        if not self.num_results_for_query:
            logger.debug(f'{self.__class__.__name__}: Cannot parse num_results from serp page with selectors {num_results_selector}')
        try:
            self.page_number = int(self.first_match(self.page_number_selectors, self.dom))
        except ValueError:
            self.page_number = -1
        self.effective_query = self.first_match(self.effective_query_selector, self.dom)
        if self.effective_query:
            logger.debug(f'{self.__class__.__name__}: There was no search hit for the search query. Search engine used {self.effective_query} instead.')
        else:
            self.effective_query = ''
        self.no_results_text = self.first_match(self.no_results_selector, self.dom)
        if not selector_dict or not isinstance(selector_dict, dict):
            raise Exception(f'There is no such attribute: {attr_name}. No selectors found')
        for result_type, selector_class in selector_dict.items():
            self.search_results[result_type] = []
            self.related_keywords[result_type] = []
            for _, selectors in selector_class.items():
                if 'result_container' in selectors and selectors['result_container']:
                    css = f"{selectors['container']} {selectors['result_container']}"
                else:
                    css = selectors['container']
                results = self.dom.xpath(self.css_to_xpath(css))
                to_extract = set(selectors.keys()) - {'container', 'result_container'}
                selectors_to_use = {key: selectors[key] for key in to_extract if key in selectors}
                for index, result in enumerate(results):
                    serp_result = {}
                    for key, selector in selectors_to_use.items():
                        serp_result[key] = self.advanced_css(selector, result)
                    serp_result['rank'] = index + 1
                    if 'link' in serp_result and serp_result['link'] and not any(e['link'] == serp_result['link'] for e in self.search_results[result_type]):
                        self.search_results[result_type].append(serp_result)
                        self.num_results += 1
                    if 'keyword' in serp_result and serp_result['keyword']:
                        self.related_keywords[result_type].append(serp_result)

    def advanced_css(self, selector: str, element) -> str:
        """Evaluate :text and ::attr(attr-name) selectors."""
        value = None
        if selector.endswith('::text'):
            try:
                value = element.xpath(self.css_to_xpath(selector.split('::')[0]))[0].text_content()
            except IndexError:
                pass
        else:
            match = re.search(r'::attr\((?P<attr>.*)\)$', selector)
            if match:
                attr = match.group('attr')
                try:
                    value = element.xpath(self.css_to_xpath(selector.split('::')[0]))[0].get(attr)
                except IndexError:
                    pass
            else:
                try:
                    value = element.xpath(self.css_to_xpath(selector))[0].text_content()
                except IndexError:
                    pass
        return value

    def first_match(self, selectors: list, element) -> str:
        """Get the first match from a list of selectors."""
        assert isinstance(selectors, list), 'selectors must be of type list!'
        for selector in selectors:
            if selector:
                try:
                    match = self.advanced_css(selector, element=element)
                    if match:
                        return match
                except IndexError:
                    pass
        return False

    def after_parsing(self):
        """Subclass-specific behaviour after parsing happened. Override in subclass."""

    def __str__(self):
        """Return a nicely formatted overview of the results."""
        return pprint.pformat(self.search_results)

    @property
    def cleaned_html(self):
        """Return cleaned HTML with unnecessary elements removed."""
        cleaner = Cleaner()
        cleaner.scripts = True
        cleaner.javascript = True
        cleaner.comments = True
        cleaner.style = True
        self.dom = cleaner.clean_html(self.dom)
        assert len(self.dom), 'The html needs to be parsed to get the cleaned html'
        return lxml.html.tostring(self.dom)

    def iter_serp_items(self):
        """Yields the key and index of any item in the serp results that has a link value."""
        for key, value in self.search_results.items():
            if isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict) and item.get('link'):
                        yield (key, i)
