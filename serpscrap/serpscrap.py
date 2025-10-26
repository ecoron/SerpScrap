#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
SerpScrap.SerpScrap
"""
import argparse
import chromedriver_autoinstaller
import os
import pprint
import shutil

from scrapcore.core import Core
from scrapcore.logger import Logger
from serpscrap.config import Config
from serpscrap.csv_writer import CsvWriter
from serpscrap.urlscrape import UrlScrape

logger = Logger()
logger.setup_logger()
logger = logger.get_logger()


class SerpScrap:
    """Main module to execute SERP and URL scrape tasks."""
    def __init__(self):
        self.args = []
        self.serp_query = None
        self.results = []
        self.related = []
        self.config = None
        self.driver = None

    def cli(self, args=None):
        """Method called if executed on command line."""
        parser = argparse.ArgumentParser(prog='serpscrap')
        parser.add_argument('-k', '--keyword', help='keyword for scraping', nargs='*')
        self.args = parser.parse_args()
        if self.args.keyword:
            keywords = ' '.join(self.args.keyword)
        else:
            raise ValueError('No keywords provided via CLI.')
        self.init(config=None, keywords=keywords)
        return self.run()

    def _setup_webdriver(self):
        import chromedriver_autoinstaller
        from selenium import webdriver
        chromedriver_autoinstaller.install()
        logger.info("Verified chromedriver installation via chromedriver-autoinstaller.")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        executable_path = self.config.get('executable_path', '')
        self.driver = webdriver.Chrome(executable_path or None, options=options)

    def init(self, config=None, keywords=None):
        """Initialize config and serp_query."""
        if config is not None:
            self.config = config
        else:
            self.config = Config().get()
        self._setup_webdriver()
        # Cleanup screenshot dir on init
        if os.path.exists(self.config['dir_screenshot']):
            shutil.rmtree(self.config['dir_screenshot'], ignore_errors=True)
        screendir = f"{self.config['dir_screenshot']}/{self.config['today']}"
        if not os.path.exists(screendir):
            os.makedirs(screendir)
        if isinstance(keywords, str):
            self.serp_query = [keywords]
        elif isinstance(keywords, list) and keywords:
            self.serp_query = keywords
        else:
            raise ValueError('No keywords given')

    def run(self):
        """Main method to run scrap_serps and scrap_url."""
        self.results = []
        if self.serp_query is not None:
            self.results = self.scrap_serps()
        if self.config.get('scrape_urls'):
            for index, result in enumerate(self.results):
                if 'serp_type' in result and 'serp_url' in result:
                    logger.info('Scraping URL: ' + result['serp_url'])
                    result_url = self.scrap_url(result['serp_url'])
                    if 'status' in result_url:
                        self.results[index].update(result_url)
        return self.results if isinstance(self.results, list) else [self.results]

    def as_csv(self, file_path: str):
        writer = CsvWriter()
        self.results = self.run()
        writer.write(file_path + '.csv', self.results)

    def scrap_serps(self):
        """Call scrap method and append SERP results to list."""
        search = self.scrap()
        self.results = []
        if search is not None:
            for serp in search.serps:
                self.related = []
                for related_keyword in getattr(serp, 'related_keywords', []):
                    self.related.append({
                        'keyword': related_keyword.keyword,
                        'rank': related_keyword.rank
                    })
                for link in getattr(serp, 'links', []):
                    self.results.append({
                        'query_num_results_total': getattr(serp, 'num_results_for_query', ''),
                        'query_num_results_page': getattr(serp, 'num_results', 0),
                        'query_page_number': getattr(serp, 'page_number', -1),
                        'query': getattr(serp, 'query', ''),
                        'serp_rank': getattr(link, 'rank', None),
                        'serp_type': getattr(link, 'link_type', None),
                        'serp_url': getattr(link, 'link', None),
                        'serp_rating': getattr(link, 'rating', None),
                        'serp_title': getattr(link, 'title', None),
                        'serp_domain': getattr(link, 'domain', None),
                        'serp_visible_link': getattr(link, 'visible_link', None),
                        'serp_snippet': getattr(link, 'snippet', None),
                        'serp_sitelinks': getattr(link, 'sitelinks', None),
                        'screenshot': os.path.join(f"{self.config['dir_screenshot']}/{self.config['today']}/google_{serp.query}-{serp.page_number}.png")
                    })
            return self.results
        else:
            raise Exception('No Results')

    def scrap(self):
        """Call Core().run with the current config and keywords."""
        self.config['keywords'] = self.serp_query if isinstance(self.serp_query, list) else [self.serp_query]
        return Core().run(self.config)

    def scrap_url(self, url: str):
        """Call UrlScrape for a given URL."""
        urlscrape = UrlScrape(self.config)
        return urlscrape.scrap_url(url)

    def get_related(self):
        return self.related
