#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pprint
import serpscrap

keywords = ['berlin']

config = serpscrap.Config()
config.set('sel_browser', 'chrome')
config.set('executable_path', '/tmp/chromedriver_win32/chromedriver.exe')

scrap = serpscrap.SerpScrap()
scrap.init(config=config.get(), keywords=keywords)
results = scrap.run()

for result in results:
    pprint.pprint(result)
    print()
