=============
Configuration
=============

``Config`` retains dictionary access for Phase 1 compatibility. New code can
pass friendly options directly to ``SerpScrap.search``. Settings are copied and
validated once for every independent request.

Core settings
-------------

* ``search_engines``: ordered list of registered engines, for example
  ``['google', 'bing', 'duckduckgo']``.
* ``search_type``: ``normal``, ``image``, ``news``, ``shopping``, or ``videos``.
* ``num_pages_for_keyword``: positive page count per query.
* ``num_results_per_page``: positive value up to 100.
* ``num_workers``: maximum concurrent search-engine requests. Set it to ``4``
  to cap a multi-engine run at four simultaneous requests.
* ``engine_workers``: optional per-engine ceiling; it must not exceed
  ``num_workers``. ``engine_workers_by_engine`` can provide individual limits.
* ``chrome_headless``: use headless Chrome; defaults to ``True``.
* ``chrome_binary``: optional explicit Chrome executable.
* ``executable_path``: optional explicit ChromeDriver executable. Empty uses Selenium Manager.
* ``page_load_timeout``: WebDriver navigation timeout in seconds.
* ``wait_timeout``: maximum wait for a recognizable SERP state.
* ``user_agent``: optional explicit desktop Chrome identity. Empty resolves a
  user agent matching the installed Chrome major version, with a maintained
  current Chrome fallback when detection is unavailable.
* ``request_delay_min`` and ``request_delay_max``: jittered delay range between
  Google navigations; no delay is added before the first navigation.
* ``request_retry_limit``: bounded retries for transient timeout/WebDriver
  failures. Blocking, CAPTCHA, consent, and rate-limit outcomes are not retried.
* ``request_backoff_base`` and ``request_backoff_max``: exponential retry delay
  bounds.
* ``block_threshold``: explicit block/rate-limit outcomes that open the shared
  run circuit breaker and stop new navigation.
* ``window_width`` and ``window_height``: Chrome viewport dimensions.
* ``language``: Google ``hl`` query parameter.
* ``screenshot``: save diagnostic screenshots; defaults to ``False``.
* ``dir_screenshot``: base directory for screenshots.
* ``do_caching`` and ``cachedir``: enable and locate captured-HTML caching.
* ``store_history``: persist SQLite run history; defaults to ``True``.
* ``database_name``: SQLite history path without the ``.db`` suffix.
* ``scrape_urls``: fetch the text content of parsed result URLs.
* ``url_connect_timeout`` and ``url_read_timeout``: URL-enrichment network
  timeout settings.
* ``url_max_redirects`` and ``url_max_response_bytes``: enrichment response
  safety bounds.

Example
-------

.. code-block:: python

   import serpscrap

   scraper = serpscrap.SerpScrap()
   results = scraper.search(
       ['example query'],
       pages=2,
       workers=2,
       screenshots=True,
       store_history=False,
   )

Multiple search engines with at most four concurrent requests can be selected
through ``Config``. The same settings are used by the Python API and the CLI;
one failed provider does not discard successful results from the others.

.. code-block:: python

   from serpscrap import Config, SerpScrap

   config = Config()
   config.apply({
       'search_engines': ['google', 'bing', 'duckduckgo', 'ecosia'],
       'country_code': 'DE',
       'num_pages_for_keyword': 1,
       'num_results_per_page': 10,
       'num_workers': 4,
       'engine_workers': 1,
   })

   scraper = SerpScrap()
   results = scraper.search(['privacy-friendly search'], config=config)

The equivalent CLI invocation is:

.. code-block:: bash

   serpscrap search -k "privacy-friendly search" \
     --engine google --engine bing --engine duckduckgo --engine ecosia \
     --country DE --workers 4

Cache, SQLite history, screenshots, and JSON output are independent. JSON
output is selected with ``output=`` or ``save_json()`` rather than a Config
key. The removed ``output_filename`` and ``print_results`` settings raise a
migration error.

Proxy file
----------

Set ``use_own_ip`` to ``False`` and provide ``proxy_file``. Each non-comment
line uses one of these formats:

.. code-block:: text

   http 192.0.2.10:8080
   socks5 192.0.2.11:1080

Authenticated proxies are rejected by the Chrome factory because they require
an external extension. They are not silently started without authentication.

Request policy
--------------

The defaults deliberately favor low request volume: captured-page cache hits
are resolved before Chrome starts, each query reuses one Chrome session, and
Google navigation starts are paced across workers. SerpScrap classifies access
controls and returns partial failures; it does not rotate identities or bypass
CAPTCHAs automatically. Reducing delays or increasing workers raises the chance
that Google rejects a run.
