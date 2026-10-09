"""Lags, arrival windows and status. Pure code: no model input anywhere."""
import datetime as dt
import statistics

from . import takeoff
from .config import (HOME, MIN_CASES, NO_WINDOW_STALE_WEEKS, NOT_TRAVELLING_GRACE_WEEKS, WIDE_WINDOW_WEEKS,
                     PEAK_DROP, PEAK_RECENT_WEEKS, PEAK_REVIVE, WINDOW_PERCENTILES)
from .series import cut, parse_date

REGION_NAMES = {
    "SG": "Singapore", "KR": "South Korea", "JP": "Japan", "TW": "Taiwan",
    "AE": "the UAE", "US": "the US", "MY": "Malaysia",
}
STATUSES = ["arriving_now", "rising_abroad", "already_here", "peaked_here", "not_travelling"]


def weeks_between(a, b):
    """Whole weeks from date a to date b (b later => positive)."""
    return round((parse_date(b) - parse_date(a)).days / 7)


def add_weeks(d, n):
    return parse_date(d) + dt.timedelta(weeks=n)


def percentile(xs, p):
    """Linear-interpolated percentile (same as numpy's default)."""
    xs = sorted(xs)
    if len(xs) == 1:
        return float(xs[0])
    k = (len(xs) - 1) * p / 100
    lo = int(k)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def takeoffs(weeks, geo_series, as_of):
    """{geo: takeoff week} for every region whose takeoff is confirmed by as_of."""
    out = {}
    for geo, values in geo_series.items():
        t = takeoff.detect(weeks, values, as_of)
        if t:
            out[geo] = t
    return out


def origin_of(tk):
    """Earliest non-home takeoff as (geo, week), or (None, None)."""
    abroad = [(w, g) for g, w in tk.items() if g != HOME]
    if not abroad:
        return None, None
    w, g = min(abroad)
    return g, w


def historical_cases(snapshot, concepts, as_of):
    """Every concept that took off abroad then in SG, both confirmed by as_of."""
    weeks = snapshot["weeks"]
    cases = []
    for c in concepts:
        geo_series = snapshot["series"].get(c["id"], {})
        tk = takeoffs(weeks, geo_series, as_of)
        og, ow = origin_of(tk)
        if HOME not in tk or not og:
            continue
        lag = weeks_between(ow, tk[HOME])
        cases.append({
            "concept_id": c["id"], "category": c["category"],
            "origin": og, "origin_week": ow, "sg_week": tk[HOME], "lag_weeks": lag,
        })
    return cases


def window_from_cases(cases, category):
    """Lag range from past cases that actually travelled (lag > 0).

    Same category if it has MIN_CASES, else all categories, else None.
    """
    travelled = [c for c in cases if c["lag_weeks"] > 0]
    same = [c["lag_weeks"] for c in travelled if c["category"] == category]
    if len(same) >= MIN_CASES:
        lags, basis = same, "category"
    elif len(travelled) >= MIN_CASES:
        lags, basis = [c["lag_weeks"] for c in travelled], "all"
    else:
        return None
    lo, hi = WINDOW_PERCENTILES
    lag_low, lag_high = round(percentile(lags, lo)), round(percentile(lags, hi))
    return {
        "lag_low": lag_low,
        "lag_high": lag_high,
        "n_cases": len(lags),
        "basis": basis,
        "wide": lag_high - lag_low > WIDE_WINDOW_WEEKS,
    }


def _sg_peaked(weeks, values, sg_week, as_of):
    """Walk forward from the SG takeoff with two thresholds (hysteresis):
    cooled once the recent mean drops below PEAK_DROP x peak-so-far, and back
    to popular only once it climbs above PEAK_REVIVE x peak-so-far."""
    w, v = cut(weeks, values, as_of)
    v = [0 if x is None else x for x in v]
    start = w.index(sg_week)
    peak, peaked = 0, False
    for i in range(start, len(v)):
        peak = max(peak, v[i])
        recent = statistics.mean(v[max(start, i - PEAK_RECENT_WEEKS + 1):i + 1])
        if not peaked and recent < PEAK_DROP * peak:
            peaked = True
        elif peaked and recent > PEAK_REVIVE * peak:
            peaked = False
    return peaked


def forecast(concept, snapshot, concepts, as_of, cases=None):
    """Status, origin, takeoff weeks and arrival window for one concept at as_of."""
    weeks = snapshot["weeks"]
    geo_series = snapshot["series"].get(concept["id"], {})
    tk = takeoffs(weeks, geo_series, as_of)
    og, ow = origin_of(tk)
    if cases is None:
        cases = historical_cases(snapshot, concepts, as_of)
    out = {
        "concept_id": concept["id"],
        "as_of": str(as_of),
        "takeoffs": tk,
        "origin": og,
        "origin_name": REGION_NAMES.get(og),
        "origin_week": ow,
        "sg_week": tk.get(HOME),
        "window": None,
        "status": None,
        "sg_rising": False,
    }

    if HOME in tk:
        peaked = _sg_peaked(weeks, geo_series[HOME], tk[HOME], as_of)
        out["status"] = "peaked_here" if peaked else "already_here"
        return out
    if not og:
        out["status"] = "not_travelling"
        return out

    win = window_from_cases(cases, concept["category"])
    as_of_d = parse_date(as_of)
    out["sg_rising"] = takeoff.rising_now(weeks, geo_series.get(HOME, []), as_of)
    if win:
        start = add_weeks(ow, win["lag_low"])
        end = add_weeks(ow, win["lag_high"])
        out["window"] = dict(win, start=start.isoformat(), end=end.isoformat())
        if as_of_d > add_weeks(end, NOT_TRAVELLING_GRACE_WEEKS):
            out["status"] = "not_travelling"
        elif out["sg_rising"] or (as_of_d >= start and not win["wide"]):
            # a wide window opening proves nothing; only Singapore itself moving does
            out["status"] = "arriving_now"
        else:
            out["status"] = "rising_abroad"
    else:
        if as_of_d > add_weeks(ow, NO_WINDOW_STALE_WEEKS):
            out["status"] = "not_travelling"
        elif out["sg_rising"]:
            out["status"] = "arriving_now"
        else:
            out["status"] = "rising_abroad"
    return out


def forecast_all(snapshot, concepts, as_of):
    cases = historical_cases(snapshot, concepts, as_of)
    return [forecast(c, snapshot, concepts, as_of, cases) for c in concepts], cases
