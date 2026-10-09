"""Should this shop do it, and later: keep, push or drop it? Pure code.

Every number here is computed from the snapshot or typed in by the shop
(price, cost, units). The model's only input is the kitchen verdict.
"""
import statistics

from . import words
from .config import (MIN_REVIEW_WEEKS, MIN_SELLING_WEEKS, SALES_DROP, SALES_RISE, SETUP_WEEKS,
                     STOCK_SAFETY_WEEKS)
from .forecast import add_weeks
from .lifecycle import phase
from .series import parse_date

VERDICT_LABEL = {"go": "Go", "go_late": "Go, but you're late", "wait": "Wait and watch", "skip": "Skip"}
REVIEW_LABEL = {"push": "Push it", "keep": "Keep, buy weekly", "rethink": "Rethink it",
                "drop": "Wind it down", "too_early": "Too early to tell"}


def _num(x, lo=0.0, hi=1e6):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if lo <= x <= hi else None


def clean_inputs(raw):
    raw = raw or {}
    return {"price": _num(raw.get("price"), 0.01, 1000), "cost": _num(raw.get("cost"), 0, 1000),
            "units_per_week": _num(raw.get("units_per_week"), 1, 100000)}


def decide(fc, fit, when, life, wave, as_of, inputs):
    """The Go / Wait / Skip card for one food."""
    as_of = parse_date(as_of)
    typical = life.get("typical") if life else None
    reasons = []
    verdict = None
    s = fc["status"]

    # timing
    if s == "arriving_now":
        reasons.append({"ok": True, "text": "Timing: it's arriving in Singapore now."})
        verdict = "go"
    elif s == "rising_abroad":
        if when["kind"] in ("date", "this_week"):
            reasons.append({"ok": True, "text": f"Timing: {when['text']}"})
            verdict = "go"
        else:
            reasons.append({"ok": None, "text": "Timing: rising abroad, but there's no reliable date for Singapore yet."})
            verdict = "wait"
    elif s == "already_here":
        elapsed = wave["elapsed"] if wave else 0
        if typical:
            left = typical["low"] - elapsed
            if wave and wave.get("steady") and not wave["climbing"]:
                reasons.append({"ok": None, "text": f"Timing: popular here for {elapsed} weeks, and searched every week "
                                                    f"rather than in spikes. That's how the long runs here started, "
                                                    f"while most trends fade within {typical['high']} weeks."})
                verdict = "go_late"
            elif wave and wave["climbing"]:
                big = (life.get("longest") or [{}])[0]
                is_long = big.get("length", 0) >= 2 * typical["high"]   # only cite a genuinely long run
                example = f" (like {big['name']}, which ran {big['length']} weeks)" if is_long else ""
                reasons.append({"ok": None, "text": f"Timing: popular here for {elapsed} weeks and still climbing. Most runs "
                                                    f"end within {typical['high']} weeks, but the ones still climbing can be "
                                                    f"the long ones{example}."})
                verdict = "go_late"
            elif left >= SETUP_WEEKS + MIN_SELLING_WEEKS:
                reasons.append({"ok": None, "text": f"Timing: popular here for {elapsed} weeks already. Short runs last "
                                                    f"about {typical['low']} weeks, so there's still time if you move fast."})
                verdict = "go_late"
            else:
                reasons.append({"ok": False, "text": f"Timing: popular here for {elapsed} weeks already. Most runs fade "
                                                     f"after {typical['low']} to {typical['high']} weeks, likely before you're set up."})
                verdict = "skip"
        else:
            reasons.append({"ok": None, "text": "Timing: already popular here, and we don't have enough history to say how long it lasts."})
            verdict = "wait"
    elif s == "peaked_here":
        reasons.append({"ok": False, "text": "Timing: it has peaked here and is cooling. You'd be stocking a fading item."})
        verdict = "skip"
    else:
        reasons.append({"ok": False, "text": "Timing: it isn't heading for Singapore."})
        verdict = "skip"

    # kitchen (the model's judgement, already validated)
    if not fit:
        reasons.append({"ok": None, "text": "Kitchen: we couldn't check this one. Judge it yourself."})
    elif fit["verdict"] == "make":
        reasons.append({"ok": True, "text": "Kitchen: you can make the original."})
    elif fit["verdict"] == "adapt":
        reasons.append({"ok": True, "text": f"Kitchen: make your own version ({fit['adaptation'].rstrip('.')})."})
    else:
        reasons.append({"ok": False, "text": f"Kitchen: {fit['reason']}"})
        verdict = "skip"
    if fit and fit.get("overlaps"):
        them = "it" if len(fit["overlaps"]) == 1 else "them"
        reasons.append({"ok": None, "text": f"Menu: close to your {' and '.join(fit['overlaps'])}. "
                                            f"It could replace {them} or sit beside {them}."})

    # run length
    run = None
    if typical:
        started = s in ("already_here", "peaked_here")
        elapsed = wave["elapsed"] if (wave and started) else 0
        run = {"low": typical["low"], "high": typical["high"], "median": typical["median"],
               "elapsed": elapsed if started else None,
               "remaining_low": max(0, typical["low"] - elapsed), "remaining_high": max(0, typical["high"] - elapsed),
               "phase": phase(elapsed, typical) if started else None}
        reasons.append({"ok": None, "text": f"Run: most food trends here have lasted {typical['low']} to "
                                            f"{typical['high']} weeks once they land."})

    # money (shop's own numbers)
    money = None
    p, c, u = inputs["price"], inputs["cost"], inputs["units_per_week"]
    if p is not None and c is not None:
        margin = round(p - c, 2)
        money = {"margin": margin, "units_per_week": u, "profit_low": None, "profit_high": None}
        if margin <= 0:
            reasons.append({"ok": False, "text": "Money: at that price you'd lose money on every one."})
            verdict = "skip"
        else:
            reasons.append({"ok": True, "text": f"Money: about ${margin:.2f} margin on each."})
            if u and run and verdict != "skip":
                money["profit_low"] = round(u * margin * run["remaining_low"])
                money["profit_high"] = round(u * margin * run["remaining_high"])

    # stock plan
    stock = None
    if typical and verdict in ("go", "go_late"):
        selling_from = parse_date(when["date"]) if when.get("date") else as_of
        weeks_left = run["remaining_low"]
        bulk_until = add_weeks(selling_from, weeks_left - STOCK_SAFETY_WEEKS)
        if bulk_until <= selling_from:
            stock = {"bulk_until": None,
                     "text": "Buy week by week from the start. Runs like this are short, so don't bulk order."}
        else:
            stock = {"bulk_until": bulk_until.isoformat(),
                     "text": (f"Bulk order until about {words.day_month(bulk_until)}, then buy week by week. "
                              f"That's {STOCK_SAFETY_WEEKS} weeks before the shortest typical runs end.")}

    headline = {
        "go": "Worth doing. Get ready now.",
        "go_late": "Still worth it if you can launch within a couple of weeks.",
        "wait": "Watch it. Prepare, but don't buy stock yet.",
        "skip": "Give this one a miss.",
    }[verdict]
    return {"verdict": verdict, "label": VERDICT_LABEL[verdict], "headline": headline,
            "reasons": reasons, "run": run, "money": money, "stock": stock}


def review(fc, wave, life, logs, price=None, cost=None):
    """Keep / push / drop for a launched item, from its weekly sales and Singapore's curve."""
    logs = sorted((l for l in logs if isinstance(l.get("sold"), (int, float)) and l["sold"] >= 0),
                  key=lambda l: l["week"])
    sold = [l["sold"] for l in logs]
    total = sum(sold)
    metrics = {"weeks": len(sold), "total": total,
               "revenue": round(total * price, 2) if price else None,
               "profit": round(total * (price - cost), 2) if price is not None and cost is not None else None}
    typical = (life or {}).get("typical")
    ph = phase(wave["elapsed"], typical) if (wave and typical) else None
    sg_cooling = fc["status"] in ("peaked_here", "not_travelling") or ph in ("late", "overtime")
    sg_text = {"peaked_here": "Singapore searches have peaked and are cooling",
               "not_travelling": "it never really took off in Singapore"}.get(
        fc["status"], f"Singapore is in the {ph} part of a typical run" if ph else "Singapore searches are still up")

    if len(sold) < MIN_REVIEW_WEEKS:
        v, text = "too_early", f"Log at least {MIN_REVIEW_WEEKS} weeks of sales and we'll give you a call."
    else:
        pairs = [statistics.mean(sold[i:i + 2]) for i in range(len(sold) - 1)]
        best, recent = max(pairs), pairs[-1]
        falling = recent < SALES_DROP * best
        rising = sold[-1] > sold[-2] * SALES_RISE
        metrics.update({"recent_avg": round(recent, 1), "best_avg": round(best, 1)})
        if falling and sg_cooling:
            v = "drop"
            text = (f"Sales are down to {round(100 * recent / best)}% of your best and {sg_text}. "
                    "Stop reordering, run a last-chance promo and use up stock.")
        elif falling:
            v = "rethink"
            text = (f"Sales are down to {round(100 * recent / best)}% of your best, but {sg_text}. "
                    "The trend isn't the problem: check taste, price, and whether customers can see it.")
        elif sg_cooling:
            v = "keep"
            text = f"Sales are holding, but {sg_text}. Keep it while it sells and buy week by week."
        else:
            v = "push"
            text = (f"Sales are {'climbing' if rising else 'holding'} and {sg_text}. "
                    "Feature it, try a second flavour, and keep stock up.")
    return {"verdict": v, "label": REVIEW_LABEL[v], "text": text, "metrics": metrics, "phase": ph}
