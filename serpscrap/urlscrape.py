#!/usr/bin/python3
# -*- coding: utf-8 -*-
import chardet
import hashlib
import html2text
import json
import re
import urllib.request

from bs4 import BeautifulSoup

class UrlScrape():

    meta_robots_pattern = re.compile(r'<meta\sname=["\']robots["\']\scontent=["\'](.*?)["\']\s/>')
    meta_title_pattern = re.compile(r'<title[^>]*>([^<]+)</title>')

    def adjust_encoding(self, data):
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
        filename = m.hexdigest()

        try:
            with open('/temp/tmpscraped/'+filename+'.json') as json_data:
                result = json.load(json_data)
                json_data.close()
            return result
        except:
            print('failed to open: '+'/tmp/tmpscraped/'+filename+'.json')
            pass

        result = {}
        with urllib.request.urlopen(url) as response:
            html = response.read()

            encoded = self.adjust_encoding(data=html)
            html = encoded['data']

            for sign in ['[', ']', '(', ')']:
                html = html.replace(sign, ' ')
            for sign in ['»']:
                html = html.replace(sign, '')

            result.update({'meta_robots': self.meta_robots_pattern.findall(html)})
            result.update({'meta_title': self.meta_title_pattern.findall(html)})
            result.update({'status': response.getcode()})
            result.update({'url': response.geturl()})
            result.update({'encoding': encoded['encoding']})

            headers = dict(response.getheaders())
            # pprint.pprint(headers)
            if 'Last-Modified' in headers.keys():
                result.update({'last_modified': headers['Last-Modified']})
            else:
                result.update({'last_modified': None})

            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True

            soup = BeautifulSoup(h.handle(html), 'html.parser')
            txt = soup.get_text()
            txt.replace('\t', ' ')
            txt.replace('\r', ' ')
            txt.replace('\n', ' ')
            txt.replace('.', '.\n')
            result.update({'text_raw': txt})

            with open('/tmp/tmpscraped/'+filename+'.json', 'w') as fp:
                json.dump(result, fp)
        return result