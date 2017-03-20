#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

version = '0.3.0'

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
    # 'lxml==3.6.0',
    install_requires=[
        'GoogleScraper==0.2.1',
        'chardet==2.3.0',
        'beautifulsoup4==4.4.1',
        'html2text==2016.9.19',
        'markovify==0.5.4',
        'libxml2'
    ],
    dependency_links=[
        'https://github.com/ecoron/GoogleScraper/tarball/master#egg=GoogleScraper-0.2.1'
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Topic :: Internet',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='serp url scraper',
)
