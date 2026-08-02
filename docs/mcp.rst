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
