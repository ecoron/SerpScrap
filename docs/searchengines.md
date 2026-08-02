# Search engines

SerpScrap uses a registry of provider plugins. The registry exposes stable
engine IDs, capabilities, readiness, transport, provider family, and the
browser interaction contract through the API, CLI configuration, and MCP
``list_engines`` tool.

## Active defaults

The default configuration enables the following browser providers:

| ID | Display name | Notes |
| --- | --- | --- |
| `bing` | Bing | General web search |
| `yandex` | Yandex | General web search |
| `yahoo` | Yahoo | General web search |
| `duckduckgo` | DuckDuckGo | HTML web search |
| `startpage` | Startpage | Privacy-oriented web search |
| `brave` | Brave | General web search; challenges remain typed |
| `swisscows` | Swisscows | General web search |
| `mojeek` | Mojeek | Independent web search |
| `good` | GOOD Search | Public European web search |
| `xprivo` | xPrivo | Public European web search |
| `marginalia` | Marginalia | Public independent web search |
| `etools` | eTools.ch | Public metasearch web search |

Google, Ecosia, and Qwant remain registered and can be selected explicitly
when their current provider contract is appropriate. MetaGer is registered but
disabled until a public no-auth route is available. Experimental SearXNG use is
instance-scoped and requires an explicitly trusted base URL.

List current metadata instead of relying on this table when building an
integration:

.. code-block:: bash

   curl http://localhost:8000/api/v1/engines

## Selecting engines

Python and CLI selections use the same IDs:

.. code-block:: python

   from serpscrap import Config, SerpScrap

   config = Config()
   config.apply({"search_engines": ["bing", "xprivo"], "country_code": "DE"})
   results = SerpScrap().search("european search", config=config)

.. code-block:: bash

   serpscrap search -k "european search" --engine bing --engine xprivo

An explicitly selected disabled or unknown engine is rejected before browser
navigation. One provider's block, consent, rate limit, timeout, or selector
failure remains separate from successful results from other providers.

## Provider safety

Provider pages are dynamic and can change without notice. SerpScrap uses
visible browser controls and bounded waits. It does not bypass CAPTCHAs, rate
limits, access controls, or consent decisions. Live checks are opt-in and must
remain low-volume. Sanitized offline fixtures are the source of truth for
deterministic parser and contract tests.

## Adding a provider

Developers should:

1. Implement the shared plugin contract and immutable provider metadata.
2. Add URL, pagination, browser, parser, and classification behavior in the
   provider module or registry entry.
3. Add sanitized fixtures for normal, empty, malformed, blocked, consent, and
   rate-limited states where relevant.
4. Add contract tests for identity, capabilities, URL encoding, parsing,
   readiness, metadata serialization, and partial failures.
5. Run the full offline suite, Ruff, package build, and Sphinx warning-as-error
   build before enabling the provider by default.
