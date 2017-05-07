# -*- coding: utf-8 -*-

from collections import namedtuple
import csv
import json
import os
import threading
from scrapcore import database


class JsonStreamWriter():
    """Writes consecutive objects to an json output file."""

    def __init__(self, filename):
        self.file = open(filename, 'wt')
        self.file.write('[')
        self.last_object = None

    def write(self, obj):
        if self.last_object:
            self.file.write(',')
        json.dump(obj, self.file, indent=2, sort_keys=True)
        self.last_object = id(obj)

    def end(self):
        self.file.write(']')
        self.file.close()


class CsvStreamWriter():
    """
    Writes consecutive objects to an csv output file.
    """
    def __init__(self, filename, csv_fieldnames):
        self.csv_fieldnames = csv_fieldnames
        self.file = open(filename, 'wt')
        self.dict_writer = csv.DictWriter(
            self.file,
            fieldnames=csv_fieldnames,
            delimiter=','
        )
        self.dict_writer.writeheader()

    def write(self, data, serp):
        for row in data['results']:
            d = serp
            d.update(row)
            d = ({k: v if type(v) is str else v for k, v in d.items() if k in self.csv_fieldnames})
            self.dict_writer.writerow(d)

    def end(self):
        self.file.close()


class ScrapeJobGenerator():

    def get(self, keywords, search_engines, scrape_method, num_pages):
        """Get scrape jobs by keywords."""
        for keyword in keywords:
            for search_engine in search_engines:
                for page in range(1, num_pages + 1):
                    yield {
                        'query': keyword,
                        'search_engine': search_engine,
                        'scrape_method': scrape_method,
                        'page_number': page
                    }


class Proxies():
    Proxy = namedtuple('Proxy', 'proto, host, port, username, password')

    def parse_proxy_file(self, fname):
        """Parses a proxy file
        The format should be like the following:
            socks5 XX.XXX.XX.XX:1080 username:password
            socks4 XX.XXX.XX.XX:80 username:password
            http XX.XXX.XX.XX:80
            If username and password aren't provided, we assumes
            that the proxy doesn't need auth credentials.
        Args:
            fname: The file name where to look for proxies.
        Returns:
            The parsed proxies.
        Raises:
            ValueError if no file with the path fname could be found.
        """
        proxies = []
        path = os.path.join(os.getcwd(), fname)
        if os.path.exists(path):
            with open(path, 'r') as pf:
                for line in pf.readlines():

                    if not (line.strip().startswith('#') or
                            line.strip().startswith('//')):

                        tokens = line.replace('\n', '').split(' ')
                        try:
                            proto = tokens[0]
                            host, port = tokens[1].split(':')
                        except Exception:
                            raise Exception('''
                                Invalid proxy file.
                                Should have the following format: {}
                                '''.format(self.parse_proxy_file.__doc__)
                            )
                        if len(tokens) == 3:
                            username, password = tokens[2].split(':')
                            proxies.append(
                                self.Proxy(
                                    proto=proto,
                                    host=host,
                                    port=port,
                                    username=username,
                                    password=password
                                )
                            )
                        else:
                            proxies.append(
                                self.Proxy(
                                    proto=proto,
                                    host=host,
                                    port=port,
                                    username='',
                                    password=''
                                )
                            )
            return proxies
        else:
            raise ValueError('No such file/directory')

    def add_proxies_to_db(self, proxies, session):
        """Adds the list of proxies to the database.
        If the proxy-ip already exists and the other data differs,
        it will be overwritten.
        Will not check the status of the proxy.
        Args:
            proxies: A list of proxies.
            session: A database session to work with.
        """
        for proxy in proxies:
            if proxy:
                p = session.query(database.Proxy).filter(proxy.host == database.Proxy.ip).first()

                if not p:
                    p = database.Proxy(ip=proxy.host)

                p.port = proxy.port
                p.username = proxy.username
                p.password = proxy.password
                p.proto = proxy.proto

                session.add(p)
                session.commit()


class ShowProgressQueue(threading.Thread):
    """Prints the number of keywords scraped already to show the user
    the progress of the scraping process..
    """

    def __init__(self, config, queue, num_keywords):
        """Create a ShowProgressQueue thread instance.
        Args:
            queue: A queue.Queue instance to share among the worker threads.
            num_keywords: The number of total keywords that need to be scraped.
        """
        super().__init__()
        self.queue = queue
        self.num_keywords = num_keywords
        self.num_already_processed = 0
        self.progress_fmt = '\033[92m{}/{} keywords processed.\033[0m'

    def run(self):
        while self.num_already_processed < self.num_keywords:
            e = self.queue.get()
            if e == 'done':
                break
            self.num_already_processed += 1
            print(self.progress_fmt.format(self.num_already_processed, self.num_keywords), end='\r')
            self.queue.task_done()


class Error(Exception):
    pass


class ConfigurationError(Exception):
    pass


class BlockedSearchException(Exception):
    pass
