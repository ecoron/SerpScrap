#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pprint
import serpscrap


def scrape_to_csv(config, keywords):
    scrap = serpscrap.SerpScrap()
    scrap.init(config=config.get(), keywords=keywords)
    return scrap.as_csv('/tmp/cryptocurrency')


def get_related(config, keywords, related):
    scrap = serpscrap.SerpScrap()
    scrap.init(config=config.get(), keywords=keywords)
    scrap.run()
    results = scrap.get_related()
    for keyword in results:
        if keyword['keyword'] not in related:
            related.append(keyword['keyword'])
    return related


config = serpscrap.Config()
config.set('scrape_urls', False)
config.set('num_workers', 1)

keywords = ['cryptocurrency']

related = keywords
related = get_related(config, keywords, related)

scrape_to_csv(config, related)

pprint.pprint('********************')
pprint.pprint(related)
