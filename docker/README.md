# SerpScrap Docker layout

The Docker-specific files are grouped in this directory:

- `compose.yml` defines the four-container deployment.
- `app/Dockerfile` builds the browser-enabled SerpScrap application image.
- `mcp/Dockerfile` builds the lightweight MCP gateway image.
- `ui/Dockerfile` builds the static UI image.

All images use the repository root as their build context so that the Python
package, lock files, and UI assets remain available without duplicating source
files.

Set a secret token before starting the stack because the MCP gateway is
published on port 8001:

```powershell
$env:MCP_AUTH_TOKEN = "replace-with-a-secret"
```

Never commit the token or expose the gateway without HTTPS and an authenticated
trusted client.

Start the complete stack from the repository root:

```bash
mkdir -p data/postgres data/cache data/diagnostics data/exports logs
docker compose -f docker/compose.yml up --build
```

The UI is available at `http://localhost:8080`, the API at
`http://localhost:8000`, and the MCP gateway at `http://localhost:8001`.
