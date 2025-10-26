#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
"""
SerpScrap.Config
"""


class Config:
    """
    Config
    This module is used to hold and handle the required configuration settings.
    """
    def __init__(self):
        self.config = {
            'use_own_ip': True,
            'search_engines': ['google'],
            'num_pages_for_keyword': 2,
            'scrape_method': 'selenium',
            'sel_browser': 'chrome',
            'chrome_headless': True,
            'executable_path': '',
            'do_caching': True,
            'cachedir': '/tmp/.serpscrap/',
            'screenshot': True,
            'dir_screenshot': '/tmp/screenshots',
            'database_name': '/tmp/serpscrap',
            'minimize_caching_files': True,
            'clean_cache_after': 24,
            'output_filename': None,
            # 'print_results': 'all',
            'scrape_urls': False,
            'url_threads': 6,
            'log_level': 'INFO',
            'num_workers': 1,
            'num_results_per_page': 10,
            'results_age': 'Any',
            'sleeping_min': 20,
            'sleeping_max': 25,
            'search_type': 'normal',
            'google_search_url': 'https://www.google.com/search?',
            'bing_search_url': 'http://www.bing.com/search?',
            'headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4',
                'Accept-Encoding': 'gzip, deflate, br'
            },
            'proxy_file': '',
            'proxy_check_url': 'http://canihazip.com/s',
            'proxy_info_url': 'https://ipinfo.io/json',
            'stop_on_detection': True,
            'today': datetime.datetime.strftime(
                datetime.datetime.utcnow(),
                '%Y-%m-%d'
            )
        }

    @property
    def __dict__(self):
        return self.config

    def get(self) -> dict:
        """Get the config dictionary."""
        return self.config

    def set(self, key: str, value):
        """Set or update a value of a config key."""
        self.config[key] = value

    def apply(self, config: dict):
        """Apply an individual config, replacing default config by values of new config."""
        self.config.update(config)
