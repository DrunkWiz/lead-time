"""Weekly series per concept per region, and the as_of cut that every reader uses.

Series layout (data/series.json):
    {"weeks": ["2021-10-10", ...],              # week start dates (Sunday), ascending
     "series": {concept_id: {geo: [int|null, ...]}}}  # aligned to weeks; null = no data

A week counts as observed at `as_of` only once it has fully ended
(week start + 6 days <= as_of). Nothing downstream ever sees a later week.
"""
import datetime as dt
import json
from pathlib import Path

WEEK_DAYS = 7


def parse_date(s):
    if isinstance(s, dt.date):
        return s
    return dt.date.fromisoformat(s)


def week_end(week_start):
    return parse_date(week_start) + dt.timedelta(days=WEEK_DAYS - 1)


def observed_count(weeks, as_of):
    """Number of leading weeks fully observed at as_of."""
    as_of = parse_date(as_of)
    n = 0
    for w in weeks:
        if week_end(w) > as_of:
            break
        n += 1
    return n


def cut(weeks, values, as_of):
    """(weeks, values) truncated to what was observable at as_of."""
    n = observed_count(weeks, as_of)
    return weeks[:n], values[:n]


def combine_terms(record, allowed=None):
    """Sum a raw Trends record's alias columns into one series.

    Aliases come from a single request, so they share one 0-100 scale and
    summing them is meaningful. Partial (still-running) weeks are dropped.
    Columns for terms not in `allowed` (aliases since removed) are ignored.
    """
    dates = record.get("dates") or []
    partial = record.get("is_partial") or [False] * len(dates)
    cols = [v for t, v in record.get("values", {}).items() if v and (allowed is None or t in allowed)]
    out = {}
    for i, d in enumerate(dates):
        if partial[i]:
            continue
        out[d] = sum(col[i] for col in cols) if cols else 0
    return out


def build(raw_records, allowed_terms=None):
    """raw_records: iterable of raw Trends dicts -> series.json structure.
    allowed_terms: optional {concept_id: [terms]} to keep."""
    by_concept = {}
    all_weeks = set()
    for rec in raw_records:
        s = combine_terms(rec, (allowed_terms or {}).get(rec["concept_id"]))
        all_weeks.update(s)
        by_concept.setdefault(rec["concept_id"], {})[rec["geo"]] = s
    weeks = sorted(all_weeks)
    series = {
        cid: {geo: [s.get(w) for w in weeks] for geo, s in geos.items()}
        for cid, geos in by_concept.items()
    }
    return {"weeks": weeks, "series": series}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
