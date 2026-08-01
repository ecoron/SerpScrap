#!/usr/bin/python3
"""SerpScrap.UrlScrape"""
import hashlib
import json
import os
import re
import urllib.request

import chardet


class UrlScrape:
    """Fetches and caches web pages, extracts metadata, and handles encoding."""

    meta_robots_pattern = re.compile(r'<meta\sname=["\']robots["\']\scontent=["\'](.*?)["\']\s/>')
    meta_title_pattern = re.compile(r'<title[^>]*>([^<]+)</title>')

    def __init__(self, config=None):
        self.cache_dir = config['cachedir']
        self.url_threads = config['url_threads']
        self.results = []
        self.assure_path_exists(self.cache_dir)

    @staticmethod
    def assure_path_exists(cache_dir: str):
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    @staticmethod
    def adjust_encoding(data: bytes) -> dict:
        """Detect and adjust encoding of data, return data decoded to utf-8."""
        check_encoding = chardet.detect(data)
        if 'utf-8' not in check_encoding['encoding']:
            try:
                data = data.decode(check_encoding['encoding']).encode('utf-8')
            except Exception:
                pass
        try:
            data = data.decode('utf-8')
        except Exception:
            data = data.decode('utf-8', 'ignore')
        return {'encoding': check_encoding['encoding'], 'data': data}

    def scrap_url(self, url: str) -> dict:
        """Fetch a URL, cache the result, and extract metadata."""
        m = hashlib.md5()
        m.update(url.encode('utf-8'))
        cache_file = os.path.join(self.cache_dir, m.hexdigest() + '.json')
        result = None
        try:
            with open(cache_file) as json_data:
                result = json.load(json_data)
                self.results.append(result)
        except Exception:
            try:
                result = self.fetch_url(url, cache_file)
                self.results.append(result)
            except Exception:
                result = {'status': 'error', 'url': url}
        return result

    @staticmethod
    def fetch_url(url: str, cache_file: str) -> dict:
        """Fetch a URL and cache the result as JSON."""
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
                meta_robots = UrlScrape.meta_robots_pattern.findall(html)
                meta_title = UrlScrape.meta_title_pattern.findall(html)
                result['meta_robots'] = meta_robots[0][0:15] if meta_robots else ''
                result['meta_title'] = meta_title[0] if meta_title else ''
                result['status'] = response.getcode()
                result['url'] = response.geturl()
                result['encoding'] = encoded['encoding']
                headers = dict(response.getheaders())
                result['last_modified'] = headers.get('Last-Modified')
                # Save to cache
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f)
        except Exception as e:
            result = {'status': 'error', 'url': url, 'error': str(e)}
        return result

ascii_lowercase = "abcdefghijklmnopqrstuvwxyz"
ascii_uppercase = ascii_lowercase.upper()

# States w/ with thanks to https://github.com/unitedstates/python-us
# Titles w/ thanks to https://github.com/nytimes/emphasis and @donohoe
abbr_capped = "|".join([
    "ala|ariz|ark|calif|colo|conn|del|fla|ga|ill|ind|kan|ky|la|md|mass|mich|minn|miss|mo|mont|neb|nev|okla|ore|pa|tenn|vt|va|wash|wis|wyo", # States
    "u.s",
    "mr|ms|mrs|msr|dr|gov|pres|sen|sens|rep|reps|prof|gen|messrs|col|sr|jf|sgt|mgr|fr|rev|jr|snr|atty|supt|hr", # Titles
    "ave|blvd|st|rd|hwy", # Streets
    "jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec", # Months
    "|".join(ascii_lowercase) # Initials
]).split("|")

abbr_lowercase = "etc|v|vs|viz|al|pct"

exceptions = "U.S.|U.N.|E.U.|F.B.I.|C.I.A.".split("|")


def is_abbreviation(dotted_word):
    clipped = dotted_word[:-1]
    if clipped[0] in ascii_uppercase:
        if clipped.lower() in abbr_capped:
            return True
        else:
            return False
    else:
        if clipped in abbr_lowercase:
            return True
        else:
            return False


def is_sentence_ender(word):
    if word in exceptions:
        return False
    if word[-1] in ["?", "!", " .", " ."]:
        return True
    if len(re.sub(r"[^A-Z]", "", word)) > 1:
        return True
    if word[-1] == "." and (not is_abbreviation(word)):
        return True
    return False


def split_into_sentences(text):
    potential_end_pat = re.compile(r"".join([
        r"([\w\.'’&\]\)]+[\.\?!])",  # A word that ends with punctuation
        r"([‘’“”'\"\)\]]*)",  # Followed by optional quote/parens/etc
        r"(\s+(?![a-z\-–—]))",  # Followed by whitespace + non-(lowercase or dash)
        ]),
        re.U
    )
    dot_iter = re.finditer(potential_end_pat, text)
    end_indices = [
        (x.start() + len(x.group(1)) + len(x.group(2)))
        for x in dot_iter
        if is_sentence_ender(x.group(1))
    ]
    spans = zip([None] + end_indices, end_indices + [None], strict=True)
    sentences = [
        text[start:end].strip() for start, end in spans
    ]
    return sentences
