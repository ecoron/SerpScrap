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


class CacheManager:
    """Manages caching of search results and cache directory lifecycle."""

    CACHEDIR = '.serpscrap'
    CLEAN_CACHE_AFTER = 48

    def __init__(self, config, logger, result_writer):
        self.config = config
        self.logger = logger
        self.result_writer = result_writer
        self.create_cache_dir()
        self.clean_cache()

    def create_cache_dir(self):
        """Create cache directory if caching is enabled and directory does not exist."""
        if self.config.get('do_caching', True):
            cd = self.config.get('cachedir', self.CACHEDIR)
            os.makedirs(cd, exist_ok=True)

    def clean_cache(self):
        """Remove cache files/directories older than configured threshold."""
        cachedir = self.config.get('cachedir', self.CACHEDIR)
        if os.path.exists(cachedir):
            cache_time = int(self.config.get('clean_cache_after', self.CLEAN_CACHE_AFTER))
            max_cache_time = 60 * 60 * cache_time
            for file_name in os.listdir(cachedir):
                path = os.path.join(cachedir, file_name)
                try:
                    if time.time() > os.path.getmtime(path) + max_cache_time:
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                except Exception as e:
                    self.logger.warning(f"Failed to clean cache file {path}: {e}")

    def cached_file_name(self, keyword, search_engine, scrape_mode, page_number):
        """Generate a unique cache file name for a search request."""
        unique = [keyword, search_engine, scrape_mode, page_number]
        sha = hashlib.sha256()
        sha.update(b''.join(str(s).encode() for s in unique))
        return f"{sha.hexdigest()}.cache"

    def get_cached(self, keyword, search_engine, scrapemode, page_number):
        """Load a cached result if available and not expired."""
        if not self.config.get('do_caching', False):
            return False
        file_name = self.cached_file_name(keyword, search_engine, scrapemode, page_number)
        cache_dir = self.config.get('cachedir', self.CACHEDIR)
        path = os.path.join(cache_dir, file_name)
        if not os.path.exists(path):
            return False
        try:
            modtime = os.path.getmtime(path)
            modtime_hours = (time.time() - modtime) / 3600
            if modtime_hours > int(self.config.get('clean_cache_after', 48)):
                return False
            return self.read_cached_file(path)
        except Exception as e:
            self.logger.warning(f"Error reading cache file {path}: {e}")
            return False

    def read_cached_file(self, path):
        """Read and return the contents of a cache file."""
        if not self.config.get('do_caching', False):
            return None
        ext = path.split('.')[-1]
        if ext != 'cache':
            raise Exception(f'"{path}" is an invalid cache file.')
        try:
            with open(path, 'r', encoding='utf-8') as fd:
                return fd.read()
        except UnicodeDecodeError as e:
            self.logger.warning(str(e))
            return None

    def cache_results(self, parser, query, search_engine, scrape_mode, page_number, db_lock=None):
        """Store parsed HTML in a cache file, optionally using a lock."""
        if not self.config.get('do_caching', False):
            return
        html = parser.cleaned_html if self.config.get('minimize_caching_files', False) else parser.html
        file_name = self.cached_file_name(query, search_engine, scrape_mode, page_number)
        cache_dir = self.config.get('cachedir', self.CACHEDIR)
        path = os.path.join(cache_dir, file_name)
        if db_lock:
            db_lock.acquire()
        try:
            with open(path, 'w', encoding='utf-8') as fd:
                if isinstance(html, bytes):
                    fd.write(html.decode())
                else:
                    fd.write(html)
        finally:
            if db_lock:
                db_lock.release()

    def _get_all_cache_files(self):
        """Return all cache files in the cache directory tree."""
        files = set()
        for dirpath, _, filenames in os.walk(self.config.get('cachedir', self.CACHEDIR)):
            for file_name in filenames:
                if file_name.endswith('.cache'):
                    files.add(os.path.join(dirpath, file_name))
        return files

    def filter_scrape_jobs(self, scrape_jobs, session, scraper_search):
        """Filter out jobs that are already cached and parse them if needed."""
        files = self._get_all_cache_files()
        num_cached = num_total = 0
        mapping = {self.cached_file_name(job['query'], job['search_engine'], job['scrape_method'], job['page_number']): job for job in scrape_jobs}
        num_total = len(scrape_jobs)
        for path in files:
            file_name = os.path.split(path)[1]
            job = mapping.get(file_name)
            if job:
                try:
                    serp = self.get_serp_from_database(
                        session,
                        job['query'],
                        job['search_engine'],
                        job['scrape_method'],
                        job['page_number']
                    )
                except Exception as e:
                    self.logger.warning(f"DB lookup failed: {e}")
                    serp = None
                if not serp:
                    serp = self.parse_again(file_name, job['search_engine'], job['query'])
                serp.scraper_searches.append(scraper_search)
                session.add(serp)
                if num_cached % 200 == 0:
                    session.commit()
                self.result_writer.store_serp_result(serp, self.config)
                num_cached += 1
                scrape_jobs.remove(job)
        self.logger.info(f"{len(files)} cache files found in {self.config.get('cachedir')}")
        self.logger.info(f"{num_cached}/{num_total} objects have been read from the cache. {num_total - num_cached} remain to get scraped.")
        session.add(scraper_search)
        session.commit()
        return scrape_jobs

    def parse_again(self, file_name, search_engine, query):
        """Parse a cached file again to create a SearchEngineResultsPage object."""
        path = os.path.join(self.config.get('cachedir', self.CACHEDIR), file_name)
        html = self.read_cached_file(path)
        parsing = Parsing()
        return parsing.parse_serp(self.config, html=html, search_engine=search_engine, query=query)

    def get_serp_from_database(self, session, query, search_engine, scrape_method, page_number):
        """Retrieve a SearchEngineResultsPage from the database if it exists."""
        try:
            return session.query(SearchEngineResultsPage).filter(
                SearchEngineResultsPage.query == query,
                SearchEngineResultsPage.search_engine_name == search_engine,
                SearchEngineResultsPage.scrape_method == scrape_method,
                SearchEngineResultsPage.page_number == page_number
            ).first()
        except Exception as e:
            self.logger.warning(f"DB error: {e}")
            return None
