#!/usr/bin/python3
# -*- coding: utf-8 -*-
import serpscrap

url = 'http://www.tagesspiegel.de/berlin/verkehr-in-berlin-umweltbundesamt-fordert-generelles-tempo-30-in-staedten/19564430.html'

config = serpscrap.Config()

urlscrape = serpscrap.UrlScrape(config.get())
results = urlscrape.scrap_url(url)

for result in results:
    print(result)
    print()
