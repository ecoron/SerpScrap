#!/usr/bin/python3
# -*- coding: utf-8 -*-
import serpscrap

keywords = ['computer since']

config = serpscrap.Config()
config.set('scrape_urls', True)

scrap = serpscrap.SerpScrap()
scrap.init(config=config.get(), keywords=keywords)
results = scrap.run()

for result in results:
    print(result)
    print()
