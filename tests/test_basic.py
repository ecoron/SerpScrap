#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import os
import random

from serpscrap.config import Config
from serpscrap.serpscrap import SerpScrap


class TestClass:

    keyword_list = [
        'computer news',
        'since topics',
        'python tutorial',
        'pythons',
        'machine learning',
        'artificial intelligence',
    ]

    def test_config_default(self):
        config = Config()
        assert len(config.get()) == 31
        assert config.use_own_ip is True
        assert config.screenshot is True
        assert config.scrape_urls is False

        today = datetime.datetime.strftime(
            datetime.datetime.utcnow(),
            '%Y-%m-%d'
        )
        assert config.today == today

    def test_simple(self):

        keywords = random.choice(self.keyword_list)

        config = Config()
        config.set('sel_browser', 'chrome')
        config.set('chrome_headless', True)
        config.set('executable_path', '/usr/local/bin/chromedriver')
        scrap = SerpScrap()
        scrap.init(config=config.get(), keywords=keywords)
        results = scrap.run()

        assert len(results) > 0
        assert len(results[0]) > 0


    def test_screenshot(self):
        keywords = random.choice(self.keyword_list)
        config = Config()
        config.set('screenshot', True)
        scrap = SerpScrap()
        scrap.init(config=config.get(), keywords=keywords)
        # results = scrap.run()

        screendir = '{}/{}'.format(
            config.get()['dir_screenshot'],
            config.today
        )

        assert config.get()['screenshot'] is True
        assert os.path.exists(screendir) is True
