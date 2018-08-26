#!/usr/bin/python3
# -*- coding: utf-8 -*-
import serpscrap

keywords = ['blockchain']

config = serpscrap.Config()
config.set('scrape_urls', True)

scrap = serpscrap.SerpScrap()
scrap.init(config=config.get(), keywords=keywords)
scrap.as_csv('/tmp/output')