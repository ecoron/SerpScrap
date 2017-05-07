#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
SerpScrap.SerpScrap
"""
import argparse
import pprint

import chardet
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
        adjust_encoding(string): for encoding
    """
    args = []

    serp_query = None

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
            if phantomjs is False:
                firstrun.download()
                phantomjs = firstrun.detect_phantomjs()
                if phantomjs is False:
                    raise Exception('''
                        phantomjs binary not found,
                        provide custom path in config''')
            self.config.__setitem__('executable_path', phantomjs)
            logger.info('using ' + phantomjs)

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
        results = None
        if self.serp_query is not None:
            results = self.scrap_serps()

        if self.config['scrape_urls']:
            for index, result in enumerate(results):
                if 'serp_type' in result and \
                   'ads_main' not in result['serp_type'] and \
                   'serp_url' in result:
                    result_url = self.scrap_url(result['serp_url'])[0]
                    if 'status' in result_url:
                        results[index].update(result_url)
        return results if isinstance(results, list) else [results]

    def as_csv(self, file_path):
        writer = CsvWriter()
        result = self.run()
        writer.write(file_path + '.csv', result)

    def scrap_serps(self):
        """call scrap method and append serp results to list
        Returns
            list: dict of scrape results
        """
        search = self.scrap()
        result = []
        if search is not None:
            for serp in search.serps:
                related = []
                for related_keyword in serp.related_keywords:
                    related.append({
                        'keyword': related_keyword.keyword,
                        'rank': related_keyword.rank
                    })
                for link in serp.links:
                    result.append({
                        'query_num_results total': serp.num_results_for_query,
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
                        'related_keywords': related
                    })
            return result
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

    def adjust_encoding(self, data):
        """detect and adjust encoding of data return data decoded to utf-8
        TODO:
            move to tools
        Args:
            data (string): data to encode
        Returns:
            dict: encoding and data
        """
        if data is None:
            return {'encoding': None, 'data': data}

        data = data.encode('utf-8')
        check_encoding = chardet.detect(data)

        if check_encoding['encoding'] is not None \
           and 'utf-8' not in check_encoding['encoding']:
            try:
                data = data.decode(check_encoding['encoding']).encode('utf-8')
            except Exception:
                pass
        try:
            data = data.decode('utf-8')
        except Exception:
            data = data.decode('utf-8', 'ignore')

        return {'encoding': check_encoding['encoding'], 'data': data}


if __name__ == "__main__":
    """called on commandline execution"""
    res = SerpScrap().cli()
    pprint.pprint(res)
