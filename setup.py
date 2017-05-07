#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

version = '0.6.0'


setup(
    name='SerpScrap',
    version=version,
    description='''
    A python scraper to extract and analyze data from
    search engine result pages and urls.
    Extract data, like url, title, snippet
    of results or ratings for given keywords.
    ''',
    long_description=open('README.rst').read(),
    author='Ronald Schmidt',
    author_email='ronald.schmidt@zu-web.de',
    doc_url='http://serpscrap.readthedocs.io/en/latest/',
    url='https://github.com/ecoron/SerpScrap',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'PySocks==1.6.7',
        'chardet==3.0.2',
        'beautifulsoup4==4.6.0',
        'html2text==2016.9.19',
        'markovify==0.6.0',
        'numpy==1.12.1',
        'scipy==0.19.0',
        'scikit-learn==0.18.1',
        'lxml',
        'sqlalchemy==1.0.12',
        'selenium==3.4.1',
        'cssselect==1.0.1',
        'requests==2.13.0',
        'aiohttp==0.21.5',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Internet',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='serp-scraper url-scraper text-analyzer',
)
