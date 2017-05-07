#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pprint

from serpscrap.config import Config
from serpscrap.markovi import Markovi
from serpscrap.urlscrape import UrlScrape


url = 'http://gutenberg.spiegel.de/buch/johann-wolfgang-goethe-gedichte-3670/231'
config = Config().get()

urlscrape = UrlScrape(config)
contents = urlscrape.scrap_url(url)

markovi = Markovi(config)
texts = []
for content in contents:
    for _ in range(5):
        texts.append(markovi.generate(content.__getitem__('text_raw'), 1))

for text in texts:
    pprint.pprint(text, width=120)
