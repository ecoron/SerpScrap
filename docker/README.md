# SerpScrap Docker layout

The Docker-specific files are grouped in this directory:

- `compose.yml` defines the four-container deployment.
- `app/Dockerfile` builds the browser-enabled SerpScrap application image.
- `mcp/Dockerfile` builds the lightweight MCP gateway image.
- `ui/Dockerfile` builds the static UI image.

All images use the repository root as their build context so that the Python
package, lock files, and UI assets remain available without duplicating source
files.

Start the complete stack from the repository root:

```bash
mkdir -p data/postgres data/cache data/diagnostics data/exports logs
docker compose -f docker/compose.yml up --build
```

The UI is available at `http://localhost:8080`, the API at
`http://localhost:8000`, and the MCP gateway at `http://localhost:8001`.
