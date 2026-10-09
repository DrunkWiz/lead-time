"""What changed: a weekly feed of new takeoffs and status changes. Pure code.

Each step re-runs the forecast as it would have read at the end of that week,
so the feed is exactly what someone checking weekly would have been told.
"""
import datetime as dt

from . import words
from .forecast import HOME, REGION_NAMES, forecast_all
from .series import parse_date

FEED_WEEKS = 8          # default look-back: two months of weekly check-ins
MAX_FEED_WEEKS = 26     # cap so one request can't ask for years of re-forecasting

STATUS_TEXT = {
    "arriving_now": "is arriving in Singapore now",
    "rising_abroad": "is heading this way",
    "already_here": "has taken off in Singapore",
    "peaked_here": "has peaked in Singapore and is cooling",
    "not_travelling": "stalled before reaching Singapore",
}
# Status changes worth telling a shop about; others (e.g. not_travelling -> not_travelling) are noise.
IMPORTANCE = {"arriving_now": 3, "rising_abroad": 2, "already_here": 2, "peaked_here": 1, "not_travelling": 1}


def _events(prev, cur, concept, seen_on):
    out = []
    name = concept["name"]
    for geo, week in sorted(cur["takeoffs"].items(), key=lambda x: x[1]):
        if geo in prev["takeoffs"]:
            continue
        where = "Singapore" if geo == HOME else REGION_NAMES.get(geo, geo)
        out.append({
            "kind": "takeoff", "concept_id": concept["id"], "name": name, "geo": geo,
            "seen_on": seen_on, "week": week, "importance": 3 if geo == HOME else 2,
            "text": f"{name} took off in {where} (week of {words.day_month_year(week)}).",
        })
    if prev["status"] != cur["status"]:
        text = STATUS_TEXT[cur["status"]]
        if (prev["status"], cur["status"]) == ("peaked_here", "already_here"):
            text = "is picking up again in Singapore"
        out.append({
            "kind": "status", "concept_id": concept["id"], "name": name,
            "from": prev["status"], "to": cur["status"], "seen_on": seen_on, "week": seen_on,
            "importance": IMPORTANCE[cur["status"]],
            "text": f"{name} {text}.",
        })
    return out


def changes(snapshot, concepts, as_of, weeks=FEED_WEEKS):
    """Events from the last `weeks` weekly check-ins up to as_of, newest first."""
    weeks = max(1, min(int(weeks), MAX_FEED_WEEKS))
    end = parse_date(as_of)
    dates = [end - dt.timedelta(weeks=k) for k in range(weeks, -1, -1)]  # oldest first
    states = [forecast_all(snapshot, concepts, d.isoformat())[0] for d in dates]
    events = []
    for k in range(1, len(dates)):
        for c, prev, cur in zip(concepts, states[k - 1], states[k]):
            events.extend(_events(prev, cur, c, dates[k].isoformat()))
    events.sort(key=lambda e: (e["seen_on"], e["importance"]), reverse=True)
    return {"as_of": end.isoformat(), "since": dates[0].isoformat(), "weeks": weeks, "events": events}
