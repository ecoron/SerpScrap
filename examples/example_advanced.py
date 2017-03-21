#!/usr/bin/python3
# -*- coding: utf-8 -*-
import serpscrap

keywords = ['python tutorial nltk']

config = serpscrap.Config()
config.set('scrape_urls', True)
scrap = serpscrap.SerpScrap()
scrap.init(config=config.get(), keywords=keywords)
results = scrap.run()

markovi = serpscrap.Markovi(config)

models = []
for result in results:
    if 'text_raw' in result:
        model = markovi.get_model(result['text_raw'], 3)
        if model.state_size > 0:
            models.append(model)

model = markovi.get_combined_model(models)

texts = []
for _ in range(25):
    texts.append(model.make_sentence(tries=55, max_overlap_ratio=0.7, max_overlap_total=25))

for text in texts:
    print(text)
    print()
