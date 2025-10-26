# -*- coding: utf-8 -*-
import json
import logging
import re
from urllib.parse import unquote

from scrapcore.parser.parser import Parser

logger = logging.getLogger(__name__)


class GoogleParser(Parser):
    """Parses SERP pages of the Google search engine for normal and image search types."""

    search_engine = 'google'

    search_types = ['normal', 'image']

    effective_query_selector = [
        '#topstuff .med > b::text', '.med > a > b::text'
    ]

    no_results_selector = []

    num_results_search_selectors = ['#resultStats']

    page_number_selectors = ['div#foot div#navcnt td.cur::text']

    normal_search_selectors = {
        'results': {
            'items': {
                'container': '#center_col',
                'result_container': 'div.g',
                'link': 'div.r > a:first-of-type::attr(href)',
                'snippet': 'div.s span.st::text',
                'title': 'div.r > a:first-of-type::text',
                'visible_link': 'cite::text',
                'rating': 'div.f.slp::text',
                'sitelinks': 'div.osl::text'
            },
        },
        'videos': {
            'video_items': {
                'container': 'g-inner-card',
                'result_container': 'div.y8AWGd',
                'link': 'div.y8AWGd a::attr(href)',
                'snippet': 'div.y8AWGd::text',
                'title': 'div.y8AWGd::text',
                'visible_link': 'div.y8AWGd cite::text',
                'rating': 'div.osl a:first-of-type::text',
                'sitelinks': 'div.osl::text'
            },
        },
        'news': {
            'news_items': {
                'container': 'g-scrolling-carousel',
                'result_container': 'div.So9e7d',
                'link': 'div.So9e7d a::attr(href)',
                'snippet': 'div.So9e7d::text',
                'title': 'div.So9e7d div.Igo7ld::text',
                'visible_link': 'div.So9e7d cite::text',
                'rating': 'div.osl a:first-of-type::text',
                'sitelinks': 'div.osl::text'
            },
        },
        'shopping': {
            'shopping_items_main': {
                'container': 'div.top-pla-group-inner',
                'result_container': 'div.mnr-c.pla-unit',
                'link': 'div.mnr-c.pla-unit a.pla-unit-title-link::attr(href)',
                'snippet': 'div.mnr-c.pla-unit::text',
                'title': 'div.mnr-c.pla-unit a.pla-unit-title-link > span::text',
                'visible_link': 'a.FfKHB::attr(href)',
                'rating': 'xxxx',
                'sitelinks': 'a.FfKHB > span::text'
            },
            'shopping_items_side': {
                'container': 'div.cu-container',
                'result_container': 'div.mnr-c.pla-unit',
                'link': 'div.mnr-c.pla-unit a.pla-unit-title-link::attr(href)',
                'snippet': 'div.mnr-c.pla-unit::text',
                'title': 'div.mnr-c.pla-unit a.pla-unit-title-link > span::text',
                'visible_link': 'a.FfKHB::attr(href)',
                'rating': 'xxxx',
                'sitelinks': 'a.FfKHB > span::text'
            },
        },
        'ads_main': {
            'ads_item': {
                'container': '#center_col',
                'result_container': '.ads-ad',
                'link': 'div.ad_cclk > a:nth-child(2)::attr(href)',
                'snippet': 'div.ads-creative::text',
                'title': 'div.ad_cclk > a:nth-child(2)::text',
                'visible_link': '.ads-visurl cite::text',
                'rating': 'div.xyt0c span::text',
                'sitelinks': 'ul.OkkX2d::text'
            }
        },
        'related_keywords': {
            'related_items': {
                'container': 'div.card-section',
                'result_container': 'p.nVcaUb',
                'keyword': 'a::text'
            }
        }
    }

    image_search_selectors = {
        'image': {
            'de_ip': {
                'container': '#isr_mc div.rg_di',
                # 'result_container': 'div.rg_di',
                'snippet': 'div.rg_di > div.rg_meta',
                'link': 'a.rg_l::attr(href)'
            },
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
