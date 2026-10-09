"""Print predicted vs actual for every historical case. Paste the output into the README unedited.

    py -3 scripts/backtest_report.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from leadtime import backtest, config, data  # noqa: E402


def blank(x):
    return "" if x is None else x


def main():
    res = backtest.run(data.snapshot(), data.concepts(), data.snapshot_date())
    s = res["summary"]
    print(f"Lead Time backtest, snapshot to {res['as_of']}")
    print(f"Constants: BASELINE_WEEKS={config.BASELINE_WEEKS} TAKEOFF_RATIO={config.TAKEOFF_RATIO} "
          f"SUSTAIN={config.SUSTAIN} MIN_BASELINE={config.MIN_BASELINE} "
          f"MIN_TAKEOFF_VALUE={config.MIN_TAKEOFF_VALUE} SMOOTH_WEEKS={config.SMOOTH_WEEKS} "
          f"BASELINE_GAP_WEEKS={config.BASELINE_GAP_WEEKS} MIN_CASES={config.MIN_CASES}")
    print()
    hdr = (f"{'concept':<27}{'from':<6}{'origin wk':<12}{'flagged':<12}{'window then':<25}"
           f"{'SG actual':<12}{'outcome':<14}{'miss':>5}{'warn':>6}")
    print(hdr)
    print("-" * len(hdr))
    for r in res["rows"]:
        w = r["window"]
        win = f"{w['start']}..{w['end']}" if w else "-"
        print(f"{r['concept_id']:<27}{r['origin']:<6}{r['origin_week']:<12}{r['flagged_on']:<12}{win:<25}"
              f"{(r['actual_sg_week'] or '-'):<12}{r['outcome']:<14}"
              f"{blank(r['miss_weeks']):>5}{blank(r['warning_weeks']):>6}")
    print()
    print(f"Flagged abroad: {s['concepts_flagged']}  Forecasts judged: {s['forecasts_judged']}  "
          f"Inside window: {s['inside_window']}")
    print(f"Median miss (weeks, judged forecasts): {s['median_miss_weeks']}  "
          f"Median warning before SG takeoff (weeks): {s['median_warning_weeks']}")
    print("Outcomes:", ", ".join(f"{k}={v}" for k, v in s["outcomes"].items()))
    loo = res["leave_one_out"]
    print()
    print("Leave-one-out (ignores time order; checks whether lags generalise):")
    for r in loo["rows"]:
        w = f"{r['window'][0]}-{r['window'][1]} wk" if r["window"] else "not enough other cases"
        if r["inside"] is None:
            result = ""
        elif r["inside"]:
            result = "inside"
        else:
            result = f"missed by {r['miss_weeks']} wk"
        print(f"  {r['concept_id']:<27} actual lag {r['lag_weeks']:>3} wk   window from others {w:<24}{result}")
    print(f"  {loo['inside']} of {loo['judged']} inside; median miss {loo['median_miss_weeks']} weeks")
    le = res["late_entry"]
    print()
    print("Late entry (already in Singapore: is it still worth joining? rewound to the day SG takeoff was confirmed):")
    for r in le["rows"]:
        left = "still running" if r["actual_weeks_left"] is None else f"{r['actual_weeks_left']} wk left"
        verdict = "" if r["right"] is None else ("right" if r["right"] else "wrong")
        print(f"  {r['concept_id']:<27} {r['confirmed_on']}  {r['weeks_in']:>2} wk in  call={r['call']:<8} actual: {left:<14}{verdict}")
    print(f"  {le['right']} of {le['judged']} calls right")


if __name__ == "__main__":
    main()
