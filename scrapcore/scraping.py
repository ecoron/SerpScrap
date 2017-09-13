# -*- coding: utf-8 -*-
import abc
import datetime
import logging
import random
import time

from scrapcore.database import db_Proxy
from scrapcore.parsing import Parsing
from scrapcore.result_writer import ResultWriter
from scrapcore.tools import Proxies

logger = logging.getLogger(__name__)
SEARCH_MODES = ('selenium')


class GoogleSearchError(Exception):
    pass


class InvalidNumberResultsException(GoogleSearchError):
    pass


class MaliciousRequestDetected(GoogleSearchError):
    pass


class SeleniumMisconfigurationError(Exception):
    pass


class SeleniumSearchError(Exception):
    pass


class StopScrapingException(Exception):
    pass


def get_base_search_url_by_search_engine(config,
                                         search_engine_name,
                                         search_mode):
    """Retrieves the search engine base url for a specific search_engine."""
    assert search_mode in SEARCH_MODES, 'search mode "{}" is not available'.format(search_mode)

    specific_base_url = config.get(
        '{}_search_url'.format(search_engine_name),
        None
    )

    return specific_base_url


class SearchEngineScrape(metaclass=abc.ABCMeta):
    """Abstract base class that represents a search engine scrape."""

    malicious_request_needles = {
        'google': {
            'inurl': '/sorry/',
            'inhtml': 'detected unusual traffic'
        },
    }

    def __init__(self,
                 config,
                 cache_manager=None,
                 jobs=None,
                 scraper_search=None,
                 session=None,
                 db_lock=None,
                 cache_lock=None,
                 start_page_pos=1,
                 search_engine=None,
                 search_type=None,
                 proxy=None,
                 progress_queue=None):
        """Instantiate an SearchEngineScrape object."""

        self.config = config
        self.cache_manager = cache_manager

        jobs = jobs or {}
        self.search_engine_name = search_engine.lower()

        assert self.search_engine_name, 'You need to specify an search_engine'

        if not search_type:
            self.search_type = self.config.get('search_type', 'normal')
        else:
            self.search_type = search_type

        self.jobs = jobs

        # the keywords that couldn't be scraped by this worker
        self.missed_keywords = set()
        # the number of keywords
        self.num_keywords = len(self.jobs)
        # The actual keyword that is to be scraped next
        self.query = ''
        # The default pages per keywords
        self.pages_per_keyword = [1, ]
        # The number that shows how many searches have been done by the worker
        self.search_number = 1
        # The parser that should be used to parse the search engine results
        self.parser = Parsing().get_parser_by_search_engine(
            self.search_engine_name
        )(config=self.config)
        # The number of results per page
        self.num_results_per_page = int(self.config.get('num_results_per_page', 10))

        # The page where to start scraping. By default the starting page is 1.
        if start_page_pos:
            self.start_page_pos = 1 if start_page_pos < 1 else start_page_pos
        else:
            self.start_page_pos = int(self.config.get('search_offset', 1))

        # The page where we are right now
        self.page_number = self.start_page_pos

        # Install the proxy if one was provided
        self.proxy = proxy
        if isinstance(proxy, Proxies().Proxy):
            self.set_proxy()
            self.requested_by = self.proxy.host + ':' + self.proxy.port
        else:
            self.requested_by = 'localhost'

        # the scraper_search object
        self.scraper_search = scraper_search
        # the scrape mode
        # to be set by subclasses
        self.scrape_method = ''
        # Whether the instance is ready to run
        self.startable = True
        # set the database lock
        self.db_lock = db_lock
        # init the cache lock
        self.cache_lock = cache_lock
        # a queue to put an element in whenever a new keyword is scraped.
        # to visualize the progress
        self.progress_queue = progress_queue
        # set the session
        self.session = session
        # the current request time
        self.requested_at = None
        # The name of the scraper
        self.name = '[{}]'.format(self.search_engine_name) + self.__class__.__name__

        # How long to sleep (in seconds) after every request
        self.sleeping_min = self.config.get('sleeping_min')
        self.sleeping_max = self.config.get('sleeping_max')

        # the default timeout
        self.timeout = 5
        # the status of the thread after finishing or failing
        self.status = 'successful'
        self.html = ''

    @abc.abstractmethod
    def search(self, *args, **kwargs):
        """Send the search request(s) over the transport."""

    @abc.abstractmethod
    def set_proxy(self):
        """Install a proxy on the communication channel."""

    @abc.abstractmethod
    def switch_proxy(self, proxy):
        """Switch the proxy on the communication channel."""

    @abc.abstractmethod
    def proxy_check(self, proxy):
        """Check whether the assigned proxy works correctly and react"""

    @abc.abstractmethod
    def handle_request_denied(self, status_code):
        """Generic behaviour when search engines detect our scraping.
        Args:
            status_code: The status code of the http response.
        """
        self.status = 'Malicious request detected: {}'.format(status_code)

    def store(self):
        """Store the parsed data in the sqlalchemy scoped session."""
        assert self.session, 'No database session.'

        if self.html:
            # @todo check issue parser in selenium mode
            self.parser.parse(self.html)
        else:
            self.parser = None

        with self.db_lock:

            serp = Parsing().parse_serp(
                self.config,
                parser=self.parser,
                scraper=self,
                query=self.query
            )

            self.scraper_search.serps.append(serp)
            self.session.add(serp)
            self.session.commit()

            ResultWriter().store_serp_result(serp, self.config)

            if serp.num_results:
                return True
            else:
                return False

    def next_page(self):
        """Increment the page."""
        self.start_page_pos += 1

    def keyword_info(self):
        """Print a short summary"""
        logger.info('''
            {thread_name} {ip} - Keyword: "{keyword}" with {num_pages} pages,
            slept {delay} seconds before scraping. {done}/{all} already scraped
            '''.format(
                    thread_name=self.name,
                    ip=self.requested_by,
                    keyword=self.query,
                    num_pages=self.pages_per_keyword,
                    delay=self.current_delay,
                    done=self.search_number,
                    all=self.num_keywords
                    ))

    def instance_creation_info(self, scraper_name):
        """Debug message whenever a scraping worker is created"""
        logger.info('''
        [+] {}[{}][search-type:{}][{}] using search engine "{}".
        Num keywords={}, num pages for keyword={}
        '''.format(
            scraper_name,
            self.requested_by,
            self.search_type,
            self.base_search_url,
            self.search_engine_name,
            len(self.jobs),
            self.pages_per_keyword))

    def cache_results(self):
        """Caches the html for the current request."""
        self.cache_manager.cache_results(
            self.parser,
            self.query,
            self.search_engine_name,
            self.scrape_method,
            self.page_number,
            db_lock=self.db_lock
        )

    def detection_prevention_sleep(self):
        # randomly delay from sleep range
        self.current_delay = random.randrange(
            self.sleeping_min,
            self.sleeping_max
        )
        time.sleep(self.current_delay)

    def after_search(self):
        """Store the results and parse em.
        Notify the progress queue if necessary.
        """
        self.search_number += 1

        if not self.store():
            logger.debug('''
            No results to store for keyword: "{}" in search engine: {}
            '''.format(
                self.query,
                self.search_engine_name)
            )

        if self.progress_queue:
            self.progress_queue.put(1)
        self.cache_results()

    def before_search(self):
        """before entering the search loop."""
        # check proxies first before anything
        if self.config.get('check_proxies', True) and self.proxy:
            if not self.proxy_check(proxy=self.proxy):
                self.startable = False

    def update_proxy_status(self, status, ipinfo=None, online=True):
        """Sets the proxy status with the results of ipinfo.io
        Args:
            status: A string the describes the status of the proxy.
            ipinfo: The json results from ipinfo.io
            online: Whether the proxy is usable or not.
        """
        ipinfo = ipinfo or {}

        with self.db_lock:

            proxy = self.session.query(db_Proxy).filter(self.proxy.host == db_Proxy.ip).first()
            if proxy:
                for key in ipinfo.keys():
                    setattr(proxy, key, ipinfo[key])

                proxy.checked_at = datetime.datetime.utcnow()
                proxy.status = status
                proxy.online = online

                try:
                    self.session.merge(proxy, load=True)
                    self.session.commit()
                except:
                    pass
