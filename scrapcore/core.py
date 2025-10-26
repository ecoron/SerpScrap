#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import queue
import threading

from random import shuffle
from scrapcore.cachemanager import CacheManager
from scrapcore.database import ScraperSearch
from scrapcore.database import get_session, fixtures
from scrapcore.logger import Logger
from scrapcore.result_writer import ResultWriter
from scrapcore.scraper.scrape_worker_factory import ScrapeWorkerFactory
from scrapcore.tools import Proxies
from scrapcore.tools import ScrapeJobGenerator
from scrapcore.tools import ShowProgressQueue
from scrapcore.validator_config import ValidatorConfig


class Core:
    """Main controller for the scraping process."""

    def __init__(self):
        self.logger = None

    def run(self, config):
        """Validate config and start scraping."""
        ValidatorConfig().validate(config)
        return self.main(return_results=True, config=config)

    def _parse_search_engines(self, config):
        search_engines = config.get('search_engines', ['google'])
        if not isinstance(search_engines, list):
            if search_engines == '*':
                search_engines = config.get('supported_search_engines')
            else:
                search_engines = search_engines.split(',')
        return set(search_engines)

    def _get_proxies(self, config):
        proxies = []
        proxy_file = config.get('proxy_file', '')
        if config.get('use_own_ip'):
            proxies.append(None)
        elif proxy_file:
            proxies = Proxies().parse_proxy_file(proxy_file)
        if not proxies:
            raise Exception('No proxies available. Turning down.')
        shuffle(proxies)
        return proxies

    def _init_logger(self, config):
        logger = Logger()
        logger.setup_logger(level=config.get('log_level', 'INFO').upper())
        self.logger = logger.get_logger()

    def main(self, return_results=False, config=None):
        """Main scraping workflow."""
        self._init_logger(config)
        keywords = set(config.get('keywords', []))
        search_engines = self._parse_search_engines(config)
        num_search_engines = len(search_engines)
        num_workers = int(config.get('num_workers', 1))
        scrape_method = config.get('scrape_method')
        pages = int(config.get('num_pages_for_keyword', 1))
        method = config.get('scrape_method', 'selenium')

        result_writer = ResultWriter()
        result_writer.init_outfile(config, force_reload=True)
        cache_manager = CacheManager(config, self.logger, result_writer)

        scrape_jobs = ScrapeJobGenerator().get(
            keywords, search_engines, scrape_method, pages
        )
        scrape_jobs = list(scrape_jobs)
        proxies = self._get_proxies(config)

        session_cls = get_session(config, scoped=True)
        session = session_cls()
        fixtures(config, session)
        Proxies().add_proxies_to_db(proxies, session)

        scraper_search = ScraperSearch(
            number_search_engines_used=num_search_engines,
            number_proxies_used=len(proxies),
            number_search_queries=len(keywords),
            started_searching=datetime.datetime.utcnow(),
            used_search_engines=','.join(search_engines)
        )

        if config.get('do_caching'):
            scrape_jobs = cache_manager.filter_scrape_jobs(
                scrape_jobs, session, scraper_search
            )

        if scrape_jobs:
            self._run_workers(
                scrape_jobs, search_engines, proxies, num_workers, method,
                cache_manager, session, scraper_search, config, result_writer
            )

        result_writer.close_outfile()
        scraper_search.stopped_searching = datetime.datetime.utcnow()
        try:
            session.add(scraper_search)
            session.commit()
        except Exception:
            pass
        if return_results:
            # Eager loading der serps-Relation, um DetachedInstanceError zu vermeiden
            from sqlalchemy.orm import joinedload
            session.refresh(scraper_search)
            session.expunge(scraper_search)
            scraper_search = session.query(ScraperSearch).options(joinedload(ScraperSearch.serps)).get(scraper_search.id)
            return scraper_search

    def _run_workers(self, scrape_jobs, search_engines, proxies, num_workers, method,
                    cache_manager, session, scraper_search, config, result_writer):
        db_lock = threading.Lock()
        cache_lock = threading.Lock()
        captcha_lock = threading.Lock()
        self.logger.info(
            f"Going to scrape {len(scrape_jobs)} keywords with {len(proxies)} proxies by using {len(search_engines)} threads."
        )
        q = queue.Queue()
        progress_thread = ShowProgressQueue(config, q, len(scrape_jobs))
        progress_thread.start()
        workers = queue.Queue()
        num_worker = 0
        for search_engine in search_engines:
            for proxy in proxies:
                for _ in range(num_workers):
                    num_worker += 1
                    workers.put(
                        ScrapeWorkerFactory(
                            config,
                            search_engine=search_engine,
                            queries=[],
                            screenshot_dir=None
                        )
                    )
        for job in scrape_jobs:
            while True:
                worker = workers.get()
                workers.put(worker)
                if worker.is_suitabe(job):
                    worker.add_job(job)
                    break
        threads = []
        while not workers.empty():
            worker = workers.get()
            thread = worker.get_worker()
            if thread:
                threads.append(thread)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        q.put('done')
        progress_thread.join()
