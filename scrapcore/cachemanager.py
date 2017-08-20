#!/usr/bin/python3
# -*- coding: utf-8 -*-
import hashlib
import os
import shutil
import time

# import lxml.html
# from lxml.html.clean import Cleaner
from scrapcore.database import SearchEngineResultsPage
from scrapcore.parsing import Parsing


class CacheManager():
    """Manages caching"""

    CACHEDIR = '.serpscrap'
    CLEAN_CACHE_AFTER = 48

    def __init__(self, config, logger, result_writer):
        self.config = config
        self.logger = logger
        self.create_cache_dir()
        self.clean_cache()
        self.result_writer = result_writer

    def create_cache_dir(self):
        if self.config.get('do_caching', True):
            cd = self.config.get('cachedir', self.CACHEDIR)
            if not os.path.exists(cd):
                os.mkdir(cd)

    def clean_cache(self):
        """Clean the caches searches."""
        cachedir = self.config.get('cachedir', self.CACHEDIR)
        if os.path.exists(cachedir):
            for file_name in os.listdir(cachedir):
                path = os.path.join(cachedir, file_name)
                cache_time = int(
                    self.config.get(
                        'clean_cache_after',
                        self.CLEAN_CACHE_AFTER
                    )
                )
                max_cache_time = 60 * 60 * cache_time
                if time.time() > os.path.getmtime(path) + max_cache_time:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(os.path.join(cachedir, file_name))

    def cached_file_name(self,
                         keyword,
                         search_engine,
                         scrape_mode,
                         page_number):
        """Make a unique file name from the search engine search request."""
        unique = [keyword, search_engine, scrape_mode, page_number]
        sha = hashlib.sha256()
        sha.update(b''.join(str(s).encode() for s in unique))

        return '{file_name}.{extension}'.format(
            file_name=sha.hexdigest(),
            extension='cache'
        )

    def get_cached(self, keyword, search_engine, scrapemode, page_number):
        """Loads a cached result."""
        if self.config.get('do_caching', False):
            file_name = self.cached_file_name(
                keyword,
                search_engine,
                scrapemode,
                page_number
            )
            cache_dir = self.config.get('cachedir', self.CACHEDIR)
            if file_name in os.listdir(cache_dir):
                try:
                    modtime = os.path.getmtime(
                        os.path.join(cache_dir, file_name)
                    )
                except FileNotFoundError:
                    return False
                modtime = (time.time() - modtime) / 60 / 60
                if (modtime > int(self.config('clean_cache_after', 48))):
                    return False
                path = os.path.join(cache_dir, file_name)
                return self.read_cached_file(path)
            else:
                return False

    def read_cached_file(self, path):
        """Read a cache file."""
        if self.config.get('do_caching', False):
            ext = path.split('.')[-1]

            if ext == 'cache':
                with open(path, 'r') as fd:
                    try:
                        return fd.read()
                    except UnicodeDecodeError as e:
                        self.logger.warning(str(e))
            else:
                raise Exception('"{}" is a invalid cache file.'.format(path))

    def cache_results(self,
                      parser,
                      query,
                      search_engine,
                      scrape_mode,
                      page_number,
                      db_lock=None):
        """Stores the parsed html in a file.
        If an db_lock is given, all action are wrapped in this lock.
        """
        if self.config.get('do_caching', False):
            if db_lock:
                db_lock.acquire()

            if self.config.get('minimize_caching_files', False):
                html = parser.cleaned_html
            else:
                html = parser.html

            file_name = self.cached_file_name(
                query,
                search_engine,
                scrape_mode,
                page_number
            )
            cache_dir = self.config.get('cachedir', self.CACHEDIR)
            path = os.path.join(cache_dir, file_name)

            with open(path, 'w') as fd:
                if isinstance(html, bytes):
                    fd.write(html.decode())
                else:
                    fd.write(html)

            if db_lock:
                db_lock.release()

    def _get_all_cache_files(self):
        """Return all files found in the cachedir."""
        files = set()
        dir_tree = os.walk(self.config.get('cachedir', self.CACHEDIR))
        for dirpath, _, filenames in dir_tree:
            for file_name in filenames:
                if 'cache' in file_name:
                    files.add(os.path.join(dirpath, file_name))
        return files

    def filter_scrape_jobs(self,
                           scrape_jobs,
                           session,
                           scraper_search):
        """Walk recursively through the cachedir
        and parse all cached files.
        Args:
            session: An sql alchemy session to add the entities
            scraper_search: Abstract object representing the current search.

        Returns:
            The scrape jobs that couldn't be parsed from the cache directory.
        """
        files = self._get_all_cache_files()
        num_cached = num_total = 0
        mapping = {}
        for job in scrape_jobs:
            cache_name = self.cached_file_name(
                job['query'],
                job['search_engine'],
                job['scrape_method'],
                job['page_number']
            )
            mapping[cache_name] = job
            num_total += 1

        for path in files:
            file_name = os.path.split(path)[1]
            job = mapping.get(file_name, None)

            if job:
                try:
                    serp = self.get_serp_from_database(
                        session,
                        job['query'],
                        job['search_engine'],
                        job['scrape_method'],
                        job['page_number']
                    )
                except Exception:
                    pass

                if not serp:
                    serp = self.parse_again(
                        file_name,
                        job['search_engine'],
                        job['query']
                    )

                serp.scraper_searches.append(scraper_search)
                session.add(serp)

                if num_cached % 200 == 0:
                    session.commit()

                self.result_writer.store_serp_result(serp, self.config)
                num_cached += 1
                scrape_jobs.remove(job)

        self.logger.info('{} cache files found in {}'.format(
            len(files),
            self.config.get('cachedir'))
        )
        self.logger.info('''{}/{} objects have been read from the cache.
        {} remain to get scraped.'''.format(
            num_cached,
            num_total,
            num_total - num_cached)
        )

        session.add(scraper_search)
        session.commit()

        return scrape_jobs

    def parse_again(self, file_name, search_engine, query):
        path = os.path.join(
            self.config.get('cachedir', self.CACHEDIR),
            file_name
        )
        html = self.read_cached_file(path)
        parsing = Parsing()
        return parsing.parse_serp(
            self.config,
            html=html,
            search_engine=search_engine,
            query=query
        )

    def get_serp_from_database(self,
                               session,
                               query,
                               search_engine,
                               scrape_method,
                               page_number):
        try:
            serp = session.query(SearchEngineResultsPage).filter(
                SearchEngineResultsPage.query == query,
                SearchEngineResultsPage.search_engine_name == search_engine,
                SearchEngineResultsPage.scrape_method == scrape_method,
                SearchEngineResultsPage.page_number == page_number).first()
            return serp
        except Exception:
            return False
