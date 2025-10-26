.. image:: https://raw.githubusercontent.com/ecoron/SerpScrap/master/docs/logo.png
    :target: https://github.com/ecoron/SerpScrap

=========
SerpScrap
=========

.. image:: https://img.shields.io/pypi/v/SerpScrap.svg
    :target: https://pypi.python.org/pypi/SerpScrap

.. image:: https://readthedocs.org/projects/serpscrap/badge/?version=latest
    :target: http://serpscrap.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: https://travis-ci.org/ecoron/SerpScrap.svg?branch=master
    :target: https://travis-ci.org/ecoron/SerpScrap

.. image:: https://img.shields.io/docker/pulls/ecoron/serpscrap.svg
    :target: https://hub.docker.com/r/ecoron/serpscrap

SerpScrap is a Python tool for extracting SEO data from major search engine result pages (SERPs).
It collects URLs, titles, snippets, rich snippets, and result types for your keywords. It can also detect ads, take automated screenshots, and fetch the text content of result URLs.

SerpScrap is ideal for SEO and business research tasks.

Features
--------

* Extracts result types: ads_main, image, news, results, shopping, videos
* For each result, you get: domain, rank, rich snippet, site links, snippet, title, type, url, visible url
* Takes a screenshot of each result page
* Optionally scrapes the text content of each result URL
* Results can be saved as CSV for analytics
* Supports using your own proxy list
* Only supports Google Chrome (headless)

Quickstart Example
------------------

The recommended way to use SerpScrap is with pipenv:

.. code-block:: bash

   pip install pipenv
   pipenv install --dev
   pipenv run python -m serpscrap.cli --help

To run a simple search:

.. code-block:: bash

   pipenv run python -m serpscrap.cli --keywords "example keyword"

For more details, see the install and usage sections.

Ressources
==========

See http://serpscrap.readthedocs.io/en/latest/ for documentation.

Source is available at https://github.com/ecoron/SerpScrap


Contents
--------
.. toctree::
   :maxdepth: 2
   
   install
   results
   configuration
   docker
   examples
   ressources


Usage
=====

SerpScrap in your applications

.. code-block:: python

   import serpscrap
   
   keywords = ['one', 'two']
   scrap = serpscrap.SerpScrap()
   scrap.init(keywords=keywords)
   result = scrap.scrap_serps()

More detailes in the `examples`_ section of the documentation.

Supported OS
------------

* SerpScrap should work on Linux, Windows and Mac OS with installed Python >= 3.4
* SerpScrap requieres lxml
* Doesn't work on iOS

Changes
=======
For the full changelog, see the file `CHANGELOG.md` in the repository root.

References
==========

SerpScrap is using `Chrome headless`_ and `lxml`_ to scrape serp results. For raw text contents of fetched URL's, it is using `beautifulsoup4`_ . The scrapcore was based on `GoogleScraper`_ , an outdated project, and has many changes and improvements.

.. target-notes::

.. _`install`: http://serpscrap.readthedocs.io/en/latest/install.html
.. _`examples`: http://serpscrap.readthedocs.io/en/latest/examples.html
.. _`Chrome headless`: http://chromedriver.chromium.org/
.. _`lxml`: https://lxml.de/
.. _`beautifulsoup4`: https://www.crummy.com/software/BeautifulSoup/
.. _`GoogleScraper`: https://github.com/NikolaiT/GoogleScraper
.. _`examples`: http://serpscrap.readthedocs.io/en/latest/examples.html
