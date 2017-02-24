#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

version = '0.1.3'

setup(
    name='SerpScrap',
    version=version,
    description='A python module to scrape and extract data, like links, titles, descriptions, ratings, from search engine result pages.',
    long_description=open('README.md').read(),
    author='Ronald Schmidt',
    author_email='ronald.schmidt@zu-web.de',
    url='https://github.com/ecoron/SerpScrap',
    packages=find_packages(),
    install_requires=[
        'GoogleScraper',
        'chardet==2.3.0'
    ],
    dependency_links=[
        'git+git://github.com/ecoron/GoogleScraper#egg=GoogleScraper'
    ],
)
