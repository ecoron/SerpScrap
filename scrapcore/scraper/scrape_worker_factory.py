# -*- coding: utf-8 -*-


class ScrapeWorkerFactory():
    def __init__(self, config, cache_manager=None, mode=None, proxy=None,
                 search_engine=None, session=None, db_lock=None,
                 cache_lock=None, scraper_search=None, captcha_lock=None,
                 progress_queue=None, browser_num=1):

        self.config = config
        self.cache_manager = cache_manager
        self.mode = mode
        self.proxy = proxy
        self.search_engine = search_engine
        self.session = session
        self.db_lock = db_lock
        self.cache_lock = cache_lock
        self.scraper_search = scraper_search
        self.captcha_lock = captcha_lock
        self.progress_queue = progress_queue
        self.browser_num = browser_num

        self.jobs = dict()

    def is_suitabe(self, job):

        return job['scrape_method'] == self.mode and job['search_engine'] == self.search_engine

    def add_job(self, job):

        query = job['query']
        page_number = job['page_number']

        if query not in self.jobs:
            self.jobs[query] = []

        self.jobs[query].append(page_number)

    def get_worker(self):

        if self.jobs:

            if self.mode == 'selenium':
                from scrapcore.scraper.selenium import get_selenium_scraper_by_search_engine_name
                return get_selenium_scraper_by_search_engine_name(
                    self.config,
                    self.search_engine,
                    cache_manager=self.cache_manager,
                    search_engine=self.search_engine,
                    jobs=self.jobs,
                    session=self.session,
                    scraper_search=self.scraper_search,
                    cache_lock=self.cache_lock,
                    db_lock=self.db_lock,
                    proxy=self.proxy,
                    progress_queue=self.progress_queue,
                    captcha_lock=self.captcha_lock,
                    browser_num=self.browser_num,
                )

        return None
