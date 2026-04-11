#!/usr/bin/env python3
"""Minimal echo HTTP server for system lab tests.

/ip      → plain-text client IP (matches ifconfig.me format)
/health  → "ok"
/*       → JSON with client_ip, path, headers
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._text(200, b"ok")
        elif self.path == "/ip":
            self._text(200, self.client_address[0].encode())
        else:
            body = json.dumps(
                {
                    "client_ip": self.client_address[0],
                    "path": self.path,
                    "headers": {k: v for k, v in self.headers.items()},
                }
            ).encode()
            self._respond(200, body, "application/json")

    def _text(self, code: int, body: bytes):
        self._respond(code, body, "text/plain")

    def _respond(self, code: int, body: bytes, content_type: str):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args):
        return


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
