# SerpScrap Docker layout

The Docker-specific files are grouped in this directory:

- `compose.yml` defines the application, database, UI, MCP, SearXNG, and
  Valkey services.
- `Dockerfile` builds the single browser-enabled SerpScrap runtime image.

Compose reuses that image for the application, UI, and MCP services. The UI
service starts `python -m ui.app`, while runtime commands, ports, health
checks, and mounts remain service-specific.

Set a secret token before starting the stack because the MCP gateway is
published on port 8001:

```powershell
$env:POSTGRES_PASSWORD = "replace-with-a-database-secret"
$env:SEARXNG_SECRET = "replace-with-a-long-random-secret"
$env:MCP_AUTH_TOKEN = "replace-with-a-secret"
```

Never commit the token or expose the gateway without HTTPS and an authenticated
trusted client.

Start the complete stack from the repository root:

```bash
mkdir -p data/postgres data/cache data/diagnostics data/exports logs
docker compose -f docker/compose.yml up --build
```

To use a prebuilt or pinned image, set `SERPSCRAP_IMAGE` and skip the build:

```powershell
$env:SERPSCRAP_IMAGE = "serpscrap:2.0.0-alpha.2"
docker compose -f docker/compose.yml up -d
```

The UI is available at `http://localhost:8080`, the API at
`http://localhost:8000`, and the MCP gateway at `http://localhost:8001`.

## SearXNG integration

SearXNG and Valkey start with the normal Compose stack. ``SEARXNG_SECRET`` is
required before startup. SerpScrap points at the internal SearXNG service by
default:

The bundled configuration disables optional `ahmia`, `torch`, and `wikidata`
engines because they can fail during startup independently of the core search
service. The limiter configuration is included locally and uses the Compose
network as an explicitly local client range without trusting forwarded headers
globally.

```powershell
docker compose -f docker/compose.yml up -d --build
```

SearXNG is enabled by default in the standard Compose deployment. The
configuration page at `http://localhost:8080/configuration` provides one
grouped overview for direct SerpScrap engines and the engines queried through
SearXNG. The global `searxng_enabled` setting can disable SearXNG for new
searches. `searxng_fallback: true` adds it alongside the selected engines when
it is enabled; otherwise select `searxng` in `search_engines`.

Use `searxng_engines` to choose the engines inside the SearXNG instance, for
example `['duckduckgo', 'brave']`. The default selects all currently mapped
no-key sources, grouped as web, scientific, developer/Q&A, and news engines.
This includes sources such as `wiby`, `pubmed`, and `askubuntu`. Results expose
their originating source as `SearXNG:<engine>` when SearXNG provides that
metadata; this source is also used by relevance fusion.
