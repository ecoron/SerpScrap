#!/usr/bin/python3
import serpscrap

scraper = serpscrap.SerpScrap()
results = scraper.search(["privacy-friendly search engines"])
path = scraper.save_json("/tmp/output.json", results, overwrite=True)
print(path)
