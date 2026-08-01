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
           'query_num_results_total': 'About 42 results',
           'query_num_results_page': 10,
           'query_page_number': 1,
           'serp_domain': 'example.com',
           'serp_rank': 1,
           'serp_rating': None,
           'serp_sitelinks': None,
           'serp_snippet': 'An example result.',
           'serp_title': 'Example',
           'serp_type': 'results',
           'serp_url': 'https://example.com/',
           'serp_visible_link': 'example.com',
           'screenshot': None,
       }
   ]

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
retryability, and correlation ID. Related keywords contain ``keyword`` and
``rank``.

URL enrichment
--------------

Set ``scrape_urls=True`` to append URL metadata and raw text fields to each
successful result dictionary.

serp_type
---------

The parser can return organic ``results`` and engine-specific result types such
as ``image``, ``news``, ``shopping``, and ``videos`` when present in the SERP.
