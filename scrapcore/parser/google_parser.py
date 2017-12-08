# -*- coding: utf-8 -*-
import json
import logging
import re
from urllib.parse import unquote

from scrapcore.parser.parser import Parser

logger = logging.getLogger(__name__)


class GoogleParser(Parser):
    """Parses SERP pages of the Google search engine."""

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
            'us_ip': {
                'container': '#center_col',
                'result_container': 'div.g ',
                'link': 'h3.r > a:first-of-type::attr(href)',
                'snippet': 'div.s span.st::text',
                'title': 'h3.r > a:first-of-type::text',
                'visible_link': 'cite::text',
                'rating': 'div.f.slp::text',
                'sitelinks': 'div.osl::text'
            },
            'de_ip': {
                'container': '#center_col',
                'result_container': 'li.g ',
                'link': 'h3.r > a:first-of-type::attr(href)',
                'snippet': 'div.s span.st::text',
                'title': 'h3.r > a:first-of-type::text',
                'visible_link': 'cite::text',
                'rating': 'div.f.slp::text',
                'sitelinks': 'div.osl::text'
            },
        },
        'news': {
            'de_ip_news_items': {
                'container': 'g-inner-card',
                'link': 'g-inner-card a::attr(href)',
                'snippet': 'g-inner-card::text',
                'title': 'g-inner-card div._Jvo::text',
                'visible_link': 'g-inner-card cite::text',
                'rating': 'div.osl a:first-of-type::text',
                'sitelinks': 'div.osl::text'
            },
            'de_ip_othernews_items': {
                'container': 'li.card-section',
                'link': 'a._Dk::attr(href)',
                'snippet': 'span._dwd::text',
                'title': 'a._Dk::text',
                'visible_link': 'cite::text',
                'rating': 'div.osl a:first-of-type::text',
                'sitelinks': 'div.osl::text'
            },
        },
        'shopping': {
            'de_ip_shopping_items': {
                'container': 'div.pla-unit-container',
                'link': 'a.pla-unit-title-link::attr(href)',
                'snippet': 'div.pla-unit-container::text',
                'title': 'a.pla-unit-title-link > span.rhsg4::text',
                'visible_link': 'div._mC > span.rhsg4.a::text',
                'rating': 'div._QD._pvi::text',
                'sitelinks': 'div._zHp > div::text'
            },
            'de_ip_shoppingtop_items': {
                'container': 'g-scrolling-carousel div.pla-unit-container',
                'link': 'g-scrolling-carousel div.pla-unit-container a.pla-unit-title-link::attr(href)',
                'snippet': 'g-scrolling-carousel div.pla-unit-container::text',
                'title': 'g-scrolling-carousel div.pla-unit-container a.pla-unit-title-link::text',
                'visible_link': 'g-scrolling-carousel div.pla-unit-container div._mC::text',
                'rating': 'g-scrolling-carousel div.pla-unit-container div._p2d::text',
                'sitelinks': 'div._zHp > div::text'
            },
        },
        'ads_main': {
            'us_ip': {
                'container': '#center_col',
                'result_container': 'li.ads-ad',
                'link': 'h3.r > a:first-of-type::attr(href)',
                'snippet': 'div.s span.st::text',
                'title': 'h3.r > a:first-of-type::text',
                'visible_link': '.ads-visurl cite::text',
                'rating': 'div._Ond _Bu span::text',
                'sitelinks': 'div.osl::text'
            },
            'de_ip': {
                'container': '#center_col',
                'result_container': '.ads-ad',
                'link': 'h3 > a:nth-child(2)::attr(href)',
                'snippet': 'div.ads-creative::text',
                'title': 'h3 > a:nth-child(2)::text',
                'visible_link': '.ads-visurl cite::text',
                'rating': 'div._Ond _Bu span::text',
                'sitelinks': 'ul._wEo::text'
            }
        },
        'related_keywords': {
            'de_ip': {
                'container': 'div.card-section',
                'result_container': 'p._e4b',
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
        """Clean the urls.

        A typical scraped results looks like the following:

        '/url?q=http://www.youtube.com/user/Apple&sa=U&ei=\
        lntiVN7JDsTfPZCMgKAO&ved=0CFQQFjAO&usg=AFQjCNGkX65O-hKLmyq1FX9HQqbb9iYn9A'

        Clean with a short regex.
        """
        super().after_parsing()

        if self.searchtype == 'normal':
            if self.num_results > 0:
                self.no_results = False
            elif self.num_results <= 0:
                self.no_results = True

            if 'No results found for' in \
               self.html or 'did not match any documents' in self.html:
                self.no_results = True

            # finally try in the snippets
            if self.no_results is True:
                for key, i in self.iter_serp_items():

                    if 'snippet' in self.search_results[key][i] and self.query:
                        if self.query.replace('"', '') in \
                           self.search_results[key][i]['snippet']:
                            self.no_results = False

        if self.searchtype == 'image':
            for key, i in self.iter_serp_items():
                if self.search_results[key][i]:
                    meta_dict = json.loads(self.search_results[key][i]['snippet'])
                    rank = self.search_results[key][i]['rank']
                    # logger.info(meta_dict)
                    self.search_results[key][i] = {
                        'link': meta_dict['ou'],
                        'snippet': meta_dict['s'],
                        'title': meta_dict['pt'],
                        'visible_link': meta_dict['isu'],
                        'rating': None,
                        'sitelinks': None,
                        'rank': rank
                    }

        clean_regexes = {
            'normal': r'/url\?q=(?P<url>.*?)&sa=U&ei=',
            'image': r'imgres\?imgurl=(?P<url>.*?)&'
        }

        for key, i in self.iter_serp_items():
            result = re.search(
                clean_regexes[self.searchtype],
                self.search_results[key][i]['link']
            )
            if result:
                self.search_results[key][i]['link'] = unquote(
                    result.group('url')
                )
