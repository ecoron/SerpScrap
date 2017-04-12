#!/usr/bin/python3
# -*- coding: utf-8 -*-
import serpscrap

keywords = ['seo trends', 'seo news', 'seo tools']

config = serpscrap.Config()
config.set('scrape_method', 'selenium')
config.set('sel_browser', 'phantomjs'),
# change the path to your phantomjs binary, in this example we use the windows binary
config.set('executable_path', '../phantomjs/phantomjs.exe'),
# slowly increase the number of workers
config.set('num_workers', 1)
config.set('scrape_urls', False)

scrap = serpscrap.SerpScrap()
scrap.init(config=config.get(), keywords=keywords)
results = scrap.run()

texts = []
for result in results:
    if 'serp_title' in result and len(result['serp_title']) > 1:
        texts.append(result['serp_title'])

keywords = []
if len(texts) > 0:
    tf = serpscrap.TfIdf().get_tfidf(texts)

    for word in tf[0:15]:
        keywords.append(word['word'])

    print(keywords)

    scrap = serpscrap.SerpScrap()
    scrap.init(config=config.get(), keywords=keywords)
    results = scrap.run()

for result in results:
    if 'serp_title' in result and len(result['serp_title']) > 1:
        print(result['serp_title'])
