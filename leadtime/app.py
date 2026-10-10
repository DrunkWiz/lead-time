"""HTTP-agnostic API. api/index.py (Vercel) and scripts/dev_server.py both call route()."""
import datetime as dt
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import unquote

from . import backtest, config, content, data, decision, feed, fit, launch, lifecycle, offers, rank, words
from .forecast import HOME, REGION_NAMES, forecast, forecast_all
from .providers import Chain, OfflineProvider
from .schema import SchemaError
from .series import cut, parse_date

SPARK_WEEKS = 78          # sparkline shows the last ~18 months before as_of
FIT_WORKERS = 6           # model calls in parallel so a cold request stays under the function timeout
MIN_HISTORY_WEEKS = 16    # as_of needs a baseline's worth of data behind it
MAX_PLAN_ITEMS = 12       # a menu plan, not the whole catalogue

_chain = None


def chain():
    global _chain
    if _chain is None:
        _chain = Chain(offline=OfflineProvider({"fit": fit.offline_fit, "launch": launch.offline_plan}))
    return _chain


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def _as_of(value):
    snap = data.snapshot_date()
    if not snap:
        raise ApiError(503, "No trend snapshot yet. Run scripts/fetch_trends.py then scripts/build_series.py.")
    if not value:
        return snap
    try:
        d = parse_date(value)
    except ValueError:
        raise ApiError(400, "as_of must look like 2025-03-01.")
    first = parse_date(data.snapshot()["weeks"][0]) + dt.timedelta(weeks=MIN_HISTORY_WEEKS)
    if d > parse_date(snap):
        raise ApiError(400, f"Our data stops at {words.day_month_year(snap)}. Pick an earlier date.")
    if d < first:
        raise ApiError(400, f"Our data starts too late for that. Pick a date after {words.day_month_year(first)}.")
    return d.isoformat()


def _concept(cid):
    for c in data.concepts():
        if c["id"] == cid:
            return c
    raise ApiError(404, f"No food called {cid!r} in our list.")


def _summary(c, fc):
    return {
        "id": c["id"], "name": c["name"], "category": c["category"], "description": c["description"],
        "status": fc["status"], "status_label": words.status_label(fc["status"]),
        "why": words.why(fc), "evidence": words.evidence(fc),
        "origin": fc["origin"], "origin_name": fc["origin_name"],
        "origin_week": fc["origin_week"], "sg_week": fc["sg_week"],
        "window": fc["window"], "takeoffs": fc["takeoffs"],
    }


def _spark(c, fc, as_of, weeks_back=SPARK_WEEKS):
    snap = data.snapshot()
    series = snap["series"].get(c["id"], {})
    origin = fc["origin"] or next((g for g in series if g != HOME), None)
    w_all = snap["weeks"]
    out = {"origin": origin, "origin_name": REGION_NAMES.get(origin), "weeks": [], "lines": {}}
    for geo in [origin, HOME]:
        if geo and geo in series:
            w, v = cut(w_all, series[geo], as_of)
            out["weeks"] = w[-weeks_back:]
            out["lines"][geo] = v[-weeks_back:]
    return out


def _profile(body):
    try:
        return fit.normalise_profile(body.get("profile") or {})
    except SchemaError as e:
        raise ApiError(400, f"That shop profile doesn't look right ({e}).")


DERIVED_DIR = Path(__file__).resolve().parent.parent / "data" / "cache" / "derived"
DERIVED_MAX = 256       # distinct (name, as_of) results kept in memory before starting over
_derived = {}
_derived_lock = threading.Lock()


def _derived_path(key):
    return DERIVED_DIR / (re.sub(r"[^A-Za-z0-9_.-]", "_", key) + ".json")


def derived(name, compute):
    """Results that depend only on the snapshot (backtest, weekly feed): computed once per
    process. scripts/precompute.py can write them at deploy time, because a free-tier CPU
    takes over ten seconds for the backtest. Keyed by snapshot so a data refresh misses."""
    key = f"{name}__{data.meta().get('fetched_at')}"
    with _derived_lock:   # one computation at a time; a second caller waits for the first
        if key not in _derived:
            if len(_derived) >= DERIVED_MAX:
                _derived.clear()
            path = _derived_path(key)
            _derived[key] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else compute()
        return _derived[key]


def get_meta(q, body):
    m = data.meta()
    weeks = data.snapshot()["weeks"]
    return {
        "fetched_at": m.get("fetched_at"),
        "snapshot_date": data.snapshot_date(),
        "first_week": weeks[0] if weeks else None,
        "earliest_as_of": (parse_date(weeks[0]) + dt.timedelta(weeks=MIN_HISTORY_WEEKS)).isoformat() if weeks else None,
        "regions": [{"code": g, "name": REGION_NAMES[g]} for g in m.get("regions", REGION_NAMES)],
        "sources": m.get("sources", []),
        "concept_count": len(data.concepts()),
        "youtube_fetched_at": data.youtube().get("fetched_at"),
        "method": {
            "takeoff_ratio": config.TAKEOFF_RATIO, "sustain": list(config.SUSTAIN),
            "baseline_weeks": config.BASELINE_WEEKS, "baseline_gap_weeks": config.BASELINE_GAP_WEEKS,
            "smooth_weeks": config.SMOOTH_WEEKS, "min_cases": config.MIN_CASES,
            "window_percentiles": list(config.WINDOW_PERCENTILES),
        },
        "agent": {"ladder": chain().ladder(), "attempts": []},
    }


def get_concepts(q, body):
    as_of = _as_of(q.get("as_of"))
    fcs, cases = forecast_all(data.snapshot(), data.concepts(), as_of)
    items = [_summary(c, fc) for c, fc in zip(data.concepts(), fcs)]
    return {"as_of": as_of, "concepts": items, "history_cases": len(cases), "agent": {"attempts": []}}


def get_concept(cid, q, body):
    as_of = _as_of(q.get("as_of"))
    c = _concept(cid)
    fc = forecast(c, data.snapshot(), data.concepts(), as_of)
    snap = data.snapshot()
    series = {}
    weeks = []
    for geo, values in snap["series"].get(cid, {}).items():
        weeks, series[geo] = cut(snap["weeks"], values, as_of)
    out = _summary(c, fc)
    out.update({
        "as_of": as_of, "aliases": c["aliases"], "key_ingredients": c["key_ingredients"],
        "techniques": c["techniques"], "equipment": c["equipment"],
        "series": {"weeks": weeks, "regions": series},
        "region_names": REGION_NAMES,
        "agent": {"attempts": []},
    })
    return out


def post_recommend(q, body):
    as_of = _as_of(body.get("as_of"))
    profile = _profile(body)
    fcs, _ = forecast_all(data.snapshot(), data.concepts(), as_of)
    pairs = [(c, fc) for c, fc in zip(data.concepts(), fcs) if fc["status"] in rank.STATUS_ORDER]

    with ThreadPoolExecutor(max_workers=FIT_WORKERS) as pool:
        judged = list(pool.map(lambda p: fit.judge(chain(), p[0], profile), pairs))

    items, attempts = [], []
    for (c, fc), j in zip(pairs, judged):
        attempts.append({"concept_id": c["id"], "provider": j["provider"], "cached": j["cached"],
                         "attempts": j["attempts"]})
        items.append({"concept": c, "forecast": fc, "fit": j["fit"], "fit_provider": j["provider"]})
    top, more = rank.rank(items)

    def card(it):
        c, fc = it["concept"], it["forecast"]
        return dict(_summary(c, fc), fit=it["fit"], fit_provider=it["fit_provider"],
                    launch=launch.launch_when(fc, as_of), spark=_spark(c, fc, as_of))

    skipped = [{"id": it["concept"]["id"], "name": it["concept"]["name"], "reason": it["fit"]["reason"]}
               for it in items if it["fit"] and it["fit"]["verdict"] == "skip"]
    here = [{"id": c["id"], "name": c["name"], "status": fc["status"]}
            for c, fc in zip(data.concepts(), fcs) if fc["status"] in ("already_here", "peaked_here")]
    empty = None
    if not top:
        empty = ("Nothing we track is heading for Singapore right now that fits your kitchen. "
                 "Try another date in backtest mode, or add equipment.") if pairs else (
                 "Nothing we track is heading for Singapore right now. Try another date in backtest mode.")
    return {"as_of": as_of, "snapshot_date": data.snapshot_date(), "profile": profile,
            "cards": [card(i) for i in top], "more": [card(i) for i in more],
            "skipped": skipped, "already_here": here, "empty": empty,
            "agent": {"attempts": attempts}}


def post_launch(q, body):
    as_of = _as_of(body.get("as_of"))
    profile = _profile(body)
    c = _concept(body.get("concept_id") or "")
    fc = forecast(c, data.snapshot(), data.concepts(), as_of)
    j = fit.judge(chain(), c, profile)
    p = launch.plan(chain(), c, profile, j["fit"], fc, as_of, data.youtube())
    return {"as_of": as_of, "concept": _summary(c, fc), "fit": j["fit"], "fit_provider": j["provider"],
            "when": p["when"], "plan": p["plan"], "plan_provider": p["provider"],
            "disclaimer": p["disclaimer"], "links": p["links"],
            "agent": {"attempts": [{"step": "fit", "provider": j["provider"], "attempts": j["attempts"]},
                                   {"step": "launch", "provider": p["provider"], "attempts": p["attempts"]}]}}


def get_changes(q, body):
    as_of = _as_of(q.get("as_of"))
    try:
        weeks = int(q.get("weeks") or feed.FEED_WEEKS)
    except ValueError:
        raise ApiError(400, "weeks must be a whole number.")
    out = derived(f"changes_{as_of}_{weeks}",
                  lambda: feed.changes(data.snapshot(), data.concepts(), as_of, weeks))
    return dict(out, agent={"attempts": []})


def post_plan(q, body):
    """The shop's planned items: launch timing (code), kitchen fit (model, cached),
    and a combined shopping and equipment list built from the concept records."""
    as_of = _as_of(body.get("as_of"))
    profile = _profile(body)
    ids = body.get("concept_ids") or []
    if not isinstance(ids, list) or len(ids) > MAX_PLAN_ITEMS:
        raise ApiError(400, f"Send up to {MAX_PLAN_ITEMS} foods to plan.")
    items, attempts = [], []
    shopping, kit = {}, {}
    for cid in dict.fromkeys(ids):
        c = _concept(cid)
        fc = forecast(c, data.snapshot(), data.concepts(), as_of)
        j = fit.judge(chain(), c, profile)
        attempts.append({"concept_id": cid, "provider": j["provider"], "attempts": j["attempts"]})
        items.append(dict(_summary(c, fc), fit=j["fit"], fit_provider=j["provider"],
                          launch=launch.launch_when(fc, as_of), key_ingredients=c["key_ingredients"]))
        if j["fit"] and j["fit"]["verdict"] == "skip":
            continue
        for ing in c["key_ingredients"]:
            shopping.setdefault(ing, []).append(c["name"])
        for e in (j["fit"] or {}).get("missing_equipment", []):
            kit.setdefault(e, []).append(c["name"])

    def when_key(it):
        return it["launch"]["date"] or "9999-12-31"
    items.sort(key=when_key)
    return {"as_of": as_of, "items": items,
            "shopping": [{"ingredient": k, "for": v} for k, v in sorted(shopping.items(), key=lambda x: (-len(x[1]), x[0]))],
            "missing_equipment": [{"equipment": k, "for": v} for k, v in sorted(kit.items())],
            "agent": {"attempts": attempts}}


def _life_and_wave(c, fc, as_of):
    life = lifecycle.lifespan(data.snapshot(), data.concepts(), as_of)
    wave = None
    if fc["sg_week"]:
        wave = lifecycle.first_wave(data.snapshot()["weeks"], data.snapshot()["series"][c["id"]][HOME],
                                    fc["sg_week"], as_of)
    return life, wave


def _life_public(life):
    return {k: life.get(k) for k in ("typical", "n_cases", "longest")}


def post_decision(q, body):
    """Go / Wait / Skip for one food, with run length, money and a stock plan."""
    as_of = _as_of(body.get("as_of"))
    profile = _profile(body)
    c = _concept(body.get("concept_id") or "")
    fc = forecast(c, data.snapshot(), data.concepts(), as_of)
    j = fit.judge(chain(), c, profile)
    when = launch.launch_when(fc, as_of)
    life, wave = _life_and_wave(c, fc, as_of)
    d = decision.decide(fc, j["fit"], when, life, wave, as_of, decision.clean_inputs(body.get("inputs")))
    return {"as_of": as_of, "concept_id": c["id"], "decision": d, "lifespan": _life_public(life), "wave": wave,
            "agent": {"attempts": [{"step": "fit", "provider": j["provider"], "attempts": j["attempts"]}]}}


def post_review(q, body):
    """Keep / push / drop for a launched item. Sales come from the shop's device; nothing is stored."""
    as_of = _as_of(body.get("as_of"))
    c = _concept(body.get("concept_id") or "")
    logs = body.get("logs") or []
    if not isinstance(logs, list) or len(logs) > 520:
        raise ApiError(400, "Send weekly sales as a list.")
    clean = []
    for l in logs:
        if isinstance(l, dict) and isinstance(l.get("week"), str) and isinstance(l.get("sold"), (int, float)):
            clean.append({"week": l["week"][:10], "sold": l["sold"]})
    nums = decision.clean_inputs({"price": body.get("price"), "cost": body.get("cost")})
    fc = forecast(c, data.snapshot(), data.concepts(), as_of)
    life, wave = _life_and_wave(c, fc, as_of)
    r = decision.review(fc, wave, life, clean, nums["price"], nums["cost"])
    return {"as_of": as_of, "concept_id": c["id"], "review": r, "status": fc["status"],
            "status_label": words.status_label(fc["status"]), "agent": {"attempts": []}}


DRINK_WORDS = ("latte", "coffee", "kopi", "teh", "tea", "juice", "drink", "shake", "milo", "bandung")


def _pair_item(profile, concept):
    """Something already on the menu to bundle with: a drink if the new item isn't one."""
    menu = profile.get("menu") or []
    if concept["category"] != "drink":
        for m in menu:
            if any(w in m.lower() for w in DRINK_WORDS):
                return m
    return menu[0] if menu else None


def post_playbook(q, body):
    """Launch offer options (code arithmetic) and a dated content plan (code formats + model hooks)."""
    as_of = _as_of(body.get("as_of"))
    profile = _profile(body)
    c = _concept(body.get("concept_id") or "")
    raw = body.get("inputs") or {}
    nums = decision.clean_inputs(raw)
    capacity = decision._num(raw.get("capacity_per_day"), 1, 100000)
    fc = forecast(c, data.snapshot(), data.concepts(), as_of)
    j = fit.judge(chain(), c, profile)
    when = launch.launch_when(fc, as_of)
    life, wave = _life_and_wave(c, fc, as_of)
    d = decision.decide(fc, j["fit"], when, life, wave, as_of, nums)
    units = nums["units_per_week"]
    offer = offers.plan(nums["price"], nums["cost"], units, capacity, d["verdict"], _pair_item(profile, c))
    rec = offer["recommended"]
    chosen = body.get("offer_type") if body.get("offer_type") in offers.OFFER_TYPES else (rec and rec["type"])
    rec_offer = next((o for o in offer["offers"] if o["type"] == chosen), None)
    offer["chosen"] = rec_offer and rec_offer["type"]
    p = launch.plan(chain(), c, profile, j["fit"], fc, as_of, data.youtube())
    hooks = (p.get("plan") or {}).get("hooks")
    cplan = content.plan(c, when, rec_offer and rec_offer["type"], rec_offer and rec_offer["title"], hooks, as_of)
    return {"as_of": as_of, "concept_id": c["id"], "verdict": d["verdict"], "when": when,
            "offers": offer, "content": cplan,
            "agent": {"attempts": [{"step": "fit", "provider": j["provider"], "attempts": j["attempts"]},
                                   {"step": "launch", "provider": p["provider"], "attempts": p["attempts"]}]}}


def get_lifespan(q, body):
    as_of = _as_of(q.get("as_of"))
    life = lifecycle.lifespan(data.snapshot(), data.concepts(), as_of)
    return dict(_life_public(life), as_of=as_of, rows=life["rows"], agent={"attempts": []})


def get_backtest(q, body):
    snap = data.snapshot_date()
    if not snap:
        raise ApiError(503, "No trend snapshot yet.")
    out = derived("backtest", lambda: backtest.run(data.snapshot(), data.concepts(), snap))
    return dict(out, agent={"attempts": []})


def route(method, path, query=None, body=None):
    """Return (status, payload). Never raises."""
    query = query or {}
    body = body or {}
    path = "/" + path.strip("/")
    try:
        if method == "GET" and path == "/api/meta":
            return 200, get_meta(query, body)
        if method == "GET" and path == "/api/concepts":
            return 200, get_concepts(query, body)
        if method == "GET" and path.startswith("/api/concepts/"):
            return 200, get_concept(unquote(path.split("/", 3)[3]), query, body)
        if method == "POST" and path == "/api/recommend":
            return 200, post_recommend(query, body)
        if method == "POST" and path == "/api/launch":
            return 200, post_launch(query, body)
        if method == "GET" and path == "/api/changes":
            return 200, get_changes(query, body)
        if method == "POST" and path == "/api/plan":
            return 200, post_plan(query, body)
        if method == "POST" and path == "/api/decision":
            return 200, post_decision(query, body)
        if method == "POST" and path == "/api/review":
            return 200, post_review(query, body)
        if method == "POST" and path == "/api/playbook":
            return 200, post_playbook(query, body)
        if method == "GET" and path == "/api/lifespan":
            return 200, get_lifespan(query, body)
        if method == "GET" and path == "/api/backtest":
            return 200, get_backtest(query, body)
        return 404, {"error": "No such endpoint."}
    except ApiError as e:
        return e.status, {"error": str(e)}
    except Exception as e:  # last resort: say what happened, don't leak a stack trace
        print(f"[api] {method} {path} failed: {e!r}")
        return 500, {"error": "Something broke on our side. Try again in a moment."}


def parse_body(raw):
    if not raw:
        return {}
    try:
        b = json.loads(raw)
        return b if isinstance(b, dict) else {}
    except ValueError:
        return {}
