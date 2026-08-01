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

SerpScrap is a Python SEO scraper to extract data from major search engine result pages (SERPs).
It extracts data such as URL, title, snippet, rich snippet, and type for given keywords. It can detect ads, take automated screenshots, and fetch the text content of URLs found in search results or provided by you.

SerpScrap is useful for SEO and business research tasks.

Features
--------

* Extracts result types: ads_main, image, news, results, shopping, videos
* For each result, you get: domain, rank, rich snippet, site links, snippet, title, type, url, visible url
* Takes a screenshot of each result page
* Optionally scrapes the text content of each result URL
* Results are returned as ``list[dict]`` and can be saved as UTF-8 JSON
* Supports using your own proxy list

Quickstart Example (CLI)
-----------------------

Install SerpScrap into a virtual environment:

.. code-block:: bash

   python -m pip install .
   serpscrap --help

This will show you the available CLI options. For a simple search, try:

.. code-block:: bash

   serpscrap search --keyword "example keyword" --output results.json

Use ``--log-level`` and ``--log-format`` before the command to control stderr
logging independently from JSON results on stdout:

.. code-block:: bash

   serpscrap --log-level DEBUG --log-format json search -k "example keyword"


Install
-------

SerpScrap requires Python >= 3.10 and Google Chrome. Selenium Manager resolves
ChromeDriver automatically; controlled environments may configure explicit
Chrome and ChromeDriver paths.

.. code-block:: bash

   python -m pip install .

For more details, see the `install`_ section of the documentation.


Usage in Python
===============

.. code-block:: python
  
  import serpscrap
  
  scraper = serpscrap.SerpScrap()
  results = scraper.search(['example'])
  scraper.save_json('results.json', overwrite=True)
  
  for result in results:
      print(result)

For more details, see the `examples`_ section of the documentation.

To avoid encoding issues in the Windows CLI, use:

.. code-block:: bash

   chcp 65001
   set PYTHONIOENCODING=utf-8

.. image:: https://raw.githubusercontent.com/ecoron/SerpScrap/master/docs/logo.png
    :target: https://github.com/ecoron/SerpScrap

Supported OS
------------

* SerpScrap works on Linux, Windows, and macOS with Python >= 3.10
* Requires Google Chrome; ChromeDriver is managed by Selenium by default
* Not supported on iOS

Changes
-------
For the full changelog, see the file `CHANGELOG.md` in the repository root.

References
----------

SerpScrap uses `Chrome headless`_ and `lxml`_ to scrape SERP results. For raw text contents of fetched URLs, it uses `beautifulsoup4`_.
The core was based on `GoogleScraper`_, an outdated project, and has many improvements.

.. target-notes::

.. _`install`: http://serpscrap.readthedocs.io/en/latest/install.html
.. _`examples`: http://serpscrap.readthedocs.io/en/latest/examples.html
.. _`Chrome headless`: http://chromedriver.chromium.org/
.. _`lxml`: https://lxml.de/
.. _`beautifulsoup4`: https://www.crummy.com/software/BeautifulSoup/
.. _`GoogleScraper`: https://github.com/NikolaiT/GoogleScraper
