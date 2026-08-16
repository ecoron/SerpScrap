=====================
Topic tools
=====================

Topic tools provide a common interface for thematic sources such as news
feeds and shopping pages. They use the same request, result, source-status,
error, and metadata shape even when a source uses a feed or browser transport.
Shopping result pages are opened through the same configured Selenium/Chrome
transport as search engines. This includes headless mode, desktop user agent,
language, page-load and wait timeouts, pacing, retry and backoff limits, and
block/consent handling. Direct HTTP is not used for these pages. Provider
challenges are reported as structured source failures and are not bypassed.

The built-in topics are ``news`` and ``shopping``. The implementation is
available through the Python API, the CLI, the HTTP API, and MCP. Topic tools
are opt-in; the existing ``search`` command and ``SearchEnginePlugin`` API
remain compatible.

Shared contract
===============

``TopicRequest`` contains the query, topic, optional sources, country,
language, time window, and topic-specific filters. ``TopicResult`` preserves
both ``raw_url`` and ``canonical_url`` and may carry topic fields such as
``published_at``, ``author``, ``price``, ``currency``, ``merchant``, and
``availability``. ``TopicReport`` contains normalized results, per-source
status, structured errors, duration, and ``schema_version``.

URLs are normalized by removing tracking parameters such as ``utm_*``,
``gclid``, and ``fbclid``. Results are deduplicated after normalization and
receive deterministic report-local ranks.

News
====

The News MVP prefers RSS and Atom feeds. It extracts title, description,
source, publication time, author, language, and original URL. ``since`` and
``until`` accept ISO timestamps; relative windows such as ``24h``, ``7d``,
and ``2w`` are also supported.

Python example:

.. code-block:: python

   from serpscrap import TopicRequest, TopicService

   request = TopicRequest.create(
       "artificial intelligence",
       topic="news",
       language="en",
       since="24h",
       sources=("https://example.test/feed.xml",),
   )
   report = TopicService().execute(request)
   print(report.to_dict())

The default News source selection includes the generic Google News RSS
adapter and the following European publishers/agencies:

* ``ansa`` — ANSA English RSS
* ``dw`` — Deutsche Welle German RSS
* ``euronews`` — Euronews world-news MRSS
* ``france24`` — France 24 English RSS
* ``lemonde`` — Le Monde Europe RSS (English)
* ``guardian`` — The Guardian Europe RSS

These feeds expose headlines, short descriptions, publication times and
original article URLs. Feed terms differ by provider: ANSA and Le Monde state
that RSS use is intended for personal/non-commercial aggregation, while the
Guardian likewise documents personal, non-commercial RSS use. Deployments
should review each provider's current terms before using the sources beyond
local search and display.

Shopping
========

The Shopping MVP parses product links from HTML and extracts a bounded card
excerpt, including provider ``meta`` descriptions where available. It also
normalizes price, currency, and basic availability metadata. Product identity should prefer a
GTIN or manufacturer/model identifier supplied by a future source adapter;
the generic fallback uses the canonical product URL. Locale-specific source
adapters should add a normalized numeric price and preserve the displayed
value in the result metadata.

The first open search-page sources are:

* ``geizhals`` — ``https://geizhals.de/?fs={query}``
* ``idealo`` — ``https://www.idealo.de/preisvergleich/MainSearchProductCategory.html?q={query}``
* ``billiger`` — ``https://www.billiger.de/search?searchTerm={query}``
* ``fruugo`` — localized ``https://www.fruugo.{market}/search`` pages
* ``kaufland`` — localized Kaufland marketplace search pages
* ``allegro`` — ``https://allegro.{market}/listing?string={query}``
* ``etsy`` — ``https://www.etsy.com/search?q={query}``

These adapters use public result pages and do not require API credentials.
They remain subject to each site's robots rules, terms, rate limits, consent
flows, and access controls. A source-specific parser is used for each page
family; a failed source is reported separately while successful sources still
contribute results.

CLI
===

Use ``topic-search`` for a direct report on stdout:

.. code-block:: console

   serpscrap topic-search news "artificial intelligence" --language en --since 24h
   serpscrap topic-search shopping "noise cancelling headphones" --country DE

The command is deterministic when a source payload is supplied through a
test or custom service; production source access remains subject to provider
terms, rate limits, robots rules, consent, and access controls.

HTTP API
========

List registered topics:

.. code-block:: console

   curl http://localhost:8000/api/v1/topics

Run a topic search:

.. code-block:: console

   curl http://localhost:8000/api/v1/topics/search \
     -H "Content-Type: application/json" \
     -d '{"topic":"news","query":"renewable energy","language":"en","since":"24h"}'

The endpoint returns the same ``TopicReport`` fields as the Python service and
adds a ``run_id``. It is synchronous and intended for bounded topic requests.
The HTTP endpoint also creates a normal search-history run; results
are available through the existing history and result endpoints. The direct
Python API, CLI, and MCP service return reports without implicitly persisting
them, so callers that need history should use the HTTP API or persist the
report explicitly.

MCP
===

``list_topics`` returns topic capabilities. ``topic_search`` accepts
``topic``, ``query``, optional ``sources``, ``country``, ``language``,
``since``, and ``until`` and returns a bounded structured report. Both tools
use the same TopicService as the HTTP and Python interfaces.

Adding a source
===============

Implement ``TopicPlugin`` with a stable ``topic_id``, capabilities,
``build_url``, ``parse``, and optional ``normalize``/``classify`` methods.
Register it in a ``TopicPluginRegistry``, add sanitized fixtures, parser and
failure-state tests, and document source terms and rate-limit behavior. Do
not bypass CAPTCHA, consent, robots rules, authentication, or provider rate
limits. Raw responses containing queries, cookies, or session data must stay
out of the repository and CI artifacts.
