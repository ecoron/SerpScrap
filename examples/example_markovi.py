#!/usr/bin/python3
# -*- coding: utf-8 -*-
from serpscrap.markovi import Markovi
from serpscrap.config import Config
from serpscrap.urlscrape import UrlScrape
import pprint


url = 'http://gutenberg.spiegel.de/buch/johann-wolfgang-goethe-gedichte-3670/231'
config = Config().get()

urlscrape = UrlScrape(config)
contents = urlscrape.scrap_url(url)

markovi = Markovi(config)
texts = []
for content in contents:
    for _ in range(5):
        texts.append(markovi.generate(content.__getitem__('text_raw'), 1))

pprint.pprint(texts, width=120)
