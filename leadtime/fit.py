"""Fit: can this shop make this concept? The model judges; code validates and caches."""
import hashlib
import json
import re
from pathlib import Path

from .concepts import CATEGORIES, EQUIPMENT
from .schema import SchemaError, validate

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache" / "fit"
PRICE_BANDS = ["budget", "mid", "premium"]
MAX_MENU_ITEMS = 30          # a café menu, not a supplier catalogue
MAX_OVERLAPS = 3             # name the closest few, not the whole menu
MIN_OVERLAP_WORD = 4         # offline rule: shared words shorter than this ("tea", "ice") are too generic

PROFILE_SCHEMA = {
    "type": "object",
    "required": ["sells", "equipment", "price_band"],
    "properties": {
        "name": {"type": "string", "maxLength": 60},
        "sells": {"type": "array", "minItems": 1, "items": {"enum": CATEGORIES}},
        "equipment": {"type": "array", "items": {"enum": EQUIPMENT}},
        "price_band": {"enum": PRICE_BANDS},
        "menu": {"type": "array", "maxItems": MAX_MENU_ITEMS, "items": {"type": "string", "maxLength": 60}},
    },
}

FIT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["verdict", "adaptation", "missing_equipment", "reason", "overlaps"],
    "properties": {
        "overlaps": {"type": "array", "maxItems": MAX_OVERLAPS, "items": {"type": "string", "maxLength": 60}},
        "verdict": {"enum": ["make", "adapt", "skip"]},
        "adaptation": {"type": "string", "maxLength": 140},
        "missing_equipment": {"type": "array", "maxItems": len(EQUIPMENT), "items": {"enum": EQUIPMENT}},
        "reason": {"type": "string", "minLength": 10, "maxLength": 220},
    },
}

_DIGIT = re.compile(r"\d")
_URL = re.compile(r"https?://|www\.", re.I)


def normalise_profile(profile):
    validate(profile, PROFILE_SCHEMA)
    menu = []
    for item in profile.get("menu") or []:
        item = " ".join(item.split())
        if item and item.lower() not in {m.lower() for m in menu}:
            menu.append(item)
    return {
        "menu": menu,
        "name": (profile.get("name") or "Your shop").strip()[:60] or "Your shop",
        "sells": sorted(set(profile["sells"])),
        "equipment": sorted(set(profile["equipment"])),
        "price_band": profile["price_band"],
    }


def profile_hash(profile, include_name=False):
    keys = ["sells", "equipment", "price_band", "menu"] + (["name"] if include_name else [])
    canon = json.dumps({k: profile.get(k) for k in keys}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canon.encode()).hexdigest()[:12]


def make_validator(concept, profile):
    """Schema plus the checks code can make on the model's judgement."""
    def check(out):
        validate(out, FIT_SCHEMA)
        for field in ("adaptation", "reason"):
            if _DIGIT.search(out[field]):
                raise SchemaError(f"{field} contains a number")
            if _URL.search(out[field]):
                raise SchemaError(f"{field} contains a link")
        has = set(profile["equipment"])
        if any(e in has for e in out["missing_equipment"]):
            raise SchemaError("claims the shop lacks equipment it has")
        if out["verdict"] == "adapt" and not out["adaptation"].strip():
            raise SchemaError("adapt verdict with no adaptation")
        if out["verdict"] == "make" and out["missing_equipment"]:
            raise SchemaError("make verdict but equipment missing")
        # overlaps must name items that are really on the shop's menu; use the shop's spelling
        menu = {m.lower(): m for m in profile.get("menu", [])}
        fixed = []
        for o in out["overlaps"]:
            if o.strip().lower() not in menu:
                raise SchemaError(f"overlap {o!r} is not on the shop's menu")
            fixed.append(menu[o.strip().lower()])
        out["overlaps"] = list(dict.fromkeys(fixed))
        return out
    return check


SYSTEM = """You judge whether a small Singapore food business can make a food.
Reply with one JSON object and nothing else:
{"verdict": "make" | "adapt" | "skip",
 "adaptation": "short description of the version this shop should make, or empty string",
 "missing_equipment": [items from the allowed list that the original needs and the shop lacks],
 "reason": "one plain-English sentence",
 "overlaps": [items copied exactly from the shop's current menu that customers would see as similar; empty if none]}
Rules:
- "make": the shop can make the original as it is. "adapt": a recognisable version fits this shop with a change. "skip": no sensible version fits.
- missing_equipment may only use these words: %s. Never list something the shop already has.
- overlaps: at most %d, copied word for word from the menu list. Only real look-alikes (same format or same signature flavour).
- No numbers, no dates, no prices, no links, and no claims about popularity or trends. Judge the kitchen only.
- Talk like a friend who cooks: "You'd need a fryer for the original. Try it baked instead."
""" % (", ".join(EQUIPMENT), MAX_OVERLAPS)


def user_prompt(concept, profile):
    return json.dumps({
        "food": {k: concept[k] for k in ("name", "description", "category",
                                         "key_ingredients", "techniques", "equipment")},
        "shop": {"sells": profile["sells"], "equipment": profile["equipment"],
                 "price_band": profile["price_band"], "current_menu": profile.get("menu", [])},
    }, ensure_ascii=False)


# --- Offline rules (no model): equipment arithmetic plus hand-written swaps ---
EQUIPMENT_SWAPS = {
    "fryer": "bake or air-fry it instead of deep-frying",
    "mixer": "whisk by hand in small batches",
    "griddle": "cook it in a heavy pan on low heat",
    "espresso machine": "use strong moka-pot or cold-brew coffee",
    "moulds": "set it in a lined tray and cut it into bars",
    "stovetop": "use a portable induction plate",
    "blender": "whisk it by hand",
    "soft-serve machine": "scoop frozen yogurt instead of piping soft-serve",
}


def offline_overlaps(concept, menu):
    """Menu items sharing a meaningful word with the food's name or key ingredients."""
    words_in = set()
    for text in [concept["name"], *concept["key_ingredients"]]:
        words_in |= {w.strip(".,()").lower() for w in text.split() if len(w) >= MIN_OVERLAP_WORD}
    hits = [m for m in menu if words_in & {w.strip(".,()").lower() for w in m.split()}]
    return hits[:MAX_OVERLAPS]


def offline_fit(ctx):
    out = _offline_fit(ctx)
    out["overlaps"] = offline_overlaps(ctx["concept"], ctx["profile"].get("menu", []))
    return out


def _offline_fit(ctx):
    concept, profile = ctx["concept"], ctx["profile"]
    has = set(profile["equipment"])
    missing = [e for e in concept["equipment"] if e not in has]
    sells_it = concept["category"] in profile["sells"]
    name = concept["name"]

    if not sells_it:
        if "drink" in profile["sells"] and concept["category"] != "drink" and has & {"blender", "espresso machine"}:
            flavour = concept["key_ingredients"][0]
            return {"verdict": "adapt",
                    "adaptation": f"A {name} iced drink built on {flavour}",
                    "missing_equipment": [],
                    "reason": f"You sell drinks, not {concept['category']}, so borrow the flavours instead of the format."}
        return {"verdict": "skip", "adaptation": "", "missing_equipment": missing,
                "reason": f"It's a {concept['category']} item and that isn't what you sell."}

    if not missing:
        return {"verdict": "make", "adaptation": "", "missing_equipment": [],
                "reason": f"You already have what it needs: {', '.join(concept['equipment'])}."}
    if "fridge" in missing or "freezer" in missing:
        return {"verdict": "skip", "adaptation": "", "missing_equipment": missing,
                "reason": "It has to be kept cold and you don't have the space for it."}
    if "oven" in missing:
        base = concept["key_ingredients"][0]
        return {"verdict": "adapt",
                "adaptation": f"Buy in plain {base} from a bakery and do the filling and finishing here",
                "missing_equipment": missing,
                "reason": "You'd need an oven for the original, but the finishing is where the look comes from."}
    swaps = [EQUIPMENT_SWAPS[e] for e in missing if e in EQUIPMENT_SWAPS]
    if len(swaps) < len(missing):
        return {"verdict": "skip", "adaptation": "", "missing_equipment": missing,
                "reason": f"You'd need a {missing[0]} and there's no good way around it."}
    adaptation = "; ".join(swaps)
    return {"verdict": "adapt", "adaptation": adaptation[0].upper() + adaptation[1:],
            "missing_equipment": missing,
            "reason": f"You'd need a {' and a '.join(missing)} for the original, but a close version works without."}


# --- Cache -------------------------------------------------------------------
_memory = {}


def _cache_path(concept_id, phash):
    return CACHE_DIR / f"{concept_id}__{phash}.json"


def judge(chain, concept, profile):
    """Return {"fit": {...} | None, "provider": str|None, "attempts": [...], "cached": bool}."""
    phash = profile_hash(profile)
    key = (concept["id"], phash)
    if key in _memory:
        return dict(_memory[key], cached=True)
    path = _cache_path(*key)
    if path.exists():
        hit = json.loads(path.read_text(encoding="utf-8"))
        try:
            make_validator(concept, profile)(hit["fit"])  # cached output still must pass today's rules
            _memory[key] = hit
            return dict(hit, cached=True)
        except SchemaError:
            pass

    fit, provider, attempts = chain.run(
        "fit", SYSTEM, user_prompt(concept, profile), make_validator(concept, profile),
        context={"concept": concept, "profile": profile})
    result = {"fit": fit, "provider": provider, "attempts": attempts}
    if fit and provider != "offline":   # offline rules are instant and deterministic; no need to store
        _memory[key] = result
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass  # read-only filesystem on Vercel: memory cache only
    return dict(result, cached=False)
