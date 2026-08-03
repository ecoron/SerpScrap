#!/usr/bin/python3
import pprint

import serpscrap

scraper = serpscrap.SerpScrap()
scraper.search(["privacy-friendly search engines"])
related = [item["keyword"] for item in scraper.get_related()]

results = scraper.search(related) if related else []
scraper.save_json("/tmp/privacy-friendly-search-engines.json", results, overwrite=True)
pprint.pprint(related)
