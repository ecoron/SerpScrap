#!/usr/bin/python3
# -*- coding: utf-8 -*-
import serpscrap

keywords = ['news']

config = serpscrap.Config()

config.set('scrape_urls', False)
config.set('num_pages_for_keyword', 5)
config.set('url_threads', 5)

scrap = serpscrap.SerpScrap()
scrap.init(config=config.get(), keywords=keywords)
results = scrap.run()

markovi = serpscrap.Markovi(config)

models = []

print('--- origin titles ---')
for result in results:
    if 'serp_title' in result and len(result['serp_title']) > 1:
        print(result['serp_title'])
        try:
            model = markovi.get_model(result['serp_title'], 1)
            if model.state_size > 0:
                models.append(model)
        except Exception:
            pass
print('--- --- ---')

model = markovi.get_combined_model(models)

texts = []
for _ in range(len(results)):
    text = model.make_sentence(
        char_limit=150,
        tries=10,
        max_overlap_ratio=0.7,
        max_overlap_total=20
    )
    if isinstance(text, str):
        texts.append(text)

print('--- Generated Titles 1. iteration ---')
for text in texts:
    print(text)
print('--- --- ---')

tf = serpscrap.TfIdf().get_tfidf(texts)
print('--- TfIdf Titles ---')
print(tf)
print('--- --- ---')

model = markovi.get_model("\n".join(texts), 1)
print('--- Generated Titles 2. iteration ---')
for _ in range(10):
    text = model.make_short_sentence(
        max_chars=80,
        tries=10,
        max_overlap_ratio=0.7,
        max_overlap_total=20
    )
    if text is not None:
        print(text)
