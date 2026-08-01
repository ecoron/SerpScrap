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
