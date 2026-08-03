# SerpScrap Docker layout

The Docker-specific files are grouped in this directory:

- `compose.yml` defines the four-container deployment.
- `Dockerfile` builds the single browser-enabled SerpScrap runtime image.

Compose reuses that image for the application, UI, and MCP services. The UI
service starts `python -m ui.app`, while runtime commands, ports, health
checks, and mounts remain service-specific.

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

To use a prebuilt or pinned image, set `SERPSCRAP_IMAGE` and skip the build:

```powershell
$env:SERPSCRAP_IMAGE = "serpscrap:2.0.0-alpha.1"
docker compose -f docker/compose.yml up -d
```

The UI is available at `http://localhost:8080`, the API at
`http://localhost:8000`, and the MCP gateway at `http://localhost:8001`.
