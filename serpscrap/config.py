#!/usr/bin/python3
# -*- coding: utf-8 -*-


class Config():

    config = {
        # 'use_own_ip': True,
        'search_engines': ['google'],
        'num_pages_for_keyword': 2,
        'scrape_method': 'http',  # selenium
        # 'sel_browser': 'chrome', uncomment if scrape_method is selenium
        # 'executable_path': 'path\to\chromedriver' or 'path\to\phantomjs',
        'do_caching': True,
        'cachedir': '/tmp/.serpscrap/',
        'database_name': '/tmp/serpscrap',
        'clean_cache_after': 24,
        'output_filename': None,
        # 'print_results': 'all',
        'scrape_urls': True,
        'url_threads': 3
    }

    def get(self):
        """get the config dictionary"""
        return self.config

    def set(self, key, value):
        """set or update a value of a config key"""
        self.config.__setitem__(key, value)

    def apply(self, config):
        """apply an individual conig"""
        self.config = config
