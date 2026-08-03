#!/usr/bin/python3
import pprint

import serpscrap

scrap = serpscrap.SerpScrap()
results = scrap.search(['privacy-friendly search engines'])

for result in results:
    pprint.pprint(result)
    print()
