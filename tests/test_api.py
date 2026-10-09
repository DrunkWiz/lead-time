"""End-to-end through the router on a fixture snapshot. No network, no keys."""
import unittest
from unittest import mock

from leadtime import app, data, fit, launch
from leadtime.providers import Chain, FakeProvider, OfflineProvider
from leadtime.series import week_end
from tests import fixtures as fx

PROFILE = {"name": "Test Café", "sells": ["dessert"], "equipment": ["stovetop", "fridge"], "price_band": "mid"}


class ApiTest(unittest.TestCase):
    def setUp(self):
        snap, concepts = fx.history_snapshot(current_origin_at=90)
        self.snap = snap
        patches = [
            mock.patch.object(data, "snapshot", lambda: snap),
            mock.patch.object(data, "concepts", lambda: concepts),
            mock.patch.object(data, "meta", lambda: {"fetched_at": "2024-04-01T00:00:00+00:00", "regions": ["SG", "KR"]}),
            mock.patch.object(data, "youtube", lambda: {"fetched_at": None, "concepts": {}}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        fit._memory.clear()
        launch._memory.clear()
        app._chain = Chain([], offline=OfflineProvider({"fit": fit.offline_fit, "launch": launch.offline_plan}))
        self.addCleanup(setattr, app, "_chain", None)
        # keep tests off the on-disk caches
        for mod in (fit, launch):
            p = mock.patch.object(mod, "CACHE_DIR", mod.CACHE_DIR.parent / "_test_nonexistent")
            p.start()
            self.addCleanup(p.stop)

    def as_of(self, i):
        return week_end(self.snap["weeks"][i]).isoformat()

    def test_meta(self):
        status, body = app.route("GET", "/api/meta")
        self.assertEqual(status, 200)
        self.assertEqual(body["snapshot_date"], self.as_of(-1))
        self.assertIn("ladder", body["agent"])

    def test_concepts_list_and_detail(self):
        status, body = app.route("GET", "/api/concepts", {"as_of": self.as_of(95)})
        self.assertEqual(status, 200)
        current = next(c for c in body["concepts"] if c["id"] == "current")
        self.assertEqual(current["status"], "rising_abroad")
        status, detail = app.route("GET", "/api/concepts/current", {"as_of": self.as_of(95)})
        self.assertEqual(status, 200)
        self.assertEqual(len(detail["series"]["weeks"]), 96)   # nothing after as_of

    def test_recommend_and_launch(self):
        status, body = app.route("POST", "/api/recommend", body={"profile": PROFILE, "as_of": self.as_of(94)})
        self.assertEqual(status, 200)
        self.assertEqual([c["id"] for c in body["cards"]], ["current"])
        card = body["cards"][0]
        self.assertEqual(card["fit"]["verdict"], "make")
        self.assertEqual(card["launch"]["kind"], "date")
        self.assertEqual(body["agent"]["attempts"][0]["provider"], "offline")

        status, lp = app.route("POST", "/api/launch",
                               body={"profile": PROFILE, "as_of": self.as_of(94), "concept_id": "current"})
        self.assertEqual(status, 200)
        self.assertEqual(lp["plan_provider"], "offline")
        self.assertEqual(len(lp["plan"]["hooks"]), 3)
        self.assertEqual(lp["links"], [])

    def test_model_numbers_never_reach_the_response(self):
        bad_fit = {"verdict": "make", "adaptation": "", "missing_equipment": [],
                   "reason": "Sells about 300 a day in Seoul right now.", "overlaps": []}
        app._chain = Chain([FakeProvider([bad_fit] * 5, name="liar")],
                           offline=OfflineProvider({"fit": fit.offline_fit, "launch": launch.offline_plan}))
        status, body = app.route("POST", "/api/recommend", body={"profile": PROFILE, "as_of": self.as_of(95)})
        self.assertEqual(status, 200)
        self.assertNotIn("300", body["cards"][0]["fit"]["reason"])
        self.assertEqual(body["cards"][0]["fit_provider"], "offline")

    def test_bad_inputs_get_plain_errors(self):
        self.assertEqual(app.route("GET", "/api/concepts", {"as_of": "yesterday"})[0], 400)
        self.assertEqual(app.route("GET", "/api/concepts", {"as_of": "2099-01-01"})[0], 400)
        self.assertEqual(app.route("GET", "/api/concepts/nope")[0], 404)
        self.assertEqual(app.route("POST", "/api/recommend", body={"profile": {"sells": []}})[0], 400)
        self.assertEqual(app.route("GET", "/api/nothing")[0], 404)

    def test_changes_feed_reports_new_takeoff_and_status(self):
        # origin takes off at week 90, confirmed at 94: the feed checked weekly should see it then
        status, body = app.route("GET", "/api/changes", {"as_of": self.as_of(99), "weeks": "8"})
        self.assertEqual(status, 200)
        mine = [e for e in body["events"] if e["concept_id"] == "current"]
        kinds = {(e["kind"], e.get("geo"), e.get("to")) for e in mine}
        self.assertIn(("takeoff", "KR", None), kinds)
        self.assertIn(("status", None, "arriving_now"), kinds)
        takeoff = next(e for e in mine if e["kind"] == "takeoff")
        self.assertEqual(takeoff["seen_on"], self.as_of(94))
        self.assertEqual(takeoff["week"], self.snap["weeks"][90])
        self.assertEqual(app.route("GET", "/api/changes", {"weeks": "lots"})[0], 400)

    def test_changes_feed_has_no_lookahead(self):
        from tests.test_no_lookahead import corrupt_after
        from leadtime import feed
        as_of = self.as_of(99)
        bad = corrupt_after(self.snap, as_of)
        concepts = data.concepts()
        self.assertEqual(feed.changes(self.snap, concepts, as_of), feed.changes(bad, concepts, as_of))

    def test_plan_builds_timeline_and_shopping_list(self):
        status, body = app.route("POST", "/api/plan", body={
            "profile": PROFILE, "as_of": self.as_of(94), "concept_ids": ["current", "past-0", "current"]})
        self.assertEqual(status, 200)
        self.assertEqual([i["id"] for i in body["items"]], ["current", "past-0"])  # deduped, dated first
        self.assertEqual(body["shopping"][0]["ingredient"], "flour")
        self.assertEqual(len(body["shopping"][0]["for"]), 2)
        too_many = {"profile": PROFILE, "concept_ids": ["current"] * 13}
        self.assertEqual(app.route("POST", "/api/plan", body=too_many)[0], 400)

    def test_backtest(self):
        status, body = app.route("GET", "/api/backtest")
        self.assertEqual(status, 200)
        self.assertTrue(body["rows"])


if __name__ == "__main__":
    unittest.main()
