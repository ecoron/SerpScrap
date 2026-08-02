=========
SerpScrap
=========

.. image:: https://img.shields.io/pypi/v/SerpScrap.svg
    :target: https://pypi.python.org/pypi/SerpScrap

.. image:: https://readthedocs.org/projects/serpscrap/badge/?version=latest
    :target: http://serpscrap.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: https://github.com/ecoron/SerpScrap/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/ecoron/SerpScrap/actions/workflows/ci.yml
    :alt: CI status

.. image:: https://img.shields.io/docker/pulls/ecoron/serpscrap.svg
    :target: https://hub.docker.com/r/ecoron/serpscrap

SerpScrap is a Python and Docker application for retrieving structured search
engine result pages (SERPs) for SEO and business research. It extracts URLs,
titles, snippets, rich snippets, result types, and provider outcomes, with
optional screenshots and page-text extraction.

Version 2 is currently being completely reworked. It is available as a
pre-release Docker image and from the Git repository, but it is not yet
planned for PyPI. Use a released PyPI version for stable production workflows.

Features
--------

* Extracts result types: image, news, results, shopping, videos
* For each result, you get: domain, rank, rich snippet, site links, snippet, title, type, url, visible url
* Takes a screenshot of each result page
* Optionally scrapes the text content of each result URL
* Results are returned as ``list[dict]`` and can be saved as UTF-8 JSON
* Supports using your own proxy list
* Uses a current desktop Chrome identity, paced navigation, bounded retries,
  cache-first retrieval, and explicit block/rate-limit classification

Quickstart (CLI)
-----------------

Install the released package in an isolated environment:

.. code-block:: bash

   python -m pip install SerpScrap
   serpscrap --help

This will show you the available CLI options. For a simple search, try:

.. code-block:: bash

   serpscrap search --keyword "example keyword" --output results.json
   serpscrap search --keyword "latest news" --search-type news

Use ``--log-level`` and ``--log-format`` before the command to control stderr
logging independently from JSON results on stdout:

.. code-block:: bash

   serpscrap --log-level DEBUG --log-format json search -k "example keyword"


Installation
------------

SerpScrap requires Python >= 3.10 and Google Chrome. Selenium Manager resolves
ChromeDriver automatically; controlled environments may configure explicit
Chrome and ChromeDriver paths.

.. code-block:: bash

   python -m pip install SerpScrap

For a Version 2 pre-release, use the published Docker tag or install the Git
checkout in an isolated Pipenv environment:

.. code-block:: bash

   docker pull ecoron/serpscrap:<pre-release-tag>
   git clone https://github.com/ecoron/SerpScrap.git
   cd SerpScrap
   pipenv install --dev
   pipenv run python -m pip install -e .

For more details, see the `install`_ section of the documentation.

Docker application
------------------

The Docker Compose application provides the API, PostgreSQL history store, UI,
and MCP gateway. See the `Docker guide`_ for startup, configuration,
persistent mounts, health checks, and troubleshooting. The `developer guide`_
covers repository and contribution workflows.

.. code-block:: bash

   docker compose -f docker/compose.yml up --build

Open ``http://localhost:8080`` for the UI.


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

Project status and changes
--------------------------

The current refactoring work is documented in `Refactoring Phase 9`_.
Version 2 will be published to PyPI only after the rework, quality checks, and
release decision are complete.

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
.. _`Docker guide`: http://serpscrap.readthedocs.io/en/latest/docker.html
.. _`developer guide`: http://serpscrap.readthedocs.io/en/latest/development.html
.. _`Refactoring Phase 9`: http://serpscrap.readthedocs.io/en/latest/refactoring2026.html
.. _`Chrome headless`: http://chromedriver.chromium.org/
.. _`lxml`: https://lxml.de/
.. _`beautifulsoup4`: https://www.crummy.com/software/BeautifulSoup/
.. _`GoogleScraper`: https://github.com/NikolaiT/GoogleScraper
