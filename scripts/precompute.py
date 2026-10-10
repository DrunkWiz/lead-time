"""Write the snapshot-only results (backtest, weekly feeds) to data/cache/derived/ so a
small free-tier server never computes them on a request. The Dockerfile runs this at build
time; the output is not committed, so it always matches the code being deployed.

    py -3 scripts/precompute.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from leadtime import app, feed  # noqa: E402

PRESET_OUTCOMES = {"inside", "early", "late"}   # same rule the app uses for its "Pretend it's" chips


def main():
    _, bt = app.route("GET", "/api/backtest")
    presets = [r["flagged_on"] for r in bt["rows"] if r.get("window") and r["outcome"] in PRESET_OUTCOMES]
    for as_of in [None] + presets:
        app.route("GET", "/api/changes", query={"weeks": str(feed.FEED_WEEKS), **({"as_of": as_of} if as_of else {})})
    app.DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    for key, value in app._derived.items():
        path = app._derived_path(key)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
