#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

version = '0.2.2'

setup(
    name='SerpScrap',
    version=version,
    description='''A python module to scrape and extract data like urls, titles, descriptions, ratings from search engine result pages
    and also the meta informations und raw text content from listed urls.''',
    long_description=open('README.md').read(),
    author='Ronald Schmidt',
    author_email='ronald.schmidt@zu-web.de',
    url='https://github.com/ecoron/SerpScrap',
    license='MIT',
    packages=find_packages(),
    dependency_links=[
        'git+git://github.com/ecoron/GoogleScraper#egg=GoogleScraper'
    ],
    install_requires=[
        'GoogleScraper',
        'chardet==2.3.0',
        'beautifulsoup4==4.4.1',
        'html2text==2016.9.19',
        'lxml==3.6.0',
    ],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Topic :: Internet',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='serp url scraper',
)
