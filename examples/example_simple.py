#!/usr/bin/python3
import pprint

import serpscrap

scrap = serpscrap.SerpScrap()
results = scrap.search(['bienen'])

for result in results:
    pprint.pprint(result)
    print()
