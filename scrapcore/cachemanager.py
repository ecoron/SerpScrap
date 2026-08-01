#!/usr/bin/python3
import hashlib
import os
import shutil
import time

# import lxml.html
# from lxml.html.clean import Cleaner
from scrapcore.database import SearchEngineResultsPage
from scrapcore.parsing import Parsing


class CacheManager:
    """Manages caching"""

    CACHEDIR = '.serpscrap'
    CLEAN_CACHE_AFTER = 48

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.create_cache_dir()
        self.clean_cache()

    def create_cache_dir(self):
        if self.config.get('do_caching', True):
            cd = self.config.get('cachedir', self.CACHEDIR)
            if not os.path.exists(cd):
                os.makedirs(cd, exist_ok=True)

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
        if not self.config.get('do_caching', True):
            return False
        file_name = self.cached_file_name(
            keyword,
            search_engine,
            scrapemode,
            page_number
        )
        cache_dir = self.config.get('cachedir', self.CACHEDIR)
        cache_path = os.path.join(cache_dir, file_name)
        if not os.path.exists(cache_path):
            return False
        try:
            modtime = os.path.getmtime(cache_path)
        except FileNotFoundError:
            return False
        modtime = (time.time() - modtime) / 60 / 60
        if modtime > int(self.config.get('clean_cache_after', self.CLEAN_CACHE_AFTER)):
            return False
        return self.read_cached_file(cache_path)

    def read_cached_file(self, path):
        """Read a cache file."""
        ext = path.split('.')[-1]
        if ext == 'cache':
            try:
                with open(path, encoding='utf-8') as fd:
                    return fd.read()
            except UnicodeDecodeError as e:
                self.logger.warning(str(e))
                return None
            except Exception as e:
                self.logger.error(f"Error reading cache file {path}: {e}")
                return None
        else:
            raise Exception(f'"{path}" is an invalid cache file.')

    def cache_results(self,
                      parser,
                      query,
                      search_engine,
                      scrape_mode,
                      page_number,
                      db_lock=None):
        """Stores the parsed html in a file.
        If a db_lock is given, all actions are wrapped in this lock.
        """
        if not self.config.get('do_caching', True):
            return
        if db_lock:
            db_lock.acquire()
        try:
            html = parser.cleaned_html if self.config.get('minimize_caching_files', False) else parser.html
            file_name = self.cached_file_name(
                query,
                search_engine,
                scrape_mode,
                page_number
            )
            cache_dir = self.config.get('cachedir', self.CACHEDIR)
            path = os.path.join(cache_dir, file_name)
            with open(path, 'w', encoding='utf-8') as fd:
                if isinstance(html, bytes):
                    fd.write(html.decode('utf-8', errors='replace'))
                else:
                    fd.write(str(html))
        finally:
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
                serp = None
                try:
                    serp = self.get_serp_from_database(
                        session,
                        job['query'],
                        job['search_engine'],
                        job['scrape_method'],
                        job['page_number']
                    )
                except Exception as e:
                    self.logger.error(f"DB error for {file_name}: {e}")

                if not serp:
                    try:
                        serp = self.parse_again(
                            file_name,
                            job['search_engine'],
                            job['query'],
                            job['scrape_method'],
                            job['page_number'],
                        )
                    except Exception as e:
                        self.logger.error(f"Parse error for {file_name}: {e}")
                        continue

                if not hasattr(serp, 'scraper_searches'):
                    serp.scraper_searches = []
                serp.scraper_searches.append(scraper_search)
                session.add(serp)

                if num_cached % 200 == 0:
                    session.commit()

                num_cached += 1
                scrape_jobs.remove(job)

        self.logger.info('{} cache files found in {}'.format(
            len(files),
            self.config.get('cachedir'))
        )
        self.logger.info(f'''{num_cached}/{num_total} objects have been read from the cache.
        {num_total - num_cached} remain to get scraped.'''
        )

        session.add(scraper_search)
        session.commit()

        return scrape_jobs

    def parse_again(self, file_name, search_engine, query, scrape_method, page_number):
        path = os.path.join(
            self.config.get('cachedir', self.CACHEDIR),
            file_name
        )
        html = self.read_cached_file(path)
        parsing = Parsing()
        serp = parsing.parse_serp(
            self.config,
            html=html,
            search_engine=search_engine,
            query=query
        )
        serp.search_engine_name = search_engine
        serp.scrape_method = scrape_method
        serp.page_number = page_number
        serp.requested_by = 'cache'
        serp.status = 'successful'
        return serp

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
