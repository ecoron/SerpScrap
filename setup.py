#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

version = '0.3.9'

requirements = [r for r in open('requirements.txt', 'r').read().split('\n') if r]

setup(
    name='SerpScrap',
    version=version,
    description='''
    A python module to scrape, extract, analyze data from
    search engine result pages and urls.
    Extract data, like url, title, snippet
    of results or ratings for given keywords.
    ''',
    long_description=open('README.rst').read(),
    author='Ronald Schmidt',
    author_email='ronald.schmidt@zu-web.de',
    url='https://github.com/ecoron/SerpScrap',
    license='MIT',
    packages=find_packages(),
    dependency_links=[
        'git+https://github.com/ecoron/GoogleScraper.git#egg=GoogleScraper-0.3.1'
    ],
    install_requires=[
        'GoogleScraper==0.3.1',
        'chardet==2.3.0',
        'beautifulsoup4==4.5.3',
        'html2text==2016.9.19',
        'markovify==0.5.4',
        'numpy==1.12.1',
        'scipy==0.19.0',
        'scikit-learn==0.18.1',
        'lxml'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Internet',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='serp-scraper url-scraper text-analyzer',
)
