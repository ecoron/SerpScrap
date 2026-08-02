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

.. code-block:: bash

   $env:SERPSCRAP_API_URL = "http://127.0.0.1:8000/api/v1"  # PowerShell
   python -m serpscrap.mcp_server

   SERPSCRAP_API_URL=http://127.0.0.1:8000/api/v1 python -m serpscrap.mcp_server  # POSIX

The optional ``MCP_HOST`` and ``MCP_PORT`` variables change the bind address
and port. ``GET /healthz`` returns ``{"status": "ok"}``.

Configurations for popular model clients
========================================

MCP configuration belongs to the client or API integration, not to a model
name. The model is selected separately (for example, ``gpt-5`` or a Claude
Sonnet model). The examples below assume that the gateway is available at
``http://127.0.0.1:8001``. Replace this with a trusted HTTPS URL when the
model provider connects from the Internet. The gateway currently has no
authentication layer; do not expose an unprotected local instance publicly.

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
       "content": "Welche Suchwerkzeuge stehen zur Verfügung?"
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

``start_search``
   Start a job. Arguments include ``query`` or ``queries`` and optional
   ``options`` such as ``search_engines``, ``country_code``, page count, and
   worker limits. The response contains the job ``id``.
``get_search_status``
   Read status and partial results for a job using its ``id``.
``list_results``
   Read normalized results, optionally filtered by ``run_id``.
``list_search_history``
   List persisted search runs.
``analyze_history``
   Return aggregate history analytics.
``list_engines``
   Return registry metadata, capabilities, readiness, and browser contracts.
``get_configuration``
   Read the effective persisted/default engine configuration.
``update_configuration``
   Persist a validated configuration. The payload must contain a non-empty
   ``search_engines`` list.
``reset_configuration``
   Restore the default configuration.

Example search call
===================

.. code-block:: bash

   curl http://localhost:8001/ -H "Content-Type: application/json" -d @- <<'JSON'
   {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"start_search","arguments":{"query":"renewable energy","options":{"search_engines":["google","bing"],"country_code":"DE","num_pages_for_keyword":1}}}}
   JSON

Use the returned ID with ``get_search_status`` and then ``list_results``. MCP
clients should poll with a bounded interval and stop on the terminal status.
Only connect trusted clients to the gateway: the current gateway has no
authentication layer and configuration tools change persisted state.
