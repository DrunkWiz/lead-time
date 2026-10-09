"""Fetch weekly Google Trends interest for every concept in every region.

One request per (concept, region) with all of the concept's aliases (max 5),
so the aliases share one 0-100 scale and can be summed. Every response is
cached to data/raw/trends/{concept_id}_{geo}.json; re-running skips cached
files, so an interrupted run resumes where it stopped.

    py -3 scripts/fetch_trends.py            # fetch everything missing
    py -3 scripts/fetch_trends.py --only tanghulu --force
"""
import argparse
import datetime as dt
import json
import random
import sys
import time
from pathlib import Path

from pytrends.request import TrendReq

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from leadtime.concepts import load_concepts, query_terms  # noqa: E402

RAW = ROOT / "data" / "raw" / "trends"
REGIONS = ["SG", "KR", "JP", "TW", "AE", "US", "MY"]
TIMEFRAME = "today 5-y"     # longest window Google still returns weekly
SLEEP_SECONDS = 6           # polite gap between calls; pytrends 429s fast
JITTER_SECONDS = 4          # randomise the gap so calls don't look scripted
BACKOFF_SECONDS = [60, 120, 300, 600]   # waits after successive 429s


def fetch_one(client, terms, geo):
    for attempt, wait in enumerate([0] + BACKOFF_SECONDS):
        if wait:
            print(f"    rate limited, sleeping {wait}s (attempt {attempt + 1})", flush=True)
            time.sleep(wait)
        try:
            client.build_payload(terms, timeframe=TIMEFRAME, geo=geo)
            return client.interest_over_time()
        except Exception as exc:  # pytrends raises TooManyRequestsError, ResponseError, ...
            if "429" not in str(exc) and "TooManyRequests" not in type(exc).__name__:
                raise
    raise RuntimeError(f"gave up on {terms} in {geo} after repeated 429s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="concept id to fetch")
    ap.add_argument("--force", action="store_true", help="refetch even if cached")
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    client = TrendReq(hl="en-US", tz=-480, timeout=(10, 30))
    concepts = load_concepts()
    todo = []
    for c in concepts:
        if args.only and c["id"] != args.only:
            continue
        for geo in REGIONS:
            path = RAW / f"{c['id']}_{geo}.json"
            if path.exists() and not args.force:
                continue
            todo.append((c, geo, path))

    print(f"{len(todo)} requests to make", flush=True)
    for i, (c, geo, path) in enumerate(todo, 1):
        terms = query_terms(c)
        print(f"[{i}/{len(todo)}] {c['id']} {geo} {terms}", flush=True)
        df = fetch_one(client, terms, geo)
        record = {
            "concept_id": c["id"],
            "geo": geo,
            "terms": terms,
            "timeframe": TIMEFRAME,
            "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "dates": [],
            "values": {t: [] for t in terms},
            "is_partial": [],
        }
        if df is not None and not df.empty:
            record["dates"] = [d.strftime("%Y-%m-%d") for d in df.index]
            for t in terms:
                record["values"][t] = [int(v) for v in df[t].tolist()] if t in df else []
            if "isPartial" in df:
                record["is_partial"] = [bool(v) for v in df["isPartial"].tolist()]
        path.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(SLEEP_SECONDS + random.random() * JITTER_SECONDS)
    print("done", flush=True)


if __name__ == "__main__":
    main()
