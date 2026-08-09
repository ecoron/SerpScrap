=========
SerpScrap
=========

.. image:: https://img.shields.io/badge/version-2.0.0--alpha.1-orange.svg
   :target: https://github.com/ecoron/SerpScrap/releases
   :alt: Version 2.0.0-alpha.1

.. image:: https://readthedocs.org/projects/serpscrap/badge/?version=latest
   :target: https://serpscrap.readthedocs.io/en/latest/
   :alt: Documentation status

.. image:: https://img.shields.io/docker/pulls/ecoron/serpscrap.svg
   :target: https://hub.docker.com/r/ecoron/serpscrap
   :alt: Docker pulls

SerpScrap retrieves structured search results for SEO, research, and
automation. It is available as a Python package, a CLI, a Docker application,
and an MCP-compatible server. Results are JSON-compatible and preserve the
fusion rank, provider rank, source engine, URL, title, snippets, result type,
and typed failures.

Version 2.0.0-alpha.1
=====================

This is an alpha release for evaluation and development. Provider pages are
dynamic, live searches require Chrome and network access, and results can be
partial when a provider blocks, rate-limits, requests consent, or changes its
layout. SerpScrap does not bypass those controls.

Install the package
===================

.. code-block:: bash

   python -m pip install SerpScrap==2.0.0a1

For a source checkout:

.. code-block:: bash

   git clone https://github.com/ecoron/SerpScrap.git
   cd SerpScrap
   pipenv install --dev
   pipenv run python -m pip install -e .

Python example
==============

.. code-block:: python

   from serpscrap import Config, SerpScrap

   config = Config()
   config.apply({
       "search_engines": ["google", "bing"],
       "country_code": "DE",
       "num_workers": 2,
   })

   scraper = SerpScrap()
   results = scraper.search("privacy friendly search", config=config, pages=1)
   scraper.save_json("results.json", overwrite=True)

CLI example
===========

.. code-block:: bash

   serpscrap search -k "renewable energy" --search-type news \
     --engine google --engine bing --country DE --workers 2 \
     --output results.json --overwrite

The CLI keeps result JSON on stdout and progress/logging on stderr. Run
``serpscrap search --help`` for the complete option reference.

Docker application
==================

The Compose stack provides the API, PostgreSQL history, web UI, and MCP
gateway:

.. code-block:: bash

   mkdir -p data/postgres data/cache data/diagnostics data/exports logs
   docker compose -f docker/compose.yml up --build

Open ``http://localhost:8080`` for the UI, use the API at
``http://localhost:8000/api/v1``, and connect MCP clients to
``http://localhost:8001``. The standard stack also starts SearXNG at
``http://localhost:8888`` and connects SerpScrap to it internally. SearXNG is
enabled by default and can be disabled from the configuration page. See the
:doc:`docs/docker` guide for health checks, mounts, operations, and security
boundaries.

MCP server
==========

The MCP gateway exposes tools for starting searches, polling status, listing
results, inspecting history, discovering engines, and managing validated
configuration. See the :doc:`docs/mcp` guide for JSON-RPC examples and client
connection details.

Documentation map
=================

* `User guide <https://serpscrap.readthedocs.io/en/latest/examples.html>`_
  — Python and CLI examples.
* `CLI reference <https://serpscrap.readthedocs.io/en/latest/cli.html>`_
  — commands and important parameters.
* `Docker guide <https://serpscrap.readthedocs.io/en/latest/docker.html>`_
  — application deployment and operations.
* `MCP guide <https://serpscrap.readthedocs.io/en/latest/mcp.html>`_
  — gateway tools and JSON-RPC.
* `Developer guide <https://serpscrap.readthedocs.io/en/latest/development.html>`_
  — repository, tests, providers, and documentation.

Project checks
=============

.. code-block:: bash

   pipenv run python -m ruff check serpscrap scrapcore tests
   pipenv run python -m pytest -m "not browser"
   pipenv run python -m sphinx -W --keep-going -b html docs docs/_build/html

License and source
==================

Source code is available at https://github.com/ecoron/SerpScrap. The project
is licensed under the terms in ``LICENSE``.
