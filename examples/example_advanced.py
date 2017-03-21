#!/usr/bin/python3
# -*- coding: utf-8 -*-
import serpscrap

keywords = ['computer sience']

config = serpscrap.Config()

config.set('scrape_urls', True)
config.set('num_pages_for_keyword', 2)
config.set('url_threads', 5)

scrap = serpscrap.SerpScrap()
scrap.init(config=config.get(), keywords=keywords)
results = scrap.run()

markovi = serpscrap.Markovi(config)

models = []

for result in results:
    if 'text_raw' in result and len(result['text_raw']) > 1:
        model = markovi.get_model(result['text_raw'], 3)
        if model.state_size > 0:
            models.append(model)

model = markovi.get_combined_model(models)

texts = []
for _ in range(25):
    texts.append(model.make_short_sentence(char_limit=100, tries=10, max_overlap_ratio=0.7, max_overlap_total=20))

for text in texts:
    print(text)
    print()
