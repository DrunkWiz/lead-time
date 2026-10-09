"""Hand-made series for tests. No network, no keys."""
import datetime as dt

START = dt.date(2022, 1, 2)   # a Sunday
N_WEEKS = 120


def weeks(n=N_WEEKS):
    return [(START + dt.timedelta(weeks=i)).isoformat() for i in range(n)]


def flat(level=5, n=N_WEEKS):
    return [level] * n


def step(at, low=3, high=40, n=N_WEEKS):
    """Flat at `low`, then jumps to `high` at week `at` and stays."""
    return [low if i < at else high for i in range(n)]


def spike(at, low=3, high=80, n=N_WEEKS):
    """One-week spike at `at`."""
    return [high if i == at else low for i in range(n)]


def rise_and_fall(at, low=3, high=60, length=20, n=N_WEEKS):
    """Takes off at `at`, stays up for `length` weeks, then falls back near `low`."""
    return [high if at <= i < at + length else low for i in range(n)]


def concept(cid, category="dessert", equipment=("stovetop",)):
    return {
        "id": cid, "name": cid.replace("-", " ").title(), "aliases": {"en": [cid]},
        "description": f"Test food {cid}.", "category": category,
        "key_ingredients": ["sugar", "flour"], "techniques": ["baking"],
        "equipment": list(equipment),
    }


def history_snapshot(lags=(6, 8, 10, 12), origin_at=20, current_origin_at=90):
    """Four past concepts that travelled KR -> SG with the given lags, plus one
    'current' concept that took off in KR at `current_origin_at` and not yet in SG."""
    w = weeks()
    series, concepts = {}, []
    for k, lag in enumerate(lags):
        cid = f"past-{k}"
        o = origin_at + k * 5
        series[cid] = {"KR": step(o), "SG": step(o + lag)}
        concepts.append(concept(cid))
    series["current"] = {"KR": step(current_origin_at), "SG": flat(3)}
    concepts.append(concept("current"))
    return {"weeks": w, "series": series}, concepts
