#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pprint
import serpscrap

keywords = ['example']

config = serpscrap.Config()
config.set('scrape_urls', False)

scrap = serpscrap.SerpScrap()
scrap.init(config=config.get(), keywords=keywords)
results = scrap.run()

for result in results:
    pprint.pprint(result)
    print()
