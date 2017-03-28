#!/usr/bin/python3
# -*- coding: utf-8 -*-
from serpscrap.config import Config
from serpscrap.serpscrap import SerpScrap


class TestClass:
    def test_simple(self):
        keywords = ['computer since']
        config = Config()
        config.set('scrape_urls', False)
        scrap = SerpScrap()
        scrap.init(config=config.get(), keywords=keywords)
        results = scrap.run()

        assert len(config.get()) == 13
        assert len(results) > 0
        assert len(results[0]) > 0
