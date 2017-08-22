#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pprint
import serpscrap

keywords = ['lost places']

config = serpscrap.Config()
config.set('search_type', 'image')

scrap = serpscrap.SerpScrap()
scrap.init(config=config.get(), keywords=keywords)
results = scrap.run()

for result in results[:10]:
    pprint.pprint(result)
    print()
