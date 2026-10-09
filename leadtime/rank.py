"""Ranking: status, then verdict, then earliest arrival. Pure code."""
from .config import MORE_N, TOP_N

STATUS_ORDER = {"arriving_now": 0, "rising_abroad": 1}
VERDICT_ORDER = {"make": 0, "adapt": 1}
FAR_FUTURE = "9999-12-31"   # concepts with no window sort after any dated one


def rank(items):
    """items: [{"forecast": {...}, "fit": {...}|None, ...}] -> (top, more).

    Only concepts that are still ahead of Singapore are candidates. Skips and
    concepts the model couldn't judge (fit None) are dropped.
    """
    candidates = [
        it for it in items
        if it["forecast"]["status"] in STATUS_ORDER
        and it.get("fit") and it["fit"]["verdict"] in VERDICT_ORDER
    ]

    def key(it):
        fc = it["forecast"]
        start = (fc.get("window") or {}).get("start") or FAR_FUTURE
        return (STATUS_ORDER[fc["status"]], VERDICT_ORDER[it["fit"]["verdict"]], start, fc["concept_id"])

    candidates.sort(key=key)
    return candidates[:TOP_N], candidates[TOP_N:TOP_N + MORE_N]
