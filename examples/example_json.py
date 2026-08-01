#!/usr/bin/python3
import serpscrap

scraper = serpscrap.SerpScrap()
results = scraper.search(["stellar"])
path = scraper.save_json("/tmp/output.json", results, overwrite=True)
print(path)
