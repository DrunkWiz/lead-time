"""Takeoff detection: the first week a series clearly and durably leaves its baseline."""
import statistics
from functools import lru_cache

from .config import (BASELINE_GAP_WEEKS, BASELINE_WEEKS, MIN_BASELINE, MIN_TAKEOFF_VALUE,
                     RISING_WEEKS, SMOOTH_WEEKS, SUSTAIN, TAKEOFF_RATIO)
from .series import cut


def _clean(values):
    """None -> 0, then a trailing mean over SMOOTH_WEEKS (trailing, so no lookahead).

    Low-volume regions come back from Google as 0 / spike / 0; smoothing turns
    a run of spikes into a level the takeoff rule can see.
    """
    v = [0 if x is None else x for x in values]
    k = SMOOTH_WEEKS
    if k <= 1:
        return v
    return [sum(v[max(0, i - k + 1):i + 1]) / (i + 1 - max(0, i - k + 1)) for i in range(len(v))]


def first_testable():
    return BASELINE_WEEKS + BASELINE_GAP_WEEKS


def threshold_at(values, i):
    """The bar week i must clear: TAKEOFF_RATIO x the median of a baseline that
    ends BASELINE_GAP_WEEKS before i (floored at MIN_BASELINE). The gap lets a
    slow climb register instead of dragging its own baseline up with it."""
    end = i - BASELINE_GAP_WEEKS
    base = statistics.median(values[end - BASELINE_WEEKS:end])
    return max(base, MIN_BASELINE) * TAKEOFF_RATIO


def detect_index(values):
    return _detect(tuple(_clean(values)))


@lru_cache(maxsize=65536)  # the backtest asks the same question about the same prefix many times
def _detect(v):
    """Index of the first takeoff week in a fully observed series, or None.

    Week i is a takeoff if it reaches the threshold and MIN_TAKEOFF_VALUE, and
    at least SUSTAIN[0] of the next SUSTAIN[1] weeks also clear the threshold.
    Those following weeks must exist, so a takeoff is only confirmed
    SUSTAIN[1] weeks after it happens.
    """
    need, ahead = SUSTAIN
    for i in range(first_testable(), len(v) - ahead):
        thr = threshold_at(v, i)
        if v[i] < thr or v[i] < MIN_TAKEOFF_VALUE:
            continue
        if sum(1 for x in v[i + 1:i + 1 + ahead] if x >= thr) >= need:
            return i
    return None


def detect(weeks, values, as_of):
    """Takeoff week (ISO date string) observable at as_of, or None."""
    if not values:
        return None
    w, v = cut(weeks, values, as_of)
    i = detect_index(v)
    return w[i] if i is not None else None


def rising_now(weeks, values, as_of):
    """True if each of the last RISING_WEEKS observed weeks clears the takeoff bar
    (a takeoff starting but not yet confirmed)."""
    w, v = cut(weeks, values, as_of)
    v = _clean(v)
    if len(v) < first_testable() + RISING_WEEKS:
        return False
    start = len(v) - RISING_WEEKS
    thr = threshold_at(v, start)
    return all(x >= thr and x >= MIN_TAKEOFF_VALUE for x in v[start:])
