import unittest

from leadtime import forecast as F
from leadtime.series import week_end
from tests import fixtures as fx


class LagMathTest(unittest.TestCase):
    def test_weeks_between(self):
        self.assertEqual(F.weeks_between("2024-01-07", "2024-03-03"), 8)
        self.assertEqual(F.weeks_between("2024-03-03", "2024-01-07"), -8)

    def test_percentile_matches_linear_interpolation(self):
        xs = [6, 8, 10, 12]
        self.assertAlmostEqual(F.percentile(xs, 25), 7.5)
        self.assertAlmostEqual(F.percentile(xs, 75), 10.5)
        self.assertEqual(F.percentile([5], 25), 5.0)

    def test_historical_cases_and_lags(self):
        snap, concepts = fx.history_snapshot(lags=(6, 8, 10, 12))
        as_of = week_end(snap["weeks"][-1])
        cases = F.historical_cases(snap, concepts, as_of)
        self.assertEqual(sorted(c["lag_weeks"] for c in cases), [6, 8, 10, 12])
        self.assertTrue(all(c["origin"] == "KR" for c in cases))

    def test_window_is_origin_plus_interquartile_lag(self):
        snap, concepts = fx.history_snapshot(lags=(6, 8, 10, 12), current_origin_at=90)
        as_of = week_end(snap["weeks"][95])
        current = concepts[-1]
        fc = F.forecast(current, snap, concepts, as_of)
        self.assertEqual(fc["origin"], "KR")
        self.assertEqual(fc["origin_week"], snap["weeks"][90])
        self.assertEqual(fc["window"]["lag_low"], 8)    # round(7.5) -> 8 (banker's rounding)
        self.assertEqual(fc["window"]["lag_high"], 10)  # round(10.5) -> 10
        self.assertEqual(fc["window"]["start"], snap["weeks"][98])
        self.assertEqual(fc["status"], "rising_abroad")

    def test_arriving_now_once_window_opens(self):
        snap, concepts = fx.history_snapshot(current_origin_at=90)
        fc = F.forecast(concepts[-1], snap, concepts, week_end(snap["weeks"][99]))
        self.assertEqual(fc["status"], "arriving_now")

    def test_wide_window_is_watch_only_until_singapore_moves(self):
        # past SG takeoffs at weeks 17, 24, 64, 79; all confirmed by week 85
        snap, concepts = fx.history_snapshot(lags=(3, 5, 40, 50), origin_at=14, current_origin_at=70)
        as_of = week_end(snap["weeks"][85])        # inside the (wide) window
        fc = F.forecast(concepts[-1], snap, concepts, as_of)
        self.assertTrue(fc["window"]["wide"])
        self.assertEqual(fc["status"], "rising_abroad")
        from leadtime import launch, words
        self.assertEqual(launch.launch_when(fc, as_of)["kind"], "watch")
        self.assertIn("watch it", words.why(fc))
        # once Singapore itself moves, it's arriving
        snap["series"]["current"]["SG"] = fx.step(84, low=3, high=40)
        self.assertEqual(F.forecast(concepts[-1], snap, concepts, as_of)["status"], "arriving_now")

    def test_not_travelling_long_after_window(self):
        snap, concepts = fx.history_snapshot(current_origin_at=60)
        fc = F.forecast(concepts[-1], snap, concepts, week_end(snap["weeks"][-1]))
        self.assertEqual(fc["status"], "not_travelling")

    def test_not_enough_history_gives_no_window(self):
        snap, concepts = fx.history_snapshot(lags=(6, 8, 10))   # only 3 past cases
        fc = F.forecast(concepts[-1], snap, concepts, week_end(snap["weeks"][95]))
        self.assertIsNone(fc["window"])
        self.assertEqual(fc["status"], "rising_abroad")

    def test_category_fallback_to_all(self):
        snap, concepts = fx.history_snapshot()
        concepts[-1] = dict(concepts[-1], category="drink")   # no drink history
        fc = F.forecast(concepts[-1], snap, concepts, week_end(snap["weeks"][95]))
        self.assertEqual(fc["window"]["basis"], "all")

    def test_already_here_and_peaked_here(self):
        w = fx.weeks()
        snap = {"weeks": w, "series": {
            "here": {"KR": fx.step(20), "SG": fx.step(30)},
            "gone": {"KR": fx.step(20), "SG": fx.rise_and_fall(30, length=20)},
        }}
        concepts = [fx.concept("here"), fx.concept("gone")]
        as_of = week_end(w[-1])
        self.assertEqual(F.forecast(concepts[0], snap, concepts, as_of)["status"], "already_here")
        self.assertEqual(F.forecast(concepts[1], snap, concepts, as_of)["status"], "peaked_here")

    def test_peak_status_does_not_flap(self):
        # SG rises to 60, cools to 20 (peaked), wobbles back to 30 (still under the 60% revive bar)
        w = fx.weeks()
        sg = [3] * 30 + [60] * 10 + [20] * 10 + [30] * 10
        sg += [30] * (len(w) - len(sg))
        snap = {"weeks": w, "series": {"x": {"KR": fx.step(20), "SG": sg}}}
        c = fx.concept("x")
        statuses = {F.forecast(c, snap, [c], week_end(w[i]))["status"] for i in range(55, 80)}
        self.assertEqual(statuses, {"peaked_here"})
        sg2 = sg[:60] + [55] * (len(w) - 60)   # climbs back above 60% of the peak
        snap2 = {"weeks": w, "series": {"x": {"KR": fx.step(20), "SG": sg2}}}
        self.assertEqual(F.forecast(c, snap2, [c], week_end(w[70]))["status"], "already_here")

    def test_no_takeoff_anywhere(self):
        w = fx.weeks()
        snap = {"weeks": w, "series": {"quiet": {"KR": fx.flat(), "SG": fx.flat()}}}
        c = fx.concept("quiet")
        self.assertEqual(F.forecast(c, snap, [c], week_end(w[-1]))["status"], "not_travelling")


if __name__ == "__main__":
    unittest.main()
