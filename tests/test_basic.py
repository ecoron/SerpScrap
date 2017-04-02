#!/usr/bin/python3
# -*- coding: utf-8 -*-
import random

from serpscrap.config import Config
from serpscrap.serpscrap import SerpScrap


class TestClass:

    def test_simple(self):

        keyword_list = [
            'computer news',
            'since topics',
            'python tutorial',
            'pythons',
            'machine learning',
            'artificial intelligence',
        ]
        keywords = random.choice(keyword_list)

        config = Config()
        config.set('scrape_urls', False)
        scrap = SerpScrap()
        scrap.init(config=config.get(), keywords=keywords)
        results = scrap.run()

        assert len(config.get()) == 23
        assert len(results) > 0
        assert len(results[0]) > 0
