"""Launch offers, priced against the shop's own numbers. Pure arithmetic.

Every offer answers the same three questions in plain words:
what it costs you, what you make on each one sold, and how much more you'd
need to sell (or how many people need to come back) to come out even.
"""
import math

GIVEAWAY_DEFAULT = 50        # free portions on launch day: enough to make a visible line, small enough to afford
DISCOUNT_DEFAULT = 0.2       # 20% off launch week: noticeable without training customers to wait for sales
LOYALTY_DEFAULT = 5          # buy 5, 6th free: short enough that people finish the card during a trend
DROP_DEFAULT = 40            # limited daily drop: sells out by mid-afternoon in a small shop
STRETCH_LIFT = 1.5           # needing 1.5x normal sales just to break even is a stretch for a small shop
DAYS_OPEN = 6                # most small F&B shops open six days a week
BUNDLE_SHARE = 0.1           # bundle saving ~10% of this item's price...
BUNDLE_MIN_OFF = 0.5         # ...but at least 50 cents, or nobody notices

OFFER_TYPES = ["free_first", "launch_discount", "second_half", "loyalty", "daily_drop", "bundle"]


def free_first(price, cost, units, n=GIVEAWAY_DEFAULT):
    margin = price - cost
    spend = round(n * cost, 2)
    payback = math.ceil(round(spend / margin, 6)) if margin > 0 else None   # round first: 18 / 0.2 is 90.000...01
    if payback is None:
        plain = "At this price you lose money on every sale, so a giveaway can't pay back."
    elif payback <= n:
        plain = (f"Costs you about ${spend:.0f} in ingredients. You make it back after {payback} full-price sales, "
                 f"so roughly 1 in {max(1, round(n / payback))} people who got one free need to come back and buy one.")
    else:
        plain = (f"Costs you about ${spend:.0f} in ingredients and takes {payback} full-price sales to make back, "
                 f"more than the {n} you gave away. Only worth it for the attention.")
    return {
        "type": "free_first", "title": f"First {n} free on launch day",
        "params": {"n": n},
        "cost": spend, "margin_each": round(margin, 2), "lift_needed": None,
        "payback_sales": payback,
        "plain": plain,
        "why": "The line becomes your content: film it. Best when you're early and want people talking.",
    }


def launch_discount(price, cost, units, d=DISCOUNT_DEFAULT):
    margin = price - cost
    offer_margin = price * (1 - d) - cost
    lift = (margin / offer_margin) if offer_margin > 0 else None
    spend = round(units * price * d, 2) if units else None
    return {
        "type": "launch_discount", "title": f"{round(d * 100)}% off launch week",
        "params": {"discount": d},
        "cost": spend, "margin_each": round(offer_margin, 2), "lift_needed": round(lift, 2) if lift else None,
        "payback_sales": None,
        "plain": (f"You make ${offer_margin:.2f} on each instead of ${margin:.2f}, so you need to sell "
                  f"{lift:.1f}x your normal week to make the same profit." if lift else
                  "The discount wipes out your margin. Pick a smaller one or a different offer."),
        "why": "Simple and easy to understand. Good when you're late and need a reason to choose you over the shop next door.",
    }


def second_half(price, cost, units):
    margin = price - cost
    pair_margin = 1.5 * price - 2 * cost
    each = pair_margin / 2
    lift = (margin / each) if each > 0 else None
    return {
        "type": "second_half", "title": "Second one half price",
        "params": {},
        "cost": None, "margin_each": round(each, 2), "lift_needed": round(lift, 2) if lift else None,
        "payback_sales": None,
        "plain": (f"Each pair makes you ${pair_margin:.2f} (${each:.2f} each). It pays if it gets people to buy two "
                  f"and come in pairs; you need {lift:.1f}x your normal sales to break even." if lift else
                  "Half price on the second one loses money at this cost."),
        "why": "Brings people in twos, and two people filming is twice the posts.",
    }


def loyalty(price, cost, units, n=LOYALTY_DEFAULT):
    margin = price - cost
    per_unit = (n * price - (n + 1) * cost) / (n + 1)
    lift = (margin / per_unit) if per_unit > 0 else None
    return {
        "type": "loyalty", "title": f"Buy {n}, get the {n + 1}th free",
        "params": {"n": n},
        "cost": None, "margin_each": round(per_unit, 2), "lift_needed": round(lift, 2) if lift else None,
        "payback_sales": None,
        "plain": (f"Works out to ${per_unit:.2f} per item once the free one is counted. Only regulars finish the card, "
                  f"so it costs little and keeps people coming back after the trend cools." if lift else
                  "The free item costs more than you make on the card."),
        "why": "Turns trend visitors into regulars, which matters when most trends last a couple of months.",
    }


def daily_drop(price, cost, units, k=DROP_DEFAULT, capacity=None):
    margin = price - cost
    k = min(k, capacity) if capacity else k
    weekly = k * DAYS_OPEN
    capped = bool(units and units > weekly)
    expected = min(units, weekly) if units else weekly
    return {
        "type": "daily_drop", "title": f"Only {k} a day",
        "params": {"per_day": k},
        "cost": 0, "margin_each": round(margin, 2), "lift_needed": 1.0, "payback_sales": None,
        "weekly_profit": round(expected * margin, 2),
        "plain": (f"Costs nothing. Selling out every day makes {k} a day feel scarce and gives you a 'sold out' post. "
                  + (f"Caps you at ${weekly * margin:.0f} a week, so you'd turn away about {round(units - weekly)} sales a week."
                     if capped else
                     f"At full margin that's about ${expected * margin:.0f} a week"
                     + (" at your expected sales. Set the cap near what you'd sell anyway, so it actually sells out." if units else "."))),
        "why": "Full margin, built-in urgency, and it protects a small kitchen from being swamped.",
    }


def bundle(price, cost, units, pair_item=None):
    margin = price - cost
    off = round(max(BUNDLE_MIN_OFF, BUNDLE_SHARE * price), 1)
    each = margin - off / 2
    lift = (margin / each) if each > 0 else None
    with_what = pair_item or "a drink"
    return {
        "type": "bundle", "title": f"Pair it with {with_what}",
        "params": {"with": with_what, "off": off},
        "cost": None, "margin_each": round(each, 2), "lift_needed": round(lift, 2) if lift else None,
        "payback_sales": None,
        "plain": (f"${off:.2f} off when bought with {with_what}. You give up a little on this item but sell something "
                  f"you already make, so the basket gets bigger."),
        "why": "Uses the new item to sell what's already on your menu.",
    }


def plan(price, cost, units, capacity=None, verdict=None, pair_item=None):
    """All offers with their maths, plus one recommendation for this moment."""
    if price is None or cost is None:
        return {"ready": False, "offers": [], "recommended": None,
                "message": "Add your price and cost per portion to see what each offer would cost you."}
    offers = [
        free_first(price, cost, units),
        launch_discount(price, cost, units),
        second_half(price, cost, units),
        loyalty(price, cost, units),
        daily_drop(price, cost, units, capacity=capacity),
        bundle(price, cost, units, pair_item),
    ]
    for o in offers:
        o["stretch"] = bool(o["lift_needed"] and o["lift_needed"] > STRETCH_LIFT) or o["margin_each"] <= 0
    rec = recommend(offers, verdict, price - cost)
    return {"ready": True, "offers": offers, "recommended": rec}


def recommend(offers, verdict, margin):
    """Early: buy attention (giveaway). Late: compete on value. Waiting: protect margin. Never pick a stretch."""
    by = {o["type"]: o for o in offers}
    if margin <= 0:
        return None
    if verdict == "go":
        order = ["free_first", "daily_drop", "second_half"]
        why = "You're early, so the goal is attention: a free launch-day line is the content."
    elif verdict == "go_late":
        order = ["second_half", "bundle", "launch_discount"]
        why = "Others already sell it, so give people a reason to pick you."
    else:
        order = ["daily_drop", "loyalty", "bundle"]
        why = "Keep it low-risk until the timing is clearer."
    for t in order:
        if not by[t]["stretch"]:
            return {"type": t, "why": why}
    return {"type": "daily_drop", "why": "Every discount is a stretch at this margin, so sell at full price and make it scarce."}
