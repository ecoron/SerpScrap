=============
Example Usage
=============

Direct Python API
-----------------

A normal search requires one method call and returns ``list[dict]``:

.. code-block:: python

   import serpscrap

   scraper = serpscrap.SerpScrap()
   results = scraper.search(['seo tools', 'seo news'], pages=2, workers=2)

   for result in results:
       print(result['serp_rank'], result['serp_title'], result['serp_url'])

The Phase 1 ``init()`` followed by ``run()`` remains available as a compatibility
adapter. New code should use ``search()``.

Save JSON locally
-----------------

.. code-block:: python

   scraper = serpscrap.SerpScrap()
   results = scraper.search('stellar')
   output_path = scraper.save_json('/tmp/stellar-results', overwrite=True)

You can also save during the request:

.. code-block:: python

   results = scraper.search(
       'stellar',
       output='/tmp/stellar-results.json',
       overwrite=True,
   )

Image search
------------

.. code-block:: python

   results = serpscrap.SerpScrap().search(
       'lost places',
       search_type='image',
   )

Other Google verticals
----------------------

Use ``news``, ``shopping``, or ``videos`` in the same way. Mixed normal pages
are also classified into their actual result types.

.. code-block:: python

   news = serpscrap.SerpScrap().search(
       'renewable energy',
       search_type='news',
   )

Result URL content
------------------

.. code-block:: python

   results = serpscrap.SerpScrap().search(
       'blockchain',
       scrape_urls=True,
   )

Related keywords and failures
-----------------------------

.. code-block:: python

   scraper = serpscrap.SerpScrap()
   results = scraper.search('example')
   related = scraper.get_related()
   failures = scraper.get_failures()

CLI
---

JSON results are written to stdout while logs remain on stderr. ``--output``
saves the same JSON array locally.

.. code-block:: bash

   serpscrap search -k "seo tools" -k "seo news" --pages 2
   serpscrap search -k "renewable energy" --search-type news
   serpscrap search -k "seo tools" --output results.json --overwrite

Use ``--no-cache`` or ``--no-history`` when those local artifacts are not
desired.

Configured multi-engine run
----------------------------

The Python API accepts the same settings as the CLI. This example limits the
global concurrency to four requests and allows only one request per provider:

.. code-block:: python

   from serpscrap import Config, SerpScrap

   config = Config()
   config.apply({
       'search_engines': ['bing', 'yandex', 'duckduckgo', 'mojeek'],
       'country_code': 'DE',
       'num_pages_for_keyword': 2,
       'num_results_per_page': 10,
       'num_workers': 4,
       'engine_workers': 1,
       'engine_workers_by_engine': {'bing': 1, 'mojeek': 1},
       'store_history': False,
       'do_caching': True,
   })

   scraper = SerpScrap()
   results = scraper.search(['preisfehler', 'herrenschuhe'], config=config)
   failures = scraper.get_failures()

Progress and rendered diagnostics
----------------------------------

Progress is written to stderr, so stdout remains a valid result JSON stream.
Rendered HTML capture is disabled unless explicitly requested:

.. code-block:: bash

   serpscrap search -k "preisfehler" \
     --engine brave --engine ecosia --workers 2 \
     --progress --progress-format text \
     --diagnostic-html --diagnostic-dir logs/phase7

The run manifest is written below ``logs/phase7/<run_id>/manifest.json``. For
machine processing, use JSON Lines and separate the streams:

.. code-block:: bash

   serpscrap search -k "preisfehler" --progress-format jsonl \
     > results.json 2> progress.jsonl

The diagnostic artifacts are redacted and size-limited, but they still contain
rendered third-party page content. Review them locally and remove them after
selector analysis.
Consent dialogs use the privacy-preserving default automatically. To make the
choice explicit, use ``--consent-action necessary`` (equivalent to rejecting
all optional cookies) or disable automation with ``--consent-action disabled``
for diagnostic runs.
