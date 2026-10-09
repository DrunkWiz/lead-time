"""Launch plan: when (code), what to make and how to announce it (model), links (code)."""
import json
import re
from pathlib import Path

from . import words
from .config import LAUNCH_LEAD_WEEKS
from .fit import EQUIPMENT_SWAPS, profile_hash
from .forecast import add_weeks
from .schema import SchemaError, validate
from .series import parse_date

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache" / "launch"
SOURCE_LINKS = 3
CAPTION_MAX = 500   # Instagram allows far more; 500 keeps it readable on a card
DISCLAIMER = "A starting point. Test a batch before you sell it."


# --- When (code only) ----------------------------------------------------------
def launch_when(fc, as_of):
    s = fc["status"]
    as_of = parse_date(as_of)
    if s in ("already_here", "peaked_here"):
        return {"kind": "following", "date": None, "text": "You'd be following, not leading."}
    if s == "not_travelling":
        return {"kind": "none", "date": None, "text": "It isn't heading here, so there's no launch date."}
    if s == "arriving_now":
        return {"kind": "now", "date": as_of.isoformat(),
                "text": "Launch this week. Others will be starting too."}
    win = fc.get("window")
    if not win:
        return {"kind": "no_window", "date": None,
                "text": "Not enough history to give a launch date. Keep an eye on it."}
    if win.get("wide"):
        return {"kind": "watch", "date": None,
                "text": "No firm date. Watch it, and launch the week Singapore searches start to move."}
    d = add_weeks(win["start"], -LAUNCH_LEAD_WEEKS)
    if d <= as_of:
        return {"kind": "this_week", "date": as_of.isoformat(),
                "text": "Launch this week. Searches here could start any time."}
    return {"kind": "date", "date": d.isoformat(),
            "text": (f"Launch by {words.day_month(d)}. That gives you about "
                     f"{LAUNCH_LEAD_WEEKS} weeks before most shops catch on.")}


def has_plan(when):
    return when["kind"] in ("date", "this_week", "now", "watch")


# --- What to make + how to announce (model, validated) -------------------------
_S = lambda n: {"type": "string", "minLength": 2, "maxLength": n}  # noqa: E731
PLAN_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["method", "swaps", "hooks", "caption", "offer"],
    "properties": {
        "method": {"type": "array", "minItems": 1, "maxItems": 6, "items": {
            "type": "object", "additionalProperties": False, "required": ["component", "steps"],
            "properties": {"component": _S(60),
                           "steps": {"type": "array", "minItems": 1, "maxItems": 5, "items": _S(160)}}}},
        "swaps": {"type": "array", "maxItems": 4, "items": {
            "type": "object", "additionalProperties": False, "required": ["original", "use", "why"],
            "properties": {"original": _S(60), "use": _S(80), "why": _S(120)}}},
        "hooks": {"type": "array", "minItems": 3, "maxItems": 3, "items": _S(140)},
        "caption": _S(CAPTION_MAX),
        "offer": _S(140),
    },
}

MONTH = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
DATE_PATTERNS = [
    re.compile(r"\b\d{4}-\d{1,2}-\d{1,2}\b"),                 # 2026-11-02
    re.compile(r"\b\d{1,2}[/.]\d{1,2}([/.]\d{2,4})?\b"),      # 2/11, 02.11.2026
    re.compile(r"\b\d{1,2}(st|nd|rd|th)?\s+" + MONTH + r"\b", re.I),   # 2 Nov
    re.compile(r"\b" + MONTH + r"\s+\d{1,2}(st|nd|rd|th)?\b", re.I),   # Nov 2
    re.compile(r"\b(19|20)\d{2}\b"),                          # any year
]
URL = re.compile(r"https?://|www\.|\.com\b", re.I)
# Popularity claims are code's job (from data), never the model's. These words make one.
HYPE = re.compile(r"\b(viral|hottest|trending|everyone|obsessed|most popular|best[- ]?selling|number one|"
                  r"craze|sensation|taking over|blowing up)\b|#1\b", re.I)
GRAMS = re.compile(r"\b\d+(\.\d+)?\s?(g|gram|grams|kg|ml|l|oz|cups?|tbsp|tsp)\b", re.I)


def _strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, list):
        for v in x:
            yield from _strings(v)
    elif isinstance(x, dict):
        for v in x.values():
            yield from _strings(v)


def validate_plan(out):
    validate(out, PLAN_SCHEMA)
    for s in _strings(out):
        if URL.search(s):
            raise SchemaError(f"contains a link: {s[:60]!r}")
        for p in DATE_PATTERNS:
            if p.search(s):
                raise SchemaError(f"contains a date: {s[:60]!r}")
        if GRAMS.search(s):
            raise SchemaError(f"contains a quantity: {s[:60]!r}")
        m = HYPE.search(s)
        if m:
            raise SchemaError(f"makes a popularity claim ({m.group(0)!r}); describe the food, not its popularity")
    return out


SYSTEM = """You write a launch plan for a small Singapore food business adding a new item.
Reply with one JSON object and nothing else:
{"method": [{"component": "...", "steps": ["...", "..."]}],
 "swaps": [{"original": "...", "use": "...", "why": "..."}],
 "hooks": ["...", "...", "..."],
 "caption": "...",
 "offer": "..."}
Limits (answers over them are thrown away):
- method: 1 to 6 components, each with 1 to 5 short steps (under 160 characters each).
- swaps: at most 4. hooks: exactly 3, each under 140 characters. caption under %d, offer under 140.
Rules:
- method: an outline, not a recipe. Components and techniques only. No quantities, weights, temperatures or times.
- Make the version described in "version_to_make" with the shop's equipment. Add swaps for missing equipment or hard-to-find ingredients.
- hooks: three short-video opening lines, under fifteen words each. caption: one Instagram caption. offer: one launch offer that suits the price band.
- You may refer to the trend facts given, in words. Never write a date, a year, a link, or a new claim about popularity.
- Don't use hype words: viral, hottest, trending, everyone, obsessed, most popular, craze, sensation. Describe the food instead.
- Sound like a friendly local shop, not an ad agency. No "unlock", no "viral", no hashtags spam (two hashtags max).
""" % CAPTION_MAX


def user_prompt(concept, profile, fit, facts):
    return json.dumps({
        "food": {k: concept[k] for k in ("name", "description", "key_ingredients", "techniques", "equipment")},
        "shop": profile,
        "version_to_make": (fit or {}).get("adaptation") or "the original",
        "missing_equipment": (fit or {}).get("missing_equipment", []),
        "trend_facts": facts,
    }, ensure_ascii=False)


# Offline rules: templates filled from the concept record. Not a model.
TECHNIQUE_STEPS = {
    "tempering": "Temper the chocolate so the shell snaps and shines",
    "toasting": "Toast until golden and fragrant, then cool fully so it stays crisp",
    "melting": "Melt gently over low heat and stir until smooth",
    "shaping": "Shape while still warm and pliable",
    "hard-crack sugar": "Cook the syrup to hard crack, dip quickly, and let it set on a cold tray",
    "laminating": "Laminate the dough with cold butter, keeping it chilled between folds",
    "proofing": "Proof until puffy and light",
    "baking": "Bake until deep golden; underbaked layers turn soggy once filled",
    "deep frying": "Fry in small batches at a steady heat and drain well",
    "syrup soaking": "Soak while warm so the syrup soaks all the way through",
    "whipping": "Whip cold cream to firm peaks just before assembling",
    "piping": "Pipe the filling generously so it shows when cut",
    "brewing": "Brew strong so the coffee holds up under the cream",
    "glazing": "Glaze once cool so it sets glossy",
    "assembling": "Assemble cold, chill, then cut with a hot knife for a clean cross-section",
    "meringue": "Whip egg whites to soft, stable peaks and fold in gently",
    "low-heat cooking": "Cook low and slow under a lid so they rise without burning",
    "pressing": "Press firmly and evenly so it cooks flat and crisp",
    "caramelising": "Caramelise the sugar until deep amber, watching closely so it doesn't burn",
    "churning": "Freeze the base until thick and scoopable, stirring so ice crystals stay small",
}
TECHNIQUE_NEEDS = {   # skip a technique in the outline when the shop lacks its equipment
    "deep frying": "fryer", "baking": "oven", "proofing": "oven", "laminating": "oven",
    "low-heat cooking": "griddle",
}
INGREDIENT_SWAPS = {
    "kataifi": ("toasted crushed feuilletine or cornflakes", "Easier to find here, same crunch"),
    "pistachio cream": ("pistachio paste blended with white chocolate", "Cheaper than ready-made cream"),
    "robusta coffee": ("local kopi powder", "Already strong and easy to buy"),
    "croissant dough": ("frozen croissant dough", "Saves a day of laminating"),
    "brioche dough": ("bakery milk buns", "Close enough when filled with cream"),
    "milk bread": ("soft white sandwich bread", "Soft, cheap and on every shelf"),
}
OFFERS = {
    "budget": "Launch weekend: buy one, get the second at half price.",
    "mid": "Launch week: free drink upgrade with every {name}.",
    "premium": "Launch week tasting set: {name} with a drink, limited daily.",
}


def offline_plan(ctx):
    concept, profile, fit, facts = ctx["concept"], ctx["profile"], ctx["fit"], ctx["facts"]
    name, shop = concept["name"], profile["name"]
    method = []
    if fit and fit.get("adaptation"):
        method.append({"component": "Your version", "steps": [fit["adaptation"]]})
    missing = set((fit or {}).get("missing_equipment", []))
    for t in [t for t in concept["techniques"] if TECHNIQUE_NEEDS.get(t) not in missing][:4]:
        method.append({"component": t[0].upper() + t[1:],
                       "steps": [TECHNIQUE_STEPS.get(t, f"Practise {t} on a small batch first")]})
    swaps = []
    for e in (fit or {}).get("missing_equipment", []):
        if e in EQUIPMENT_SWAPS:
            swaps.append({"original": e, "use": EQUIPMENT_SWAPS[e], "why": "You don't have one"})
    for ing in concept["key_ingredients"]:
        if ing in INGREDIENT_SWAPS and len(swaps) < 4:
            use, why = INGREDIENT_SWAPS[ing]
            swaps.append({"original": ing, "use": use, "why": why})
    origin = facts.get("origin")
    nearby = origin in (None, "Malaysia")   # "no flight needed" only works for somewhere far away
    first_hook = (f"{name}, made fresh here at {shop}." if nearby
                  else f"You don't need a flight to {origin} for {name} anymore.")
    return {
        "method": method or [{"component": name, "steps": ["Make a small test batch first"]}],
        "swaps": swaps,
        "hooks": [
            first_hook,
            f"Making {name} for the first time at {shop}. Did it work?",
            f"First batch of {name} out of our kitchen. Worth the wait?",
        ],
        "caption": f"{name} is here. Made in small batches at {shop}, so come early. Tell us what you think!",
        "offer": OFFERS[profile["price_band"]].format(name=name),
    }


# --- Source links (code only) --------------------------------------------------
def source_links(youtube, concept_id):
    vids = (youtube or {}).get("concepts", {}).get(concept_id, [])
    vids = sorted(vids, key=lambda v: v.get("views", 0), reverse=True)[:SOURCE_LINKS]
    return [{"title": v["title"], "channel": v["channel"], "views": v.get("views"),
             "url": f"https://www.youtube.com/watch?v={v['video_id']}"} for v in vids]


_memory = {}


def plan(chain, concept, profile, fit, fc, as_of, youtube):
    when = launch_when(fc, as_of)
    out = {"when": when, "plan": None, "provider": None, "attempts": [],
           "disclaimer": DISCLAIMER, "links": source_links(youtube, concept["id"])}
    if not has_plan(when):
        return out
    facts = {"origin": fc.get("origin_name"),
             "trend": words.why(fc),
             "launch": {"date": "in a few weeks", "watch": "as soon as Singapore searches start to move"}.get(
                 when["kind"], "this week")}
    key = (concept["id"], profile_hash(profile, include_name=True), when["kind"])
    path = CACHE_DIR / f"{key[0]}__{key[1]}__{key[2]}.json"
    hit = _memory.get(key)
    if not hit and path.exists():
        try:
            hit = json.loads(path.read_text(encoding="utf-8"))
            validate_plan(hit["plan"])
        except (SchemaError, KeyError, ValueError):
            hit = None
    if hit:
        _memory[key] = hit
        return dict(out, **hit, cached=True)

    result, provider, attempts = chain.run(
        "launch", SYSTEM, user_prompt(concept, profile, fit, facts), validate_plan,
        context={"concept": concept, "profile": profile, "fit": fit, "facts": facts})
    stored = {"plan": result, "provider": provider, "attempts": attempts}
    if result and provider != "offline":
        _memory[key] = stored
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(stored, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
    return dict(out, **stored, cached=False)
