#!/usr/bin/python3
# -*- coding: utf-8 -*-
import serpscrap

url = 'https://en.wikipedia.org/wiki/Special:Random'

config = serpscrap.Config()

urlscrape = serpscrap.UrlScrape(config.get())
result = urlscrape.scrap_url(url)

print(result)
print()
