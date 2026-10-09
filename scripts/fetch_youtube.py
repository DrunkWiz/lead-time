"""Fetch recipe / how-to videos per concept from the YouTube Data API v3.

search.list costs 100 units, videos.list 1 unit; the daily quota is 10,000,
so one search per concept (16 concepts ~ 1,700 units) fits comfortably.
Raw responses go to data/raw/youtube/, the trimmed result to data/youtube.json.

    YOUTUBE_API_KEY=... py -3 scripts/fetch_youtube.py
"""
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from leadtime.concepts import load_concepts  # noqa: E402

RAW = ROOT / "data" / "raw" / "youtube"
API = "https://www.googleapis.com/youtube/v3"
RESULTS_PER_SEARCH = 15   # enough to find 3 good how-tos after sorting by views
SLEEP_SECONDS = 1         # quota, not rate, is the limit; a small gap is plenty


def main():
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        sys.exit("Set YOUTUBE_API_KEY first.")
    RAW.mkdir(parents=True, exist_ok=True)
    out = {"fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "concepts": {}}
    for c in load_concepts():
        raw_path = RAW / f"{c['id']}.json"
        if raw_path.exists():
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
        else:
            q = f"{c['aliases']['en'][0]} recipe how to make"
            s = requests.get(f"{API}/search", params={
                "part": "snippet", "q": q, "type": "video", "maxResults": RESULTS_PER_SEARCH,
                "relevanceLanguage": "en", "key": key}, timeout=20).json()
            ids = [i["id"]["videoId"] for i in s.get("items", [])]
            v = {}
            if ids:
                v = requests.get(f"{API}/videos", params={
                    "part": "snippet,statistics", "id": ",".join(ids), "key": key}, timeout=20).json()
            raw = {"query": q, "search": s, "videos": v}
            raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
            time.sleep(SLEEP_SECONDS)
        vids = []
        for item in raw.get("videos", {}).get("items", []):
            vids.append({
                "video_id": item["id"], "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "views": int(item.get("statistics", {}).get("viewCount", 0)),
            })
        out["concepts"][c["id"]] = sorted(vids, key=lambda x: x["views"], reverse=True)
        print(f"{c['id']}: {len(vids)} videos")
    (ROOT / "data" / "youtube.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
