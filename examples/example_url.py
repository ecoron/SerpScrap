#!/usr/bin/python3
import serpscrap

url = 'https://serpscrap.readthedocs.io/en/latest/'

config = serpscrap.Config()

urlscrape = serpscrap.UrlScrape(config.get())
result = urlscrape.scrap_url(url)

print(result)
print()
