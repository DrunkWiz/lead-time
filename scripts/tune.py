"""Try a small grid of takeoff constants against the backtest and print the results.

Used once to pick the frozen values in leadtime/config.py; see docs/DECISIONS.md.
    py -3 scripts/tune.py
"""
import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from leadtime import backtest, data, forecast, takeoff  # noqa: E402

GRID = {
    "TAKEOFF_RATIO": [2.5, 3.0],
    "SMOOTH_WEEKS": [1, 3],
    "BASELINE_WEEKS": [12],
    "BASELINE_GAP_WEEKS": [0, 4, 8, 12],
}


def main():
    snap, concepts, final = data.snapshot(), data.concepts(), data.snapshot_date()
    keys = list(GRID)
    print(f"{'  '.join(keys)}  cases  lag(med)  judged inside early late never  med_warn")
    for combo in itertools.product(*GRID.values()):
        for k, v in zip(keys, combo):
            setattr(takeoff, k, v)
        takeoff._detect.cache_clear()
        cases = forecast.historical_cases(snap, concepts, final)
        lags = sorted(c["lag_weeks"] for c in cases)
        res = backtest.run(snap, concepts, final)
        s = res["summary"]
        o = s["outcomes"]
        med = lags[len(lags) // 2] if lags else "-"
        print(f"{combo}  {len(cases):>5}  {med!s:>8}  {s['forecasts_judged']:>6} {o['inside']:>6} {o['early']:>5} "
              f"{o['late']:>4} {o['never_arrived']:>5}  {s['median_warning_weeks']}")


if __name__ == "__main__":
    main()
