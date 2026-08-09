from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from scrapcore.proxy import ProxyPool


class LocalProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"local proxy ok")

    def log_message(self, format, *args):
        return


def test_local_proxy_source_and_health_check_end_to_end(tmp_path: Path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), LocalProxyHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    source = tmp_path / "proxies.txt"
    source.write_text(f"http 127.0.0.1:{server.server_port}\n", encoding="utf-8")
    config = {
        "proxy_sources": [{"type": "file", "location": str(source)}],
        "check_proxies": True,
        "proxy_check_url": "http://proxy-fixture.invalid/status",
        "proxy_check_timeout": 2,
    }
    try:
        pool = ProxyPool.from_config(config)
        endpoint = pool.endpoints[0]
        health = pool.health[endpoint.key]

        assert health.online is True
        assert health.latency_ms is not None
        assert pool.select("google") == endpoint
    finally:
        server.shutdown()
        server.server_close()
