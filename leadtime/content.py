"""Content plan: what to film, when to post, around the launch date. Pure code.

Formats are picked from what the food actually is (its techniques,
ingredients and description), because a food that cracks wants a sound-led
video and a food with a filling wants a cross-section. Dates come from the
launch date code already computed.
"""
import datetime as dt

from . import words
from .series import parse_date

# Each format: the words that suggest it, and a phone-friendly shot list.
FORMATS = {
    "cross_section": {
        "name": "The cut",
        "triggers": ["cream", "custard", "filling", "filled", "paste", "stuffed", "kataifi", "sando", "layer"],
        "shots": [("Whole piece on the counter, nothing moving", 2),
                  ("Slow cut straight down the middle", 4),
                  ("Pull the halves apart towards the camera", 3),
                  ("Close-up of the inside", 2)],
        "tip": "Use your sharpest knife and wipe it between takes. A clean cut is the whole video.",
    },
    "crunch": {
        "name": "The crunch",
        "triggers": ["hard-crack", "tempering", "caramelising", "toasting", "crisp", "glassy", "shatter", "crunch", "fried"],
        "shots": [("Tap it with a spoon right next to the phone", 2),
                  ("Break or bite it close to the mic", 3),
                  ("Crumbs falling in slow motion", 2)],
        "tip": "Film somewhere quiet. The sound is the hook, so turn off the music in the shop for ten seconds.",
    },
    "pull": {
        "name": "The pull",
        "triggers": ["marshmallow", "mochi", "chewy", "glutinous", "cheese", "stretch"],
        "shots": [("Hold it up against a plain background", 2),
                  ("Pull apart slowly with both hands", 4),
                  ("Let it stretch, then snap back", 2)],
        "tip": "Pull slower than feels natural. Speed it up in the edit if you need to.",
    },
    "pour": {
        "name": "The pour",
        "triggers": ["foam", "syrup", "glaze", "condensed milk", "espresso", "coffee", "milk", "latte"],
        "shots": [("Empty clear cup with ice, from the side", 2),
                  ("Pour from above in one take", 4),
                  ("Top layer going on, then a slow stir", 3)],
        "tip": "Clear cups and side light. Do it in one take and use the best one.",
    },
    "build": {
        "name": "The build",
        "triggers": ["assembling", "piping", "shaping", "pressing", "laminating", "whipping", "topping", "piled"],
        "shots": [("Hands only: the first step", 2),
                  ("Two or three quick cuts of the making", 4),
                  ("Final topping going on, top-down", 3)],
        "tip": "Hands-only process clips need no talking and no face, and you can film them during prep.",
    },
}
ALWAYS = {
    "first_bite": {"name": "First bite", "shots": [("Customer takes the first bite (ask first)", 3),
                                                    ("Their reaction, no words needed", 2)],
                   "tip": "Ask regulars. Real reactions beat staff acting."},
    "counter": {"name": "Counter POV", "shots": [("POV walking up to the counter", 2),
                                                 ("Hand passing it over", 2),
                                                 ("Price and name on the menu board", 2)],
                "tip": "Show the price. People share things they know they can afford."},
    "line": {"name": "The line", "shots": [("Wide shot of the line outside", 3),
                                           ("Handing out the free ones, fast cuts", 4),
                                           ("Counter of how many are left", 2)],
             "tip": "Film the line from across the street at the busiest moment. That clip is your best ad."},
    "sold_out": {"name": "Sold out", "shots": [("Empty tray or display", 2),
                                               ("'Sold out' sign going up", 2)],
                 "tip": "Post it the moment you sell out. It's the most honest proof you can give."},
}
MAX_FORMATS = 2   # one hero format and one backup; more and the plan stops being simple
ANNOUNCE_DAYS = 3  # "launch this week" still needs a few days' notice, so launch day moves this far out


def pick_formats(concept):
    """Formats ranked by how many of their trigger words appear in the concept record."""
    text = " ".join([concept["description"], concept["category"], *concept["techniques"],
                     *concept["key_ingredients"]]).lower()
    scored = []
    for fid, f in FORMATS.items():
        hits = sum(1 for t in f["triggers"] if t in text)
        if hits:
            scored.append((-hits, fid))
    chosen = [fid for _, fid in sorted(scored)][:MAX_FORMATS]
    return chosen or ["build"]


def _shots(fmt):
    return [{"what": what, "seconds": sec} for what, sec in fmt["shots"]]


def _post(day, label, goal, fid, on_screen, launch_date):
    fmt = FORMATS.get(fid) or ALWAYS[fid]
    date = (launch_date + dt.timedelta(days=day)).isoformat() if launch_date else None
    return {"day": day, "date": date, "label": label, "goal": goal, "format": fid, "format_name": fmt["name"],
            "shots": _shots(fmt), "tip": fmt["tip"], "on_screen": on_screen,
            "length_seconds": sum(sec for _, sec in fmt["shots"])}


def plan(concept, when, offer_type=None, offer_title=None, hooks=None, as_of=None):
    """Five posts around launch day. Dates only when code has a launch date.
    Posts that would fall before as_of are dropped (there's no time for them)."""
    name = concept["name"]
    launch_date = parse_date(when["date"]) if when.get("date") else None
    moved = False
    if launch_date and as_of and launch_date < parse_date(as_of) + dt.timedelta(days=ANNOUNCE_DAYS):
        launch_date = parse_date(as_of) + dt.timedelta(days=ANNOUNCE_DAYS)
        moved = True
    formats = pick_formats(concept)
    hero = formats[0]
    offer_line = f" {offer_title}." if offer_title else ""

    posts = [
        _post(-7, "Tease", "Make people curious without showing it", "build",
              "Something new is coming. Guess what it is?", launch_date),
        _post(-3, "Announce", "Show it properly and say when", hero,
              f"{name}. Launching this week.{offer_line}", launch_date),
        _post(0, "Launch day", "Get people in the door today",
              "line" if offer_type == "free_first" else hero,
              (hooks or [f"{name} is here."])[0], launch_date),
        _post(2, "Reactions", "Let customers sell it for you", "first_bite",
              f"First time trying {name}.", launch_date),
        _post(7, "Follow-up", "Keep it going after the first rush",
              "sold_out" if offer_type == "daily_drop" else "counter",
              f"Still making {name} every day." if offer_type != "daily_drop" else "Sold out again. Back tomorrow.",
              launch_date),
    ]
    skipped = []
    if launch_date and as_of:
        today = parse_date(as_of)
        skipped = [p["label"] for p in posts if parse_date(p["date"]) < today]
        posts = [p for p in posts if parse_date(p["date"]) >= today]
    if not launch_date:
        when_text = "No launch date yet, so posts are counted from whenever you launch."
    elif moved:
        when_text = (f"Launch day {words.day_month(launch_date)}: {ANNOUNCE_DAYS} days to announce it first."
                     + (f" No time for the {' or '.join(skipped).lower()}, so start with the announcement." if skipped else ""))
    else:
        when_text = f"Built around launch day, {words.day_month(launch_date)}."
    return {
        "formats": [{"id": f, "name": FORMATS[f]["name"]} for f in formats],
        "posts": posts,
        "launch_date": launch_date.isoformat() if launch_date else None,
        "when_text": when_text,
    }
