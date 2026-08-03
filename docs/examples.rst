=============
Examples
=============

These examples use the public ``SerpScrap.search`` API and the current CLI.
They are offline examples of invocation and output handling; a real search
requires Chrome and network access.

Python package
==============

Basic search
------------

``search`` accepts a string or an iterable of query strings and returns a
JSON-compatible ``list[dict]``:

.. code-block:: python

   from serpscrap import SerpScrap

   scraper = SerpScrap()
   results = scraper.search("privacy friendly search")
   for row in results:
       print(row["serp_rank"], row["serp_title"], row["serp_url"])

Multiple queries, pages, and engines
------------------------------------

.. code-block:: python

   from serpscrap import Config, SerpScrap

   config = Config()
   config.apply({
       "search_engines": ["google", "bing", "duckduckgo"],
       "country_code": "DE",
       "num_pages_for_keyword": 2,
       "num_workers": 3,
       "engine_workers": 1,
   })

   scraper = SerpScrap()
   results = scraper.search(
       ["seo tools", "seo news"],
       config=config,
       pages=2,
       workers=3,
   )

Vertical searches
------------------

The supported search types are ``normal``, ``image``, ``news``, ``shopping``,
and ``videos``:

.. code-block:: python

   news = SerpScrap().search("renewable energy", search_type="news")
   images = SerpScrap().search("alpine lakes", search_type="image")
   shopping = SerpScrap().search("mechanical keyboard", search_type="shopping")

JSON files and URL enrichment
-----------------------------

Write results during a search or save the most recent result list afterward:

.. code-block:: python

   scraper = SerpScrap()
   results = scraper.search(
       "blockchain",
       scrape_urls=True,
       output="results/blockchain.json",
       overwrite=True,
   )
   scraper.save_json("results/blockchain-copy.json", results, overwrite=True)

``scrape_urls=True`` adds bounded metadata from result pages. It does not
silently ignore HTTP failures; enrichment failures remain diagnosable.

Failures and related searches
-----------------------------

Partial provider failures do not discard successful rows:

.. code-block:: python

   scraper = SerpScrap()
   results = scraper.search(["first query", "second query"])
   print(scraper.get_related())
   for failure in scraper.get_failures():
       print(failure["search_engine"], failure["category"], failure["message"])

Configuration and diagnostics
-----------------------------

Use the same settings from Python that are available through the CLI:

.. code-block:: python

   config = Config()
   config.apply({
       "progress": True,
       "progress_format": "jsonl",
       "diagnostic_html": True,
       "diagnostic_dir": "logs/diagnostics",
       "consent_action": "necessary",
       "store_history": False,
       "do_caching": True,
   })
   results = SerpScrap().search("selector troubleshooting", config=config)

Diagnostics contain redacted rendered HTML and should be treated as local,
temporary troubleshooting data.

Command line
============

.. code-block:: bash

   serpscrap search -k "seo tools" -k "seo news" --pages 2 \
     --engine google --engine bing --country DE --workers 2

   serpscrap search -k "renewable energy" --search-type news \
     --output results.json --overwrite

   serpscrap search -k "provider diagnosis" --engine xprivo \
     --progress-format jsonl --diagnostic-html \
     > results.json 2> progress.jsonl

See :doc:`cli` for the complete option reference and :doc:`results` for the
result schema.

MCP server
==========

Start the Compose MCP gateway and use an MCP client to call
``start_search``, ``get_search_status``, and ``list_results``. The gateway also
exposes history analytics, engine discovery, and validated configuration tools.
See :doc:`mcp` for the JSON-RPC request examples and safety notes.
