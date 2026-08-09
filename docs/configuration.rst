=============
Configuration
=============

``Config`` provides a dictionary-compatible configuration object. New code can
also pass friendly options directly to ``SerpScrap.search``. Settings are
copied and validated once for every independent request.

Core settings
-------------

* ``search_engines``: ordered list of registered engines, for example
  ``['google', 'bing', 'duckduckgo']``.
  In the Docker deployment, ``searxng`` is included by default when the local
  SearXNG service is configured. The web UI presents direct SerpScrap engines
  and SearXNG's internal engine selection in one grouped overview.
* ``searxng_enabled``: enable or disable the configured self-hosted SearXNG
  service. It defaults to enabled when ``SERPSCRAP_SEARXNG_URL`` is present.
* ``searxng_url``: base URL of the SearXNG JSON service. Compose defaults to
  ``http://searxng:8080``; the host-side SearXNG UI is available at
  ``http://localhost:8888``.
* ``searxng_fallback``: add SearXNG alongside the selected providers when it
  is enabled, even when ``searxng`` is not in ``search_engines``.
* ``searxng_engines``: ordered list of no-key engines requested inside
  SearXNG. The default groups cover web, scientific, developer/Q&A, and news
  sources, including ``wiby``, ``pubmed``, and ``askubuntu``.
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
* ``chrome_profile_dir``: optional isolated Chrome profile directory for
  controlled, disposable smoke tests. Do not use a personal Chrome profile;
  profile data is not suitable for CI artifacts or source control.
* ``interaction_settle_delay``: bounded wait after query entry and before
  submit, allowing provider autocomplete/form validation to settle. It does
  not hide WebDriver signals and defaults to ``0.35`` seconds.
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
* ``progress``: emit correlated per-engine progress events; the CLI enables it
  by default, while library callers can keep it disabled.
* ``progress_format``: ``text`` for human-readable stderr output or ``jsonl``
  for one machine-readable event per line on stderr.
* ``diagnostic_html``: explicitly enable redacted rendered-HTML artifacts for
  selector/provider troubleshooting; defaults to ``False``.
* ``diagnostic_dir``: artifact root, normally ``logs/diagnostics``.
* ``diagnostic_max_bytes_per_file``, ``diagnostic_max_total_bytes``, and
  ``diagnostic_max_artifacts_per_job``: safety limits for diagnostic output.
* ``consent_action``: provider consent handling. Defaults to ``necessary``
  and selects the privacy-preserving rejection action (Google's ``Alle
  ablehnen``); ``reject`` is an explicit alias and ``disabled`` preserves a
  ``consent_required`` failure. ``accept`` is an explicit diagnostic mode
  that selects the provider's full-consent action and should not be used as a
  production default.
  If the provider does not expose an actionable control, the run safely remains
  ``consent_required`` instead of bypassing or guessing at consent.
  Consent progress events use ``consent_not_present``, ``consent_visible``,
  ``consent_action_started``, and ``consent_cleared``; a failed verification
  never continues into search input handling.
* ``retryable_engine_categories``: bounded retry categories for engine jobs;
  the default is ``['timeout', 'navigation_state', 'network']``. Provider
  controls and parser/selector failures are not retried by default.
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

SearXNG selection
------------------

The bundled Docker stack starts SearXNG and Valkey with the normal Compose
stack. SearXNG is a transport to the local instance; the selected
``searxng_engines`` determine which upstream sources SearXNG queries. Results
retain their originating source as ``SearXNG:<engine>`` where available, so
result fusion can weight the underlying provider instead of treating every
result as one generic SearXNG source.

The configuration page at ``http://localhost:8080/configuration`` combines
direct SerpScrap providers and SearXNG sources in one overview. Disable the
global ``Enable SearXNG`` setting to remove SearXNG from new searches. The
bundled profile disables upstream engines that are known to fail during local
startup; one upstream CAPTCHA or rate limit produces partial results rather
than discarding successful SearXNG sources.

Diagnostic mode is opt-in because rendered pages can contain third-party
content. The artifact manifest contains correlation IDs, states, result counts,
and host/path information without query parameters. Raw artifacts are ignored
by Git and should be reviewed and deleted after troubleshooting:

.. code-block:: python

   config.apply({
       'progress': True,
       'progress_format': 'jsonl',
       'diagnostic_html': True,
       'diagnostic_dir': 'logs/diagnostics',
       'diagnostic_max_bytes_per_file': 2 * 1024 * 1024,
       'diagnostic_max_total_bytes': 20 * 1024 * 1024,
       'diagnostic_max_artifacts_per_job': 10,
       'consent_action': 'necessary',
       'retryable_engine_categories': ['timeout', 'navigation_state', 'network'],
   })

   scraper = SerpScrap()
   results = scraper.search('selector troubleshooting', config=config)

The equivalent CLI invocation is:

.. code-block:: bash

   serpscrap search -k "privacy-friendly search" \
     --engine google --engine bing --engine duckduckgo --engine ecosia \
     --country DE --workers 4

Show progress and capture rendered pages for a focused provider run:

.. code-block:: bash

   serpscrap search -k "preisfehler" \
     --engine bing --engine yandex --engine brave --engine ecosia \
     --country DE --workers 4 --progress --diagnostic-html \
     --diagnostic-dir logs/diagnostics

For machine processing, keep result JSON on stdout and progress JSONL on
stderr:

.. code-block:: bash

   serpscrap search -k "herrenschuhe" --progress-format jsonl \
     > results.json 2> progress.jsonl

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
