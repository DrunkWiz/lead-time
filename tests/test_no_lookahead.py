"""Corrupt every value after as_of and assert no output changes."""
import copy
import random
import unittest

from leadtime import backtest, forecast as F, series
from tests import fixtures as fx


def corrupt_after(snap, as_of, seed=0):
    rng = random.Random(seed)
    bad = copy.deepcopy(snap)
    n = series.observed_count(bad["weeks"], as_of)
    for geos in bad["series"].values():
        for geo, values in geos.items():
            for i in range(n, len(values)):
                values[i] = rng.choice([0, 100, 1000, None])
    return bad


class NoLookaheadTest(unittest.TestCase):
    def test_forecasts_ignore_the_future(self):
        snap, concepts = fx.history_snapshot(current_origin_at=60)
        for idx in (30, 45, 64, 70, 90, 110):
            as_of = series.week_end(snap["weeks"][idx]).isoformat()
            # also corrupt the partially observed week itself
            bad = corrupt_after(snap, as_of, seed=idx)
            good_out, good_cases = F.forecast_all(snap, concepts, as_of)
            bad_out, bad_cases = F.forecast_all(bad, concepts, as_of)
            self.assertEqual(good_out, bad_out, f"lookahead at {as_of}")
            self.assertEqual(good_cases, bad_cases)

    def test_mid_week_as_of_ignores_unfinished_week(self):
        snap, concepts = fx.history_snapshot(current_origin_at=60)
        as_of = series.parse_date(snap["weeks"][70])  # the Sunday the week starts: not finished
        bad = corrupt_after(snap, as_of)
        self.assertEqual(F.forecast_all(snap, concepts, as_of), F.forecast_all(bad, concepts, as_of))

    def test_backtest_rows_use_only_data_before_flag_date(self):
        snap, concepts = fx.history_snapshot(lags=(6, 8, 10, 12, 9), current_origin_at=80)
        final = series.week_end(snap["weeks"][-1]).isoformat()
        rows = backtest.run(snap, concepts, final)["rows"]
        for r in rows:
            bad = corrupt_after(snap, r["flagged_on"], seed=1)
            c = next(c for c in concepts if c["id"] == r["concept_id"])
            self.assertEqual(F.forecast(c, snap, concepts, r["flagged_on"]),
                             F.forecast(c, bad, concepts, r["flagged_on"]))


if __name__ == "__main__":
    unittest.main()
