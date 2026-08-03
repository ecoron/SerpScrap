#!/usr/bin/python3
import serpscrap

scrap = serpscrap.SerpScrap()
results = scrap.search(['privacy-friendly search engines'], scrape_urls=True)
scrap.save_json('/tmp/output.json', results, overwrite=True)
