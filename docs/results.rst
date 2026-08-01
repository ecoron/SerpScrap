===========
Result Data
===========

``SerpScrap.search`` returns a deterministic ``list[dict]``. Every value is
directly JSON-compatible; integers, booleans, lists, and ``None`` are not
converted to strings.

.. code-block:: python

   [
       {
           'query': 'example',
           'search_engine': 'google',
           'country_code': 'DE',
           'query_num_results_total': 'About 42 results',
           'query_num_results_page': 10,
           'query_page_number': 1,
           'serp_domain': 'example.com',
           'serp_rank': 1,
           'serp_rating': None,
           'serp_source': None,
           'serp_date': None,
           'serp_price': None,
           'serp_merchant': None,
           'serp_duration': None,
           'serp_image_url': None,
           'serp_thumbnail_url': None,
           'serp_sitelinks': None,
           'serp_snippet': 'An example result.',
           'serp_title': 'Example',
           'serp_type': 'results',
           'serp_url': 'https://example.com/',
           'serp_visible_link': 'example.com',
           'screenshot': None,
       }
   ]

Multi-engine searches add ``search_engine`` and uppercase ISO 3166-1
``country_code`` to every row. Results that resolve to the same canonical URL
are fused into one row with ``relevance_score``, ``engine_match_count``,
``best_rank``, ``independent_provider_count``, and ``matched_engines``. The
fusion report uses schema version 2 and records the active market-share
snapshot and fallback weights in report metadata.

Local JSON
----------

Save the same result array atomically as UTF-8 JSON. A missing ``.json``
extension is appended. Existing files are protected unless ``overwrite=True``.

.. code-block:: python

   scraper = serpscrap.SerpScrap()
   results = scraper.search('example')
   path = scraper.save_json('results', overwrite=True)

The CLI uses the same serializer and keeps logs on stderr:

.. code-block:: bash

   serpscrap search -k "example" --output results.json --overwrite

CSV output was removed in Refactoring Phase 2. Replace ``as_csv(path)`` with
``save_json(path)``. Passing a ``.csv`` destination raises a migration error.

Failures and related keywords
-----------------------------

Successful rows remain available when another requested page fails. Details
are separate from successful rows:

.. code-block:: python

   results = scraper.search(['first query', 'second query'])
   failures = scraper.get_failures()
   related = scraper.get_related()

Each failure contains query, search engine, page, URL, category, message,
retryability, correlation ID, and request attempt count. Categories distinguish
blocking, consent, rate limiting, circuit breaking, timeout, WebDriver, browser
startup, and persistence failures. Related keywords contain ``keyword`` and
``rank``.

URL enrichment
--------------

Set ``scrape_urls=True`` to append bounded URL-response metadata to each
successful result dictionary. Enrichment uses the same effective desktop Chrome
identity, explicit headers, pooled per-origin connections, separate connect/read
timeouts, redirect/content-type/response-size limits, classified failures, and
an identity-aware atomic cache.

serp_type
---------

The parser can return organic ``results`` and engine-specific result types such
as ``image``, ``news``, ``shopping``, and ``videos`` when present in the SERP.
All types retain the common fields above. News adds source/date, shopping adds
price/merchant/rating, videos add duration/source/date, and images add image and
thumbnail URLs where Google exposes them. Missing values remain ``None``.
