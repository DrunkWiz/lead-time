"""Precompute fit + launch plans for the demo profiles with the real model,
across the snapshot date and any backtest dates, so the demo never waits on a model.

    py -3 scripts/warm_cache.py 2024-05-01 2023-06-01     (reads keys from .env)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.dev_server import load_env  # noqa: E402

load_env()
from leadtime.app import route  # noqa: E402

PROFILES = json.loads((ROOT / "web" / "src" / "demoProfiles.json").read_text(encoding="utf-8"))


def main():
    dates = [None] + sys.argv[1:]
    for p in PROFILES:
        for d in dates:
            status, rec = route("POST", "/api/recommend", body={"profile": p["profile"], "as_of": d})
            if status != 200:
                print(p["id"], d, rec)
                continue
            # every concept, not just the cards: Explore opens any of them
            _, listing = route("GET", "/api/concepts", query={"as_of": d} if d else {})
            for c in listing["concepts"]:
                _, lp = route("POST", "/api/launch",
                              body={"profile": p["profile"], "as_of": d, "concept_id": c["id"]})
                print(f"{p['id']:<14} {d or 'snapshot':<11} {c['id']:<26} "
                      f"fit={lp.get('fit_provider')} plan={lp.get('plan_provider')}", flush=True)


if __name__ == "__main__":
    main()
