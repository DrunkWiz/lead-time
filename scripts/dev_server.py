"""Local API server on :8787 using the same router as Vercel. Vite proxies /api here.

    py -3 scripts/dev_server.py
"""
import os
import sys
from http.server import ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def load_env():
    """Read .env into the environment (stdlib only, no python-dotenv)."""
    path = os.path.join(ROOT, ".env")
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


load_env()
from api.index import handler  # noqa: E402

PORT = int(os.environ.get("PORT", 8787))

if __name__ == "__main__":
    print(f"Lead Time API on http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), handler).serve_forever()
