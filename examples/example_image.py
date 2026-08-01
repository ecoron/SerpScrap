#!/usr/bin/python3
import pprint

import serpscrap

scrap = serpscrap.SerpScrap()
results = scrap.search(['lost places'], search_type='image')

for result in results[:10]:
    pprint.pprint(result)
    print()
