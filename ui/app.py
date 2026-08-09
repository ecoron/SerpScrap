"""Flask delivery layer for the SerpScrap dynamic UI."""

from __future__ import annotations

import os
import urllib.error
import urllib.request

from flask import Flask, Response, jsonify, render_template, request, send_from_directory


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SERPSCRAP_API_URL"] = os.getenv(
        "SERPSCRAP_API_URL", "http://localhost:8000/api/v1"
    ).rstrip("/")

    def render_page(page: str, template: str) -> str:
        return render_template(
            f"pages/{template}.html",
            active_page=page,
            api_base="/api",
            application_version=os.getenv("SERPSCRAP_UI_VERSION", "2.0.0-alpha.2"),
        )

    @app.get("/")
    def index() -> str:
        return render_page("overview", "overview")

    @app.get("/search")
    def search_page() -> str:
        return render_page("search", "search")

    @app.get("/history")
    def history_page() -> str:
        return render_page("history", "history")

    @app.get("/configuration")
    def configuration_page() -> str:
        return render_page("configuration", "configuration")

    @app.get("/healthz")
    def healthz() -> tuple[Response, int]:
        return jsonify(status="ok", service="serpscrap-ui"), 200

    @app.get("/static/<path:filename>")
    def static_assets(filename: str) -> Response:
        return send_from_directory(app.static_folder or "static", filename)

    @app.route("/api", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    @app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    def api_proxy(path: str) -> Response:
        """Proxy browser requests to the internal application API.

        Keeping the browser on the UI origin avoids CORS configuration and
        keeps the Docker service name out of client-side JavaScript.
        """

        if request.method == "OPTIONS":
            return Response(status=204)
        api_path = path[3:] if path == "v1" or path.startswith("v1/") else path
        target = f"{app.config['SERPSCRAP_API_URL']}/{api_path}".rstrip("/")
        if request.query_string:
            target = f"{target}?{request.query_string.decode('ascii')}"
        body = request.get_data() or None
        headers = {"Accept": "application/json"}
        if body:
            headers["Content-Type"] = request.content_type or "application/json"
        upstream = urllib.request.Request(target, data=body, headers=headers, method=request.method)
        try:
            with urllib.request.urlopen(upstream, timeout=30) as result:
                payload = result.read()
                response_headers = {"Content-Type": result.headers.get("Content-Type", "application/json")}
                return Response(payload, status=result.status, headers=response_headers)
        except urllib.error.HTTPError as error:
            payload = error.read()
            return Response(payload, status=error.code, content_type="application/json")
        except (urllib.error.URLError, TimeoutError) as error:
            return jsonify(error="application API unavailable", detail=str(error.reason if isinstance(error, urllib.error.URLError) else error)), 503

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.getenv("UI_HOST", "0.0.0.0"),
        port=int(os.getenv("UI_PORT", "8080")),
        debug=False,
    )
