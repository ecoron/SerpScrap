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

.. image:: https://img.shields.io/docker/pulls/ecoron/serpscrap.svg
    :target: https://hub.docker.com/r/ecoron/serpscrap

SerpScrap is a Python tool for extracting structured search engine result pages (SERPs).
It collects URLs, titles, snippets, rich snippets, and result types for your keywords. It can also detect ads, take automated screenshots, and fetch the text content of result URLs.

SerpScrap is ideal for SEO and business research tasks.

Features
--------

* Extracts organic and image search results
* For each result, you get: domain, rank, rich snippet, site links, snippet, title, type, url, visible url
* Optionally takes a diagnostic screenshot of each result page
* Optionally scrapes the text content of each result URL
* Results are returned as JSON-compatible dictionaries and can be saved as JSON
* Supports using your own proxy list
* Uses Google Chrome (headless) for browser-based capture
* Supports configurable multi-engine searches with bounded concurrency

Quickstart Example
------------------

Install the package and inspect the CLI:

.. code-block:: bash

   python -m pip install .
   serpscrap --help

To run a simple search:

.. code-block:: bash

   serpscrap search --keyword "example keyword" --output results.json

For more details, see the install and usage sections.

Ressources
==========

See https://serpscrap.readthedocs.io/en/latest/ for documentation.

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
   searchengines
   refactoring2026
   changelog-refactoring2026


Usage
=====

SerpScrap in your applications

.. code-block:: python

   import serpscrap
   
   scraper = serpscrap.SerpScrap()
   results = scraper.search(['one', 'two'])

More details are available in the :doc:`examples` section of the documentation.

Supported OS
------------

* SerpScrap supports Linux, Windows, and macOS with Python >= 3.10
* SerpScrap requires Google Chrome; Selenium Manager resolves ChromeDriver
* Doesn't work on iOS

Changes
=======
For the full changelog, see the file ``CHANGELOG.md`` in the repository root.

References
==========

SerpScrap is using `Chrome headless`_ and `lxml`_ to scrape serp results. For raw text contents of fetched URL's, it is using `beautifulsoup4`_ . The scrapcore was based on `GoogleScraper`_ , an outdated project, and has many changes and improvements.

.. target-notes::

.. _`install`: https://serpscrap.readthedocs.io/en/latest/install.html
.. _`Chrome headless`: https://chromedriver.chromium.org/
.. _`lxml`: https://lxml.de/
.. _`beautifulsoup4`: https://www.crummy.com/software/BeautifulSoup/
.. _`GoogleScraper`: https://github.com/NikolaiT/GoogleScraper
