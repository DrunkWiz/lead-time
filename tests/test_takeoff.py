import unittest

from leadtime import takeoff
from leadtime.config import BASELINE_WEEKS, SUSTAIN
from leadtime.series import week_end
from tests import fixtures as fx


class TakeoffTest(unittest.TestCase):
    def test_sustained_step_is_detected_at_the_step(self):
        self.assertEqual(takeoff.detect_index(fx.step(40)), 40)

    def test_single_spike_is_not_a_trend(self):
        self.assertIsNone(takeoff.detect_index(fx.spike(40)))

    def test_flat_series_has_no_takeoff(self):
        self.assertIsNone(takeoff.detect_index(fx.flat(20)))

    def test_zero_baseline_uses_floor_not_infinite_growth(self):
        # 0 -> 1 is "infinite" growth; the MIN_BASELINE floor and MIN_TAKEOFF_VALUE stop it
        self.assertIsNone(takeoff.detect_index(fx.step(40, low=0, high=1)))
        # a real jump off zero still counts
        self.assertEqual(takeoff.detect_index(fx.step(40, low=0, high=30)), 40)

    def test_small_relative_rise_is_ignored(self):
        self.assertIsNone(takeoff.detect_index(fx.step(40, low=10, high=20)))

    def test_already_high_when_data_begins_is_not_a_takeoff(self):
        # most of the first baseline is already high: we can't see when it started
        self.assertIsNone(takeoff.detect_index(fx.step(BASELINE_WEEKS // 4)))

    def test_not_confirmed_until_sustain_weeks_observed(self):
        w, v = fx.weeks(), fx.step(40)
        too_early = week_end(w[40 + SUSTAIN[1] - 1])
        confirmed = week_end(w[40 + SUSTAIN[1]])
        self.assertIsNone(takeoff.detect(w, v, too_early))
        self.assertEqual(takeoff.detect(w, v, confirmed), w[40])

    def test_rising_now_needs_consecutive_weeks(self):
        w = fx.weeks()
        one = fx.spike(60)
        two = fx.step(59)
        from leadtime.series import week_end as we
        self.assertFalse(takeoff.rising_now(w, one, we(w[60])))
        self.assertTrue(takeoff.rising_now(w, two, we(w[60])))
        self.assertFalse(takeoff.rising_now(w, fx.flat(), we(w[60])))

    def test_none_values_are_treated_as_zero(self):
        v = fx.step(40, low=0, high=30)
        v[5] = None
        self.assertEqual(takeoff.detect_index(v), 40)


if __name__ == "__main__":
    unittest.main()
