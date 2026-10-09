"""Build data/series.json and data/meta.json from data/raw/trends/*.json.

    py -3 scripts/build_series.py
"""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from leadtime import series  # noqa: E402
from leadtime.concepts import load_concepts, query_terms  # noqa: E402

RAW = ROOT / "data" / "raw" / "trends"


def main():
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RAW.glob("*.json"))]
    known = {c["id"] for c in load_concepts()}
    records = [r for r in records if r["concept_id"] in known]
    if not records:
        sys.exit("No raw trends files. Run scripts/fetch_trends.py first.")
    snap = series.build(records, {c["id"]: query_terms(c) for c in load_concepts()})
    (ROOT / "data" / "series.json").write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")

    fetched = max(r["fetched_at"] for r in records)
    meta = {
        "fetched_at": fetched,
        "built_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sources": ["Google Trends (weekly, via pytrends)"],
        "regions": sorted({r["geo"] for r in records}, key=lambda g: (g != "SG", g)),
        "timeframe": records[0]["timeframe"],
        "terms": {c["id"]: query_terms(c) for c in load_concepts()},
        "raw_files": len(records),
    }
    (ROOT / "data" / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"series.json: {len(snap['series'])} concepts x {len(snap['weeks'])} weeks "
          f"({snap['weeks'][0]} to {snap['weeks'][-1]}) from {len(records)} raw files")


if __name__ == "__main__":
    main()
