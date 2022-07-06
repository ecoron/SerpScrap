#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

version = '0.13.0'


setup(
    name='SerpScrap',
    version=version,
    description='''
    SEO python scraper to extract data from major searchengine result pages.
    Extract data like url, title, snippet, richsnippet and the type from searchresults for given keywords. Detect Ads or make automated screenshots.
    You can also fetch text content of urls provided in searchresults or by your own.
    It's usefull for SEO and business related research tasks.
    ''',
    long_description=open('README.rst').read(),
    author='Ronald Schmidt',
    author_email='ronald.schmidt@zu-web.de',
    doc_url='http://serpscrap.readthedocs.io/en/latest/',
    url='https://github.com/ecoron/SerpScrap',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'PySocks==1.7.0',
        'chardet==3.0.4',
        'beautifulsoup4==4.8.0',
        'html2text==2019.8.11',
        'lxml==4.9.1',
        'sqlalchemy==1.3.7',
        'selenium==3.141.0',
        'cssselect==1.1.0',
    ],
    scripts=['install_chrome.sh'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Internet',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='seo scraper ad-detection scraping keywords',
)
