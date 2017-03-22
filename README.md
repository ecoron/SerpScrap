# SerpScrap
A python module to scrape and extract data like links, titles, descriptions, ratings, from search engine result pages.
It is also possible to scrape the urls of the serp results.
the raw text data could be used with markovi a sentence text generator.

 
SerpScrap wraps a [fork](https://github.com/ecoron/GoogleScraper) of [GoogleScraper](https://github.com/NikolaiT/GoogleScraper) with several improvements.

## Install

```
pip install SerpScrap
```

### Requirements Windows

on Windows you might need also [Microsoft Visual C++ Build Tools](http://landinghub.visualstudio.com/visual-cpp-build-tools) installed.

* [lxml](http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml)
* [numpy](http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy)
* [scipy](http://www.lfd.uci.edu/~gohlke/pythonlibs/#scipy)
* [scikit-learn](http://www.lfd.uci.edu/~gohlke/pythonlibs/#scikit-learn)

## Usage

SerpScrap in your applications

```
import serpscrap

keywords = ['one', 'two']
scrap = serpscrap.SerpScrap()
scrap.init(keywords=keywords)
result = scrap.scrap_serps()
```
take also a look into the [examples folder](examples/)

To run SerpScrap via command line provide one or more keywords as searchphrase.
In this example the searchphrase is "your keywords"

```
python serpscrap\serpscrap.py -k your keywords
```

## windows user

avoid encode/decode issues by running this command before starting python in your cli

```
chcp 65001
set PYTHONIOENCODING=utf-8
```
