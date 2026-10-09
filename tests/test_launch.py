import unittest

from leadtime import fit, launch
from leadtime.config import LAUNCH_LEAD_WEEKS
from leadtime.providers import Chain, FakeProvider, OfflineProvider
from leadtime.schema import SchemaError
from tests import fixtures as fx

GOOD_PLAN = {
    "method": [{"component": "Pistachio cream", "steps": ["Blend pistachios with white chocolate until smooth"]}],
    "swaps": [{"original": "kataifi", "use": "toasted crushed feuilletine", "why": "Easier to find, same crunch"}],
    "hooks": ["You don't need a flight for this.", "First try at the cross-section.", "Is it worth the hype?"],
    "caption": "It's here. Small batches, so come early.",
    "offer": "Free drink upgrade on launch weekend.",
}


def fc(status, start=None):
    return {"status": status, "window": {"start": start, "end": start} if start else None,
            "origin_name": "South Korea", "origin_week": "2025-01-05"}


class LaunchWhenTest(unittest.TestCase):
    def test_rising_abroad_launches_lead_weeks_before_window(self):
        w = launch.launch_when(fc("rising_abroad", "2025-03-30"), "2025-02-01")
        self.assertEqual(w["kind"], "date")
        self.assertEqual(w["date"], "2025-03-09")   # 30 Mar - 3 weeks
        self.assertIn("9 Mar", w["text"])
        self.assertEqual(LAUNCH_LEAD_WEEKS, 3)

    def test_launch_date_already_passed_means_this_week(self):
        w = launch.launch_when(fc("rising_abroad", "2025-03-30"), "2025-03-20")
        self.assertEqual(w["kind"], "this_week")
        self.assertEqual(w["date"], "2025-03-20")

    def test_arriving_now(self):
        w = launch.launch_when(fc("arriving_now", "2025-03-30"), "2025-04-02")
        self.assertEqual(w["kind"], "now")
        self.assertIn("Others will be starting too", w["text"])

    def test_following_statuses_have_no_date(self):
        for s in ("already_here", "peaked_here"):
            w = launch.launch_when(fc(s), "2025-04-02")
            self.assertEqual(w["kind"], "following")
            self.assertIsNone(w["date"])
            self.assertFalse(launch.has_plan(w))

    def test_no_window_says_so(self):
        w = launch.launch_when(fc("rising_abroad"), "2025-04-02")
        self.assertEqual(w["kind"], "no_window")
        self.assertIsNone(w["date"])
        self.assertIn("Not enough history", w["text"])


class PlanValidatorTest(unittest.TestCase):
    def test_accepts_good_plan(self):
        launch.validate_plan(GOOD_PLAN)

    def test_rejects_dates_urls_and_quantities(self):
        bad_strings = [
            "Launching 2 Nov!", "Launch Nov 2nd", "From 2025-11-02", "Opens 2/11", "Big in 2025",
            "Recipe at https://youtube.com/x", "see www.example.org", "Add 200g pistachio",
            "Use 2 cups cream",
        ]
        for s in bad_strings:
            plan = dict(GOOD_PLAN, caption=s)
            with self.assertRaises(SchemaError, msg=s):
                launch.validate_plan(plan)
        # also deep inside method steps
        plan = dict(GOOD_PLAN, method=[{"component": "Cream", "steps": ["Whip until 3 Oct"]}])
        with self.assertRaises(SchemaError):
            launch.validate_plan(plan)

    def test_rejects_popularity_claims(self):
        for s_ in ["Singapore's hottest dessert", "Why everyone is obsessed", "The viral bar is here",
                   "Trending now in Seoul", "Our best-selling treat"]:
            with self.assertRaises(SchemaError, msg=s_):
                launch.validate_plan(dict(GOOD_PLAN, caption=s_))
        launch.validate_plan(dict(GOOD_PLAN, caption="Crunchy, creamy, made fresh this morning."))

    def test_month_name_alone_is_allowed(self):
        launch.validate_plan(dict(GOOD_PLAN, caption="Big in Seoul since July, now here."))

    def test_rejects_wrong_hook_count(self):
        with self.assertRaises(SchemaError):
            launch.validate_plan(dict(GOOD_PLAN, hooks=["only one"]))

    def test_offline_plan_passes_validator_for_every_concept(self):
        from leadtime.concepts import load_concepts
        profile = fit.normalise_profile({"name": "Kopi Corner", "sells": ["dessert"],
                                         "equipment": ["stovetop"], "price_band": "budget"})
        for c in load_concepts():
            f = fit.offline_fit({"concept": c, "profile": profile})
            out = launch.offline_plan({"concept": c, "profile": profile, "fit": f,
                                       "facts": {"origin": "South Korea"}})
            launch.validate_plan(out)


class PlanFlowTest(unittest.TestCase):
    def test_model_date_in_plan_is_rejected_then_offline_used(self):
        launch._memory.clear()
        bad = dict(GOOD_PLAN, offer="Launch on 2 Nov only")
        chain = Chain([FakeProvider([bad], name="m")],
                      offline=OfflineProvider({"launch": launch.offline_plan}))
        c = fx.concept("test-food")
        profile = fit.normalise_profile({"name": "Shop", "sells": ["dessert"], "equipment": ["stovetop"],
                                         "price_band": "mid"})
        out = launch.plan(chain, c, profile, None, fc("arriving_now", "2025-03-30"), "2025-04-02", {})
        self.assertEqual(out["provider"], "offline")
        self.assertFalse(out["attempts"][0]["ok"])

    def test_links_come_from_snapshot_only(self):
        yt = {"concepts": {"x": [
            {"video_id": "a", "title": "A", "channel": "c", "views": 5},
            {"video_id": "b", "title": "B", "channel": "c", "views": 50},
            {"video_id": "c", "title": "C", "channel": "c", "views": 20},
            {"video_id": "d", "title": "D", "channel": "c", "views": 1},
        ]}}
        links = launch.source_links(yt, "x")
        self.assertEqual([l["title"] for l in links], ["B", "C", "A"])
        self.assertEqual(launch.source_links(yt, "missing"), [])


if __name__ == "__main__":
    unittest.main()
