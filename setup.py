#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

version = '0.14.0'


setup(
    name='SerpScrap',
    version=version,
    description='Python SEO scraper for extracting structured data from major search engine result pages (SERPs) using headless Chrome. Supports CLI and Docker usage.',
    long_description=open('README.rst').read(),
    author='Ronald Schmidt',
    author_email='ronald.schmidt@zu-web.de',
    doc_url='http://serpscrap.readthedocs.io/en/latest/',
    url='https://github.com/ecoron/SerpScrap',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'PySocks>=1.7.0',
        'chardet>=5.2.0',
        'beautifulsoup4>=4.12.0',
        'html2text==2025.4.15',
        'lxml>=6.0.2',
        'bleach>=6.2.0',
        'sqlalchemy>=2.0.0',
        'selenium>=4.0.0',
        'cssselect>=1.3.0',
        'chromedriver-autoinstaller>=0.6',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Internet',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
    ],
    keywords='seo, search engine, serp, scraper, web scraping, data extraction, google, automation, python, cli, docker, ad-detection, keyword research, analytics',
)
