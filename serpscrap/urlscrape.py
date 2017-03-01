#!/usr/bin/python3
# -*- coding: utf-8 -*-
import chardet
import concurrent.futures
import hashlib
import html2text
import json
import re
import urllib.request
import os
from bs4 import BeautifulSoup


class UrlScrape():

    meta_robots_pattern = re.compile(r'<meta\sname=["\']robots["\']\scontent=["\'](.*?)["\']\s/>')
    meta_title_pattern = re.compile(r'<title[^>]*>([^<]+)</title>')
    results = []

    def __init__(self, config=None):
        self.cache_dir = config['cachedir']
        self.url_threads = config['url_threads']
        UrlScrape.assure_path_exists(self.cache_dir)

    @staticmethod
    def assure_path_exists(cache_dir):
        cache_dir = os.path.dirname(cache_dir)
        if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)

    @staticmethod
    def adjust_encoding(data):
        """detect and adjust encoding of data return data decoded to utf-8"""
        check_encoding = chardet.detect(data)
        if 'utf-8' not in check_encoding['encoding']:
            try:
                data = data.decode(check_encoding['encoding']).encode('utf-8')
            except:
                pass
        try:
            data = data.decode('utf-8')
        except:
            data = data.decode('utf-8', 'ignore')
        return {'encoding': check_encoding['encoding'], 'data': data}

    def scrap_url(self, url):
        m = hashlib.md5()
        m.update(url.encode('utf-8'))
        cache_file = os.path.join(self.cache_dir, m.hexdigest() + '.json')

        try:
            with open(cache_file) as json_data:
                result = json.load(json_data)
                json_data.close()
            return result
        except:
            pass

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.url_threads) as executor:
                executor.submit(UrlScrape.fetch_url, url, cache_file)
        except:
            pass
        return UrlScrape.results

    @staticmethod
    def fetch_url(url, cache_file):
        result = {}
        try:
            with urllib.request.urlopen(url) as response:
                html = response.read()

                encoded = UrlScrape.adjust_encoding(data=html)
                html = encoded['data']

                for sign in ['[', ']', '(', ')']:
                    html = html.replace(sign, ' ')
                for sign in ['»']:
                    html = html.replace(sign, '')

                result.update({'meta_robots': UrlScrape.meta_robots_pattern.findall(html)})
                result.update({'meta_title': UrlScrape.meta_title_pattern.findall(html)})
                result.update({'status': response.getcode()})
                result.update({'url': response.geturl()})
                result.update({'encoding': encoded['encoding']})

                headers = dict(response.getheaders())
                if 'Last-Modified' in headers.keys():
                    result.update({'last_modified': headers['Last-Modified']})
                else:
                    result.update({'last_modified': None})

                h = html2text.HTML2Text()
                h.ignore_links = True
                h.ignore_images = True

                txt = BeautifulSoup(h.handle(html), 'html.parser').get_text()
                result.update({'text_raw': txt})

                with open(cache_file, 'w') as fp:
                    json.dump(result, fp)
        except:
            pass
        UrlScrape.results.append(result)
