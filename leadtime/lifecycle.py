"""How long trends last in Singapore, and where a food is in its run. Pure code.

A food's *first wave* starts at its Singapore takeoff and ends the first week
the recent mean (of the smoothed series) falls below PEAK_DROP x the peak so
far. Waves still running at as_of are censored: we know they've lasted at
least that long, but they don't count towards the typical length.
"""
import statistics

from .config import (CLIMBING_PEAK_WEEKS, CLIMBING_SHARE, HOME, MIN_CASES, PEAK_DROP, PEAK_RECENT_WEEKS,
                     STEADY_WEEKS, WINDOW_PERCENTILES)
from .forecast import percentile, takeoffs
from .series import cut
from .takeoff import _clean


def first_wave(weeks, sg_values, sg_week, as_of):
    """{"length": weeks or None, "ongoing": bool, "elapsed": weeks since takeoff,
    "peak_week": iso, "climbing": bool (ongoing, near its peak, and the peak is recent),
    "steady": bool (ongoing, and searched in every one of the last STEADY_WEEKS raw weeks)}.

    Google reports weeks below its privacy threshold as zero, so a run of
    non-zero raw weeks means real, sustained search volume rather than spikes.
    """
    w, raw = cut(weeks, sg_values, as_of)
    v = _clean(raw)
    start = w.index(sg_week)
    peak, peak_i = 0, start
    for i in range(start, len(v)):
        if v[i] > peak:
            peak, peak_i = v[i], i
        recent = statistics.mean(v[max(start, i - PEAK_RECENT_WEEKS + 1):i + 1])
        if peak > 0 and recent < PEAK_DROP * peak:
            return {"length": i - start, "ongoing": False, "elapsed": len(v) - 1 - start,
                    "peak_week": w[peak_i], "climbing": False, "steady": False}
    last = len(v) - 1
    recent = statistics.mean(v[max(start, last - PEAK_RECENT_WEEKS + 1):last + 1])
    climbing = peak > 0 and recent >= CLIMBING_SHARE * peak and last - peak_i <= CLIMBING_PEAK_WEEKS
    tail = raw[-STEADY_WEEKS:]
    steady = len(tail) == STEADY_WEEKS and all(x is not None and x > 0 for x in tail)
    return {"length": None, "ongoing": True, "elapsed": last - start, "peak_week": w[peak_i],
            "climbing": climbing, "steady": steady}


def waves(snapshot, concepts, as_of):
    """First wave for every concept that has taken off in Singapore by as_of."""
    out = []
    for c in concepts:
        geo_series = snapshot["series"].get(c["id"], {})
        tk = takeoffs(snapshot["weeks"], geo_series, as_of)
        if HOME not in tk:
            continue
        fw = first_wave(snapshot["weeks"], geo_series[HOME], tk[HOME], as_of)
        out.append(dict(fw, concept_id=c["id"], name=c["name"], category=c["category"], sg_week=tk[HOME]))
    return out


def lifespan(snapshot, concepts, as_of):
    """Typical first-wave length from waves that had ended by as_of, or None if too few."""
    rows = waves(snapshot, concepts, as_of)
    done = sorted(r["length"] for r in rows if not r["ongoing"])
    if len(done) < MIN_CASES:
        return {"typical": None, "n_cases": len(done), "rows": rows}
    lo, hi = WINDOW_PERCENTILES
    longest = sorted((r for r in rows if not r["ongoing"]), key=lambda r: -r["length"])[:3]
    return {
        "typical": {"low": round(percentile(done, lo)), "high": round(percentile(done, hi)),
                    "median": round(statistics.median(done))},
        "n_cases": len(done),
        "longest": [{"name": r["name"], "length": r["length"]} for r in longest],
        "rows": rows,
    }


def phase(elapsed, typical):
    """Where a food sits in a typical run: early, middle, late or overtime."""
    if typical is None:
        return None
    if elapsed < typical["low"] * 0.5:
        return "early"
    if elapsed < typical["median"]:
        return "middle"
    if elapsed <= typical["high"]:
        return "late"
    return "overtime"
