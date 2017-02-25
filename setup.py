#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

version = '0.1.4'

setup(
    name='SerpScrap',
    version=version,
    description='A python module to scrape and extract data like links, titles, descriptions, ratings, from search engine result pages.',
    long_description=open('README.md').read(),
    author='Ronald Schmidt',
    author_email='ronald.schmidt@zu-web.de',
    url='https://github.com/ecoron/SerpScrap',
    packages=find_packages(),
    dependency_links=[
        'git+git://github.com/ecoron/GoogleScraper#egg=GoogleScraper'
    ],
    install_requires=[
        'GoogleScraper',
        'chardet==2.3.0',
        'beautifulsoup4==4.4.1',
        'html2text==2016.4.2',
    ],
)
