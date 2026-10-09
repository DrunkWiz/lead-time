"""Lifespan, Go/Wait/Skip, keep/push/drop and menu overlaps. No network, no keys."""
import unittest

from leadtime import decision, fit, lifecycle
from leadtime.schema import SchemaError
from leadtime.series import week_end
from tests import fixtures as fx

TYPICAL = {"low": 7, "high": 13, "median": 8}
LIFE = {"typical": TYPICAL, "n_cases": 6, "longest": [{"name": "Big One", "length": 60}]}
NO_INPUTS = {"price": None, "cost": None, "units_per_week": None}
FIT_MAKE = {"verdict": "make", "adaptation": "", "missing_equipment": [], "reason": "Easy.", "overlaps": []}
DATE_WHEN = {"kind": "date", "date": "2025-03-09", "text": "Launch by 9 Mar."}


def fc(status, **kw):
    base = {"status": status, "window": None, "origin_name": "South Korea", "origin_week": "2025-01-05",
            "sg_week": None, "sg_rising": False}
    base.update(kw)
    return base


def wave(elapsed, climbing=False, steady=False):
    return {"length": None, "ongoing": True, "elapsed": elapsed, "peak_week": None,
            "climbing": climbing, "steady": steady}


class LifecycleTest(unittest.TestCase):
    def test_first_wave_length_and_censoring(self):
        w = fx.weeks()
        sg = fx.rise_and_fall(30, length=10)       # up for 10 weeks, then back to baseline
        tk = w[30]
        done = lifecycle.first_wave(w, sg, tk, week_end(w[-1]))
        self.assertFalse(done["ongoing"])
        # measured to when the fade is *visible*: smoothing and the 4-week mean add ~3 weeks
        self.assertTrue(10 <= done["length"] <= 14)
        running = lifecycle.first_wave(w, sg, tk, week_end(w[35]))
        self.assertTrue(running["ongoing"])
        self.assertIsNone(running["length"])
        self.assertEqual(running["elapsed"], 5)

    def test_steady_needs_every_recent_raw_week_nonzero(self):
        w = fx.weeks()
        steady = fx.step(30, low=0, high=40)
        spiky = [40 if (i >= 30 and i % 2 == 0) else 0 for i in range(len(w))]
        self.assertTrue(lifecycle.first_wave(w, steady, w[30], week_end(w[36]))["steady"])
        self.assertFalse(lifecycle.first_wave(w, spiky, w[30], week_end(w[36]))["steady"])

    def test_lifespan_needs_min_cases_and_ignores_running_waves(self):
        w = fx.weeks()
        series, concepts = {}, []
        for k, length in enumerate([6, 8, 10, 12]):
            cid = f"c{k}"
            series[cid] = {"KR": fx.step(15), "SG": fx.rise_and_fall(20 + k, length=length)}
            concepts.append(fx.concept(cid))
        series["live"] = {"KR": fx.step(15), "SG": fx.step(100)}   # still running at the end
        concepts.append(fx.concept("live"))
        snap = {"weeks": w, "series": series}
        life = lifecycle.lifespan(snap, concepts, week_end(w[-1]))
        self.assertEqual(life["n_cases"], 4)
        self.assertIsNotNone(life["typical"])
        early = lifecycle.lifespan(snap, concepts, week_end(w[30]))   # none had ended yet
        self.assertIsNone(early["typical"])

    def test_phase(self):
        self.assertEqual(lifecycle.phase(2, TYPICAL), "early")
        self.assertEqual(lifecycle.phase(6, TYPICAL), "middle")
        self.assertEqual(lifecycle.phase(10, TYPICAL), "late")
        self.assertEqual(lifecycle.phase(20, TYPICAL), "overtime")
        self.assertIsNone(lifecycle.phase(3, None))


class DecideTest(unittest.TestCase):
    def test_go_with_stock_plan_and_profit(self):
        d = decision.decide(fc("rising_abroad"), FIT_MAKE, DATE_WHEN, LIFE, None, "2025-02-01",
                            {"price": 6.5, "cost": 2.0, "units_per_week": 50})
        self.assertEqual(d["verdict"], "go")
        self.assertEqual(d["money"]["margin"], 4.5)
        self.assertEqual(d["money"]["profit_low"], round(50 * 4.5 * 7))
        self.assertEqual(d["money"]["profit_high"], round(50 * 4.5 * 13))
        self.assertEqual(d["stock"]["bulk_until"], "2025-04-13")   # 9 Mar + (7 - 2) weeks

    def test_wait_when_no_reliable_date(self):
        d = decision.decide(fc("rising_abroad"), FIT_MAKE, {"kind": "watch", "date": None, "text": ""},
                            LIFE, None, "2025-02-01", NO_INPUTS)
        self.assertEqual(d["verdict"], "wait")
        self.assertIsNone(d["stock"])

    def test_already_here_late_vs_steady(self):
        args = (FIT_MAKE, {"kind": "following", "date": None, "text": ""}, LIFE)
        self.assertEqual(decision.decide(fc("already_here"), *args, wave(4), "2025-02-01", NO_INPUTS)["verdict"], "skip")
        self.assertEqual(decision.decide(fc("already_here"), *args, wave(4, steady=True), "2025-02-01", NO_INPUTS)["verdict"], "go_late")
        self.assertEqual(decision.decide(fc("already_here"), *args, wave(4, climbing=True), "2025-02-01", NO_INPUTS)["verdict"], "go_late")
        self.assertEqual(decision.decide(fc("already_here"), *args, wave(1), "2025-02-01", NO_INPUTS)["verdict"], "go_late")

    def test_skips(self):
        skip_fit = dict(FIT_MAKE, verdict="skip", reason="Needs a fryer.")
        self.assertEqual(decision.decide(fc("arriving_now"), skip_fit, DATE_WHEN, LIFE, None, "2025-02-01", NO_INPUTS)["verdict"], "skip")
        self.assertEqual(decision.decide(fc("peaked_here"), FIT_MAKE, DATE_WHEN, LIFE, None, "2025-02-01", NO_INPUTS)["verdict"], "skip")
        losing = decision.decide(fc("arriving_now"), FIT_MAKE, DATE_WHEN, LIFE, None, "2025-02-01",
                                 {"price": 3.0, "cost": 3.5, "units_per_week": 40})
        self.assertEqual(losing["verdict"], "skip")
        self.assertIsNone(losing["money"]["profit_low"])

    def test_overlap_reason(self):
        f = dict(FIT_MAKE, overlaps=["Pistachio latte"])
        d = decision.decide(fc("arriving_now"), f, DATE_WHEN, LIFE, None, "2025-02-01", NO_INPUTS)
        self.assertTrue(any("Pistachio latte" in r["text"] for r in d["reasons"]))

    def test_clean_inputs_rejects_nonsense(self):
        self.assertEqual(decision.clean_inputs({"price": "abc", "cost": -1, "units_per_week": 0}),
                         {"price": None, "cost": None, "units_per_week": None})


class ReviewTest(unittest.TestCase):
    def logs(self, sold):
        return [{"week": f"2025-03-{i + 1:02d}", "sold": s} for i, s in enumerate(sold)]

    def test_too_early(self):
        self.assertEqual(decision.review(fc("already_here"), wave(3), LIFE, self.logs([30, 40]))["verdict"], "too_early")

    def test_push_keep_rethink_drop(self):
        early, late = wave(3), wave(11)
        self.assertEqual(decision.review(fc("already_here"), early, LIFE, self.logs([30, 40, 48]))["verdict"], "push")
        self.assertEqual(decision.review(fc("already_here"), late, LIFE, self.logs([30, 40, 40]))["verdict"], "keep")
        self.assertEqual(decision.review(fc("already_here"), early, LIFE, self.logs([50, 50, 20, 15]))["verdict"], "rethink")
        self.assertEqual(decision.review(fc("peaked_here"), late, LIFE, self.logs([50, 50, 20, 15]))["verdict"], "drop")

    def test_money_metrics(self):
        r = decision.review(fc("already_here"), wave(3), LIFE, self.logs([10, 20, 30]), price=5.0, cost=2.0)
        self.assertEqual(r["metrics"]["total"], 60)
        self.assertEqual(r["metrics"]["revenue"], 300.0)
        self.assertEqual(r["metrics"]["profit"], 180.0)


class MenuOverlapTest(unittest.TestCase):
    def setUp(self):
        self.profile = fit.normalise_profile({
            "sells": ["dessert"], "equipment": ["stovetop", "fridge", "moulds"], "price_band": "mid",
            "menu": ["Pistachio Latte", "  kaya toast ", "Pistachio latte"]})
        self.concept = dict(fx.concept("dubai-chocolate", equipment=["stovetop"]),
                            name="Dubai chocolate", key_ingredients=["pistachio cream", "kataifi"])

    def test_menu_is_cleaned_and_deduped(self):
        self.assertEqual(self.profile["menu"], ["Pistachio Latte", "kaya toast"])

    def test_model_overlaps_must_be_on_the_menu(self):
        check = fit.make_validator(self.concept, self.profile)
        good = {"verdict": "make", "adaptation": "", "missing_equipment": [], "reason": "Easy here.",
                "overlaps": ["pistachio latte"]}
        self.assertEqual(check(dict(good))["overlaps"], ["Pistachio Latte"])   # shop's spelling
        with self.assertRaises(SchemaError):
            check(dict(good, overlaps=["Matcha cake"]))                        # invented item
        with self.assertRaises(SchemaError):
            check({k: v for k, v in good.items() if k != "overlaps"})          # field required

    def test_offline_overlap_rule(self):
        out = fit.offline_fit({"concept": self.concept, "profile": self.profile})
        self.assertEqual(out["overlaps"], ["Pistachio Latte"])

    def test_menu_changes_the_cache_key(self):
        other = dict(self.profile, menu=[])
        self.assertNotEqual(fit.profile_hash(self.profile), fit.profile_hash(other))


if __name__ == "__main__":
    unittest.main()
