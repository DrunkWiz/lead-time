"""Production server: the built app (web/dist) and the API on one port. Used on Render.

    npm --prefix web run build
    PORT=8000 py -3 scripts/serve.py

Binds 0.0.0.0:$PORT because Render routes traffic to whatever port it puts in $PORT.
Keys come from the environment (Render dashboard); a local .env is read if present.
"""
import mimetypes
import os
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.dev_server import load_env  # noqa: E402

load_env()
from api.index import handler as ApiHandler  # noqa: E402

DIST = (ROOT / "web" / "dist").resolve()
DEFAULT_PORT = 8000            # Render overrides this with $PORT
ASSET_MAX_AGE = 31536000       # Vite fingerprints files in assets/, so they never change in place
mimetypes.add_type("text/javascript", ".js")  # some systems map .js to text/plain, which blocks module scripts
mimetypes.add_type("image/svg+xml", ".svg")


class handler(ApiHandler):
    def _static(self, head_only=False):
        rel = self.path.split("?", 1)[0].split("#", 1)[0].lstrip("/")
        target = (DIST / rel).resolve() if rel else DIST / "index.html"
        # Anything outside dist, or missing, gets index.html (the app uses hash routes).
        if DIST not in target.parents or not target.is_file():
            target = DIST / "index.html"
        if not target.is_file():
            return self._send(503, {"error": "The app isn't built yet. Run: npm --prefix web run build"})
        raw = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(raw)))
        immutable = target.parent.name == "assets"
        self.send_header("Cache-Control", f"public, max-age={ASSET_MAX_AGE}, immutable" if immutable else "no-cache")
        self.end_headers()
        if not head_only:
            self.wfile.write(raw)

    def do_GET(self):
        if self.path.startswith("/api/"):
            return super().do_GET()
        self._static()

    def do_HEAD(self):
        self._static(head_only=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    print(f"Lead Time on http://0.0.0.0:{port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), handler).serve_forever()
