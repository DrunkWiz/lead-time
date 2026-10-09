"""Backtest: for every concept that took off abroad, rewind to the first day we
could have flagged it, forecast with only the data visible then, and compare
with what actually happened in Singapore."""
import statistics

from .config import NOT_TRAVELLING_GRACE_WEEKS, SUSTAIN
from .forecast import (HOME, add_weeks, forecast, historical_cases, origin_of, takeoffs,
                       weeks_between, window_from_cases)
from .series import parse_date, week_end


def flag_date(origin_week):
    """First as_of at which the origin takeoff is confirmed (SUSTAIN weeks observed after it)."""
    return week_end(add_weeks(origin_week, SUSTAIN[1]))


def run(snapshot, concepts, final_as_of):
    weeks = snapshot["weeks"]
    rows = []
    for c in concepts:
        tk = takeoffs(weeks, snapshot["series"].get(c["id"], {}), final_as_of)
        og, ow = origin_of(tk)
        if not og:
            continue
        flagged = flag_date(ow)
        actual = tk.get(HOME)
        fc = forecast(c, snapshot, concepts, flagged.isoformat())
        win = fc["window"]
        row = {
            "concept_id": c["id"], "name": c["name"], "category": c["category"],
            "origin": og, "origin_week": ow, "flagged_on": flagged.isoformat(),
            "status_then": fc["status"], "window": win, "actual_sg_week": actual,
            "outcome": None, "miss_weeks": None, "warning_weeks": None,
        }
        if actual and parse_date(actual) <= flagged:
            row["outcome"] = "already_here"        # SG moved before we could have known
        elif not win:
            row["outcome"] = "no_forecast"         # not enough history at the time
        elif actual:
            a, s, e = parse_date(actual), parse_date(win["start"]), parse_date(win["end"])
            row["warning_weeks"] = weeks_between(flagged, actual)
            if s <= a <= e:
                row["outcome"], row["miss_weeks"] = "inside", 0
            elif a < s:
                row["outcome"], row["miss_weeks"] = "early", weeks_between(a, s)
            else:
                row["outcome"], row["miss_weeks"] = "late", weeks_between(e, a)
        elif parse_date(final_as_of) > add_weeks(win["end"], NOT_TRAVELLING_GRACE_WEEKS):
            row["outcome"] = "never_arrived"       # we'd have predicted it; it didn't come
        else:
            row["outcome"] = "pending"
        rows.append(row)

    judged = [r for r in rows if r["outcome"] in ("inside", "early", "late", "never_arrived")]
    hits = [r for r in judged if r["outcome"] == "inside"]
    misses = [r["miss_weeks"] for r in judged if r["miss_weeks"] is not None]
    warnings = [r["warning_weeks"] for r in rows if r["warning_weeks"] is not None and r["warning_weeks"] > 0]
    summary = {
        "concepts_flagged": len(rows),
        "forecasts_judged": len(judged),
        "inside_window": len(hits),
        "median_miss_weeks": statistics.median(misses) if misses else None,
        "median_warning_weeks": statistics.median(warnings) if warnings else None,
        "outcomes": {k: sum(1 for r in rows if r["outcome"] == k)
                     for k in ("inside", "early", "late", "never_arrived", "already_here", "no_forecast", "pending")},
    }
    return {"as_of": str(final_as_of), "summary": summary, "rows": rows,
            "leave_one_out": leave_one_out(snapshot, concepts, final_as_of),
            "late_entry": late_entry(snapshot, concepts, final_as_of)}


def late_entry(snapshot, concepts, final_as_of):
    """Is it worth joining a trend that's already here? For each Singapore takeoff,
    rewind to the day it was confirmed, ask the decision rule (timing only), and
    compare with how many selling weeks were actually left."""
    from .decision import decide
    from .lifecycle import first_wave, lifespan
    from .config import MIN_SELLING_WEEKS, SETUP_WEEKS
    rows = []
    for c in concepts:
        geo = snapshot["series"].get(c["id"], {})
        tk = takeoffs(snapshot["weeks"], geo, final_as_of)
        if HOME not in tk:
            continue
        confirmed = flag_date(tk[HOME]).isoformat()
        fc = forecast(c, snapshot, concepts, confirmed)
        if fc["status"] not in ("already_here", "peaked_here"):
            continue
        life = lifespan(snapshot, concepts, confirmed)
        wave_then = first_wave(snapshot["weeks"], geo[HOME], tk[HOME], confirmed)
        wave_final = first_wave(snapshot["weeks"], geo[HOME], tk[HOME], final_as_of)
        d = decide(fc, None, {"kind": "following", "date": None, "text": ""}, life, wave_then, confirmed,
                   {"price": None, "cost": None, "units_per_week": None})
        call = d["verdict"] if d["verdict"] in ("go_late", "skip") else "no_call"
        if wave_final["ongoing"]:
            actual_left, worth = None, None
        else:
            actual_left = wave_final["length"] - wave_then["elapsed"]
            worth = actual_left >= SETUP_WEEKS + MIN_SELLING_WEEKS
        right = None if (worth is None or call == "no_call") else (call == "go_late") == worth
        rows.append({"concept_id": c["id"], "name": c["name"], "confirmed_on": confirmed, "call": call,
                     "weeks_in": wave_then["elapsed"], "actual_weeks_left": actual_left, "worth_it": worth, "right": right})
    judged = [r for r in rows if r["right"] is not None]
    return {"rows": rows, "judged": len(judged), "right": sum(1 for r in judged if r["right"])}


def leave_one_out(snapshot, concepts, final_as_of):
    """Do lags generalise? Predict each travelled case's lag from all the others.

    This ignores time order (other cases may have resolved later), so it is a
    check on the lag distribution, not a replay of what we'd have said then.
    The strict replay is run() above.
    """
    cases = [c for c in historical_cases(snapshot, concepts, final_as_of) if c["lag_weeks"] > 0]
    rows = []
    for c in cases:
        others = [o for o in cases if o["concept_id"] != c["concept_id"]]
        win = window_from_cases(others, c["category"])
        if not win:
            rows.append({"concept_id": c["concept_id"], "lag_weeks": c["lag_weeks"], "window": None, "inside": None, "miss_weeks": None})
            continue
        lo, hi, lag = win["lag_low"], win["lag_high"], c["lag_weeks"]
        miss = 0 if lo <= lag <= hi else (lo - lag if lag < lo else lag - hi)
        rows.append({"concept_id": c["concept_id"], "lag_weeks": lag, "window": [lo, hi],
                     "inside": miss == 0, "miss_weeks": miss})
    judged = [r for r in rows if r["inside"] is not None]
    return {
        "cases": len(cases),
        "judged": len(judged),
        "inside": sum(1 for r in judged if r["inside"]),
        "median_miss_weeks": statistics.median([r["miss_weeks"] for r in judged]) if judged else None,
        "rows": rows,
    }
