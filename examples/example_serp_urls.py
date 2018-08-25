#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pprint
import serpscrap

keywords = ['corfu']

config = serpscrap.Config()
config.set('sel_browser', 'chrome')
config.set('chrome_headless', True)
config.set('executable_path', '/tmp/chromedriver_win32/chromedriver.exe')
config.set('scrape_urls', True)

scrap = serpscrap.SerpScrap()
scrap.init(config=config.get(), keywords=keywords)
scrap.as_csv('/tmp/output')