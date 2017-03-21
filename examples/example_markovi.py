#!/usr/bin/python3
# -*- coding: utf-8 -*-
from serpscrap.markovi import Markovi
from serpscrap.config import Config
from serpscrap.urlscrape import UrlScrape
import pprint


url = 'https://de.wikipedia.org/wiki/Geschichte_Berlins'
config = Config().get()

urlscrape = UrlScrape(config)
content = urlscrape.scrap_url(url)

markovi = Markovi(config)
texts = []
for _ in range(5):
    texts.append(markovi.generate_short(content.__getitem__('text_raw'), 1, 120))

pprint.pprint(texts)
