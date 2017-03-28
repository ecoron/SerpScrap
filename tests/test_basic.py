#!/usr/bin/python3
# -*- coding: utf-8 -*-
import serpscrap


class TestClass:
    def test_simple(self):
        keywords = ['computer since']
        config = serpscrap.Config()
        config.set('scrape_urls', False)
        scrap = serpscrap.SerpScrap()
        scrap.init(config=config.get(), keywords=keywords)
        results = scrap.run()

        assert len(results) > 0
        assert len(results[0]) > 0
