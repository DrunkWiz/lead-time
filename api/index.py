"""Vercel entry point. vercel.json rewrites every /api/* request here."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from leadtime.app import parse_body, route  # noqa: E402

MAX_BODY_BYTES = 64 * 1024  # profiles are tiny; refuse anything bigger


class handler(BaseHTTPRequestHandler):
    def _send(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _handle(self, method):
        url = urlparse(self.path)
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        path = query.pop("path", None)
        path = f"/api/{path}" if path else url.path
        body = {}
        if method == "POST":
            n = min(int(self.headers.get("Content-Length") or 0), MAX_BODY_BYTES)
            body = parse_body(self.rfile.read(n).decode("utf-8") if n else "")
        self._send(*route(method, path, query, body))

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")
