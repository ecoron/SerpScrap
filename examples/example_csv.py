#!/usr/bin/python3
# -*- coding: utf-8 -*-
import serpscrap

keywords = ['seo tools', 'seo news']

config = serpscrap.Config()
config.set('scrape_urls', False)

scrap = serpscrap.SerpScrap()
scrap.init(config=config.get(), keywords=keywords)
results = scrap.as_csv('/tmp/output')
