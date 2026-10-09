"""Every trend sentence the user reads. Code writes these from computed facts;
the model never produces a date, a number or a popularity claim."""
from .series import parse_date

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]
WEEKS_PER_MONTH = 4.35
SAY_MONTHS_ABOVE_WEEKS = 12   # past ~3 months, weeks read as false precision


def month_year(d):
    d = parse_date(d)
    return f"{MONTHS_LONG[d.month - 1]} {d.year}"


def day_month(d):
    d = parse_date(d)
    return f"{d.day} {MONTHS[d.month - 1]}"


def day_month_year(d):
    d = parse_date(d)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def span(lo, hi):
    """'6 to 10 weeks' or 'about 4 to 6 months'."""
    if hi > SAY_MONTHS_ABOVE_WEEKS:
        mlo = max(1, round(lo / WEEKS_PER_MONTH))
        mhi = max(mlo, round(hi / WEEKS_PER_MONTH))
        return f"about {mlo} months" if mlo == mhi else f"about {mlo} to {mhi} months"
    if lo == hi:
        return f"about {lo} weeks"
    return f"{lo} to {hi} weeks"


def lag_phrase(weeks):
    if weeks <= 0:
        return "at the same time"
    if weeks > SAY_MONTHS_ABOVE_WEEKS:
        m = round(weeks / WEEKS_PER_MONTH)
        return f"about {m} month{'s' if m != 1 else ''} later"
    return f"{weeks} week{'s' if weeks != 1 else ''} later"


def status_label(status):
    return {
        "arriving_now": "Arriving now",
        "rising_abroad": "Coming soon",
        "already_here": "Already here",
        "peaked_here": "Peaked here",
        "not_travelling": "Not heading here",
    }[status]


def why(fc):
    """One-sentence 'why' for a card."""
    s, origin = fc["status"], fc.get("origin_name")
    win = fc.get("window")
    if s in ("rising_abroad", "arriving_now"):
        lead = f"Taking off in {origin} since {month_year(fc['origin_week'])}."
        if s == "arriving_now":
            if fc.get("sg_rising"):
                return lead + " Singapore searches are starting to move."
            return lead + " Foods like this usually reach Singapore around now."
        if win and win.get("wide"):
            return lead + (f" Past foods reached Singapore anywhere from {lag_phrase(win['lag_low']).replace(' later', '')}"
                           f" to {lag_phrase(win['lag_high'])}, so watch it rather than bet on a date.")
        if win:
            return lead + f" Foods like this usually reach Singapore {span(win['lag_low'], win['lag_high'])} later."
        return lead + " Not enough history yet to say when it reaches Singapore."
    if s == "already_here":
        return f"Already popular in Singapore since {month_year(fc['sg_week'])}."
    if s == "peaked_here":
        return f"Took off in Singapore in {month_year(fc['sg_week'])} and has cooled since."
    if origin:
        return f"Took off in {origin} in {month_year(fc['origin_week'])} but never caught on here."
    return "Not taking off anywhere we track."


def evidence(fc):
    """The lag in words, for the evidence block."""
    if fc.get("origin_week") and fc.get("sg_week"):
        from .forecast import weeks_between
        lag = weeks_between(fc["origin_week"], fc["sg_week"])
        if lag <= 0:
            return f"Singapore took off in {month_year(fc['sg_week'])}, no later than anywhere else we track."
        return (f"Started in {fc['origin_name']} in {month_year(fc['origin_week'])} "
                f"and reached Singapore {lag_phrase(lag)}.")
    if fc.get("origin_week"):
        return f"Started in {fc['origin_name']} in {month_year(fc['origin_week'])}. Hasn't taken off in Singapore yet."
    if fc.get("sg_week"):
        return f"Took off in Singapore in {month_year(fc['sg_week'])}."
    return "No clear takeoff in any region we track."
