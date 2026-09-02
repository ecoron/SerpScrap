.. image:: https://raw.githubusercontent.com/ecoron/SerpScrap/master/docs/logo.png
   :target: https://github.com/ecoron/SerpScrap
   :alt: SerpScrap

=========
SerpScrap
=========

SerpScrap retrieves structured search results through a Python package, a
command-line interface, a Docker application, and an MCP-compatible gateway.
The current release line is **2.0.0-alpha.3**.

This documentation has two audiences:

* Users run searches with Python, the CLI, the Docker UI/API, or the MCP
  server.
* Developers extend providers, services, parsers, tests, and deployment files.

Start here
==========

Choose the interface that matches your workflow:

* :doc:`install` — install the package, Chrome, and development dependencies.
* :doc:`examples` — complete Python and CLI examples.
* :doc:`cli` — all important CLI commands and options.
* :doc:`docker` — run the API, UI, PostgreSQL, MCP, SearXNG, and Valkey services
  with Compose.
* :doc:`mcp` — connect an MCP client and call search/history/configuration tools.
* :doc:`results` — understand result rows, fusion, failures, and JSON output.
* :doc:`configuration` — configure engines, markets, concurrency, caching, and
  diagnostics.
* :doc:`topic-tools` — use News and Shopping sources through one shared contract.

.. toctree::
   :caption: User guide
   :maxdepth: 3
   :numbered:

   install
   examples
   cli
   results
   configuration
   docker
   mcp
   searchengines
   topic-tools

.. toctree::
   :caption: Developer guide
   :maxdepth: 3

   development

Version and support
===================

The alpha release is suitable for evaluation and development. Provider pages
can change, access controls can produce partial failures, and live browser
checks require Chrome and network access. SerpScrap never bypasses CAPTCHAs,
rate limits, consent decisions, or access controls.

Source code and issue tracking are available on
`GitHub <https://github.com/ecoron/SerpScrap>`_.
