#!/usr/bin/python3
import pprint

import serpscrap

scraper = serpscrap.SerpScrap()
scraper.search(["stellar"])
related = [item["keyword"] for item in scraper.get_related()]

results = scraper.search(related) if related else []
scraper.save_json("/tmp/cryptocurrency.json", results, overwrite=True)
pprint.pprint(related)
