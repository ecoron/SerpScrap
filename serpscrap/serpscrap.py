#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
SerpScrap.SerpScrap
"""
import argparse
import os
import pprint
import shutil

from scrapcore.core import Core
from scrapcore.logger import Logger
from serpscrap.config import Config
from serpscrap.csv_writer import CsvWriter
from serpscrap.phantom_install import PhantomInstall
from serpscrap.urlscrape import UrlScrape


logger = Logger()
logger.setup_logger()
logger = logger.get_logger()


class SerpScrap():
    """main module to execute the serp and url scrape tasks
    Attributes:
        args: list for cli args
        serp_query: list holds the keywords to query the search engine
        cli (list): for cli attributes
        init (dict, str|list): init SerpScarp
        run (): main method
        scrap_serps (): scrape serps
        scrap (): calls GoogleScraper
        scrap_url(string): calls UrlScrape
        as_csv(string): scrape serps save as csv
    """
    args = []

    serp_query = None

    results = []

    related = []

    def cli(self, args=None):
        """method called if executed on command line
        Args:
            args (mixed): args via commandline
        Returns:
            list: dicts of results
        """
        parser = argparse.ArgumentParser(prog='serpscrap')
        parser.add_argument(
            '-k',
            '--keyword',
            help='keyword for scraping',
            nargs='*'
        )
        self.args = parser.parse_args()
        if len(self.args.keyword) > 0:
            keywords = ' '.join(self.args.keyword)

        self.init(config=None, keywords=keywords)
        return self.run()

    def init(self, config=None, keywords=None):
        """init config and serp_query
        Args:
            config (None|dict): override default config
            keywords (str|list): string or list of strings, keywords to scrape
        Raises:
            ValueError:
        """
        if config is not None:
            self.config = config
        else:
            self.config = Config().get()

        if self.config['executable_path'] == '':
            logger.info('preparing phantomjs')
            firstrun = PhantomInstall()
            phantomjs = firstrun.detect_phantomjs()
            if phantomjs is None:
                firstrun.download()
                phantomjs = firstrun.detect_phantomjs()
                if phantomjs is None:
                    raise Exception('''
                        phantomjs binary not found,
                        provide custom path in config''')
            self.config.__setitem__('executable_path', phantomjs)
            logger.info('using ' + str(phantomjs))

        # cleanup screenshot dir on init
        if os.path.exists(self.config['dir_screenshot']):
            shutil.rmtree(self.config['dir_screenshot'], ignore_errors=True)
        # create screenshot dir current date
        screendir = '{}/{}'.format(
            self.config['dir_screenshot'],
            self.config['today']
        )

        if not os.path.exists(screendir):
            os.makedirs(screendir)

        if isinstance(keywords, str):
            self.serp_query = [keywords]
        elif isinstance(keywords, list) and len(keywords) > 0:
            self.serp_query = keywords
        else:
            raise ValueError('no keywords given')

    def run(self):
        """main method to run scrap_serps and scrap_url
        Returns:
            list: dicts with all results
        """
        self.results = []
        if self.serp_query is not None:
            self.results = self.scrap_serps()

        if self.config['scrape_urls']:
            for index, result in enumerate(self.results):
                if 'serp_type' in result and \
                   'ads_main' not in result['serp_type'] and \
                   'serp_url' in result:
                    result_url = self.scrap_url(result['serp_url'])[0]
                    if 'status' in result_url:
                        self.results[index].update(result_url)
        return self.results if isinstance(self.results, list) else [self.results]

    def as_csv(self, file_path):
        writer = CsvWriter()
        self.results = self.run()
        writer.write(file_path + '.csv', self.results)

    def scrap_serps(self):
        """call scrap method and append serp results to list
        Returns
            list: dict of scrape results
        """
        search = self.scrap()
        self.results = []
        if search is not None:
            for serp in search.serps:
                self.related = []
                for related_keyword in serp.related_keywords:
                    self.related.append({
                        'keyword': related_keyword.keyword,
                        'rank': related_keyword.rank
                    })
                for link in serp.links:
                    self.results.append({
                        'query_num_results_total': serp.num_results_for_query,
                        'query_num_results_page': serp.num_results,
                        'query_page_number': serp.page_number,
                        'query': serp.query,
                        'serp_rank': link.rank,
                        'serp_type': link.link_type,
                        'serp_url': link.link,
                        'serp_rating': link.rating,
                        'serp_title': link.title,
                        'serp_domain': link.domain,
                        'serp_visible_link': link.visible_link,
                        'serp_snippet': link.snippet,
                        'serp_sitelinks': link.sitelinks,
                        'screenshot': os.path.join('{}/{}/{}_{}-p{}.png'.format(
                            self.config['dir_screenshot'],
                            self.config['today'],
                            'google',
                            serp.query,
                            str(serp.page_number),
                        ))
                    })
            return self.results
        else:
            raise Exception('No Results')

    def scrap(self):
        """scrap, method calls GoogleScraper method
        Returns:
            dict: scrape result#
        """
        # See in the config.cfg file for possible values
        self.config['keywords'] = self.serp_query \
            if isinstance(self.serp_query, list) else [self.serp_query]

        return Core().run(self.config)

    def scrap_url(self, url):
        """method calls UrlScrape
        Args:
            url (string): url to scrape
        Returns:
            dict: result of url scrape
        """
        urlscrape = UrlScrape(self.config)
        return urlscrape.scrap_url(url)

    def get_related(self):
        return self.related


if __name__ == "__main__":
    """called on commandline execution"""
    res = SerpScrap().cli()
    pprint.pprint(res)
