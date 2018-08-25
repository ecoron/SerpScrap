#!/usr/bin/python3
# -*- coding: utf-8 -*-
import serpscrap

keywords = ['stellar']

config = serpscrap.Config()
config.set('sel_browser', 'chrome')
config.set('chrome_headless', True)
config.set('executable_path', '/tmp/chromedriver_win32/chromedriver.exe')
# for linux
# config.set('executable_path', '/usr/local/bin/chromedriver')
config.set('scrape_urls', False)

scrap = serpscrap.SerpScrap()
scrap.init(config=config.get(), keywords=keywords)
results = scrap.as_csv('/tmp/output')
