===========
MCP server
===========

SerpScrap ships a small MCP-compatible JSON-RPC gateway. It delegates search
execution and persistence to the application API; it does not run a second
scraper. In the Compose deployment it listens on ``http://localhost:8001``.

Start the server
================

With Docker Compose:

.. code-block:: bash

   docker compose -f docker/compose.yml up --build serpscrap-db serpscrap-app serpscrap-mcp

The gateway uses ``SERPSCRAP_API_URL`` to locate the application API. For a
local process, start the API first and then run:

The Python gateway automatically loads a project-local ``.env`` file. Copy
``.env.example`` to ``.env`` for local development; real tokens must remain
uncommitted. Explicit process environment variables always take precedence.

.. code-block:: bash

   python -m serpscrap.mcp_server

   # Optional explicit PowerShell environment override:
   $env:MCP_HOST = "127.0.0.1"
   python -m serpscrap.mcp_server

The optional ``MCP_HOST`` and ``MCP_PORT`` variables change the bind address
and port. ``GET /healthz`` returns ``{"status": "ok"}``.

Security and trust boundary
===========================

The gateway treats SERP titles, snippets, URLs, and provider diagnostics as
untrusted data. It bounds MCP output and never interprets returned content as
instructions. ``MCP_MAX_OUTPUT_BYTES`` can lower the default 100,000-byte
response limit.

Loopback development may run without authentication. A non-loopback bind
requires ``MCP_AUTH_TOKEN``; clients must send ``Authorization: Bearer
<token>``. ``MCP_ALLOW_INSECURE_REMOTE=1`` is an explicit development escape
hatch and must not be used for a hosted deployment. Use HTTPS and a secret
injection mechanism outside the repository for remote access. Configuration
mutation tools are separate from read tools and must be approved by the MCP
client according to its permission model.

Configurations for popular model clients
========================================

MCP configuration belongs to the client or API integration, not to a model
name. The model is selected separately (for example, ``gpt-5`` or a Claude
Sonnet model). The examples below assume that the gateway is available at
``http://127.0.0.1:8001``. Replace this with a trusted HTTPS URL when the
model provider connects from the Internet. Non-loopback deployments require
``MCP_AUTH_TOKEN`` authentication.

Claude Code
-----------

Claude Code can register an HTTP MCP server from the command line:

.. code-block:: bash

   claude mcp add --transport http serpscrap http://127.0.0.1:8001

Verify the entry with ``claude mcp list``. This is a client configuration;
choose the Claude model independently when starting a session.

Cursor and other JSON-configured clients
-----------------------------------------

Clients that support an HTTP ``url`` entry can use this ``mcp.json`` shape:

.. code-block:: json

   {
     "mcpServers": {
       "serpscrap": {
         "url": "http://127.0.0.1:8001"
       }
     }
   }

The exact file location and supported transport names vary by client. If the
client only accepts ``stdio`` or Streamable HTTP, it cannot connect directly
to this minimal JSON-RPC gateway without a compatible adapter.

OpenAI Responses API
--------------------

The Responses API uses a remote MCP tool configuration. The server must be
reachable by OpenAI over HTTPS; ``localhost`` and ``127.0.0.1`` are not
reachable from the hosted API:

.. code-block:: python

   from openai import OpenAI

   client = OpenAI()
   response = client.responses.create(
       model="gpt-5",
       input="Search for recent renewable-energy news in Germany.",
       tools=[{
           "type": "mcp",
           "server_label": "serpscrap",
           "server_url": "https://mcp.example.test/",
           "allowed_tools": ["start_search", "get_search_status", "list_results"],
           "require_approval": "always",
       }],
   )

Use the current OpenAI remote-MCP transport requirements when deploying this
integration; a plain local HTTP JSON-RPC endpoint is intended for local
clients and may require an adapter.

Anthropic Messages API
----------------------

Anthropic's MCP connector likewise requires a remotely reachable server URL
and a compatible remote transport:

.. code-block:: json

   {
     "model": "claude-sonnet-4-20250514",
     "max_tokens": 1000,
     "messages": [{
       "role": "user",
     "content": "Which search tools are available?"
     }],
     "mcp_servers": [{
       "type": "url",
       "url": "https://mcp.example.test/sse",
       "name": "serpscrap"
     }]
   }

The local gateway documented here does not provide an SSE endpoint. For
Anthropic's hosted connector, deploy or place an MCP transport adapter in
front of SerpScrap before using this configuration.

See the provider documentation for [Claude MCP]_ and [OpenAI remote MCP]_ for
the latest client and API options.

.. [Claude MCP] https://docs.anthropic.com/en/docs/mcp
.. [OpenAI remote MCP] https://platform.openai.com/docs/guides/tools-remote-mcp

Protocol flow
=============

An MCP client sends JSON-RPC 2.0 POST requests:

.. code-block:: bash

   curl http://localhost:8001/ -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

   curl http://localhost:8001/ -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

Call a tool by sending ``tools/call`` with ``params.name`` and
``params.arguments``. The gateway returns tool output as MCP text content.

Available tools
===============

``tools/list`` exposes strict JSON schemas with bounded arguments and
read-only/mutation annotations. Tool calls return both MCP text content and a
``structuredContent`` envelope with ``schema_version`` ``1.0``. Search
content remains inert data and is bounded before it leaves the gateway.

``start_search``
   Start a job. Arguments include ``query`` or ``queries`` and optional
   ``options`` such as ``search_engines``, ``searxng_enabled``,
   ``searxng_engines``, ``country_code``, page count, and worker limits. The
   response contains the job ``id``.
``get_search_status``
   Read status and partial results for a job using its ``id``.
``list_results``
   Read normalized results, optionally filtered by ``run_id`` and bounded by
   ``offset``/``limit`` pagination.
``list_search_history``
   List persisted search runs.
``analyze_history``
   Return aggregate history analytics.
``analyze_url_statistics``
   Return domain or canonical-URL statistics across all persisted searches,
   independent of the search query. Use ``scope=domains`` or ``scope=urls``;
   optionally filter by ``domain`` and paginate with ``limit``/``offset``.
``list_engines``
   Return registry metadata, capabilities, readiness, and browser contracts.
``get_configuration``
   Read the effective persisted/default engine configuration.
``update_configuration``
   Persist a validated configuration. The payload must contain a non-empty
   ``search_engines`` list. Local SearXNG settings can additionally include
   ``searxng_enabled``, ``searxng_url``, ``searxng_fallback``, and
   ``searxng_engines``.
``reset_configuration``
   Restore the default configuration.
``list_topics``
   List registered thematic source adapters and their transport, pagination,
   locale, and readiness capabilities.
``topic_search``
   Run a bounded News or Shopping request through the shared TopicService.
   Arguments include ``topic``, ``query``, optional ``sources``, ``country``,
   ``language``, ``since``, and ``until``. The response is a versioned report
   with results, source status, and structured errors.
``get_topic_capabilities``
   Return the registered capabilities, supported locales, transport,
   pagination, readiness, and all source adapters for one topic.
``list_topic_sources``
   List the registered source adapters for a topic. Each source includes its
   source ID, capabilities, and readiness metadata.
``search_news``
   Run a News-only request with optional source, country, language, and time
   window filters.
``group_news_events``
   Run a News request and group near-identical normalized headlines into
   source-aware events. The grouping is bounded and deterministic; it is not
   a claim that articles describe the same real-world event.
``search_products``
   Run a Shopping-only request with optional source and marketplace filters.
``compare_product_prices``
   Run a Shopping request and group comparable offers by product identifier or
   normalized title. Offers include a parsed ``price_value`` where the source
   exposed a recognizable price; source-provided displayed price fields remain
   preserved.
``validate_topic_query``
   Validate a topic request without fetching sources.
``compare_topic_results``
   Compare two bounded result lists by URL identity.
``export_topic_results``
   Export a bounded result list as JSON or CSV text.
``compare_news_sources``
   Compare News result counts and headlines by source.
``track_news_topic`` / ``track_product_price``
   Return a source-aware tracking snapshot. Persistent scheduling is outside
   the MCP gateway and can consume these snapshots.
``get_news_trends``
   Summarize News result volume by publication day.
``filter_products``
   Filter Shopping offers by maximum price and availability.
``find_product_alternatives``
   Return products with more than one comparable offer.

The specialized News and Shopping tools use the same ``TopicService`` as
``topic_search``. Source failures remain in ``source_status`` and ``errors``;
the tools do not bypass consent, robots, authentication, rate limits, or
provider blocks.

Example search call
===================

.. code-block:: bash

   curl http://localhost:8001/ -H "Content-Type: application/json" -d @- <<'JSON'
   {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"start_search","arguments":{"query":"renewable energy","options":{"search_engines":["google","bing"],"country_code":"DE","num_pages_for_keyword":1}}}}
   JSON

Use the returned ID with ``get_search_status`` and then ``list_results``. MCP
clients should poll with a bounded interval, use the returned terminal state,
and stop after a bounded number of attempts. Read tools are idempotent;
configuration tools change persisted shared state and require explicit
approval. Only connect trusted, authenticated clients to a non-loopback
gateway.
