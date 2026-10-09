"""Offer arithmetic and the content plan. No network, no keys."""
import unittest

from leadtime import content, offers
from tests import fixtures as fx

PRICE, COST, UNITS = 6.5, 1.55, 45


class OfferMathTest(unittest.TestCase):
    def test_free_first_payback(self):
        o = offers.free_first(PRICE, COST, UNITS, n=50)
        self.assertEqual(o["cost"], 77.5)                       # 50 x 1.55
        self.assertEqual(o["payback_sales"], 16)                # ceil(77.5 / 4.95)
        self.assertIn("1 in 3", o["plain"])                     # round(50 / 16)

    def test_free_first_when_payback_exceeds_giveaway(self):
        o = offers.free_first(2.0, 1.8, UNITS, n=10)            # thin margin: 18 / 0.2 = 90 sales
        self.assertEqual(o["payback_sales"], 90)
        self.assertIn("more than the 10", o["plain"])

    def test_discount_lift(self):
        o = offers.launch_discount(PRICE, COST, UNITS, d=0.2)
        self.assertAlmostEqual(o["margin_each"], 3.65)
        self.assertAlmostEqual(o["lift_needed"], round(4.95 / 3.65, 2))

    def test_second_half_and_loyalty(self):
        o = offers.second_half(PRICE, COST, UNITS)
        self.assertAlmostEqual(o["margin_each"], round((1.5 * PRICE - 2 * COST) / 2, 2))
        l = offers.loyalty(PRICE, COST, UNITS, n=5)
        self.assertAlmostEqual(l["margin_each"], round((5 * PRICE - 6 * COST) / 6, 2))

    def test_daily_drop_cap(self):
        under = offers.daily_drop(PRICE, COST, 45, k=40)
        self.assertEqual(under["weekly_profit"], round(45 * 4.95, 2))   # demand below the cap
        over = offers.daily_drop(PRICE, COST, 400, k=40)
        self.assertEqual(over["weekly_profit"], round(240 * 4.95, 2))   # capped at 40 x 6 days
        self.assertIn("turn away", over["plain"])
        self.assertEqual(offers.daily_drop(PRICE, COST, 45, k=40, capacity=25)["params"]["per_day"], 25)

    def test_losing_offers_are_flagged_and_never_recommended(self):
        p = offers.plan(3.0, 2.6, 30, verdict="go")
        by = {o["type"]: o for o in p["offers"]}
        self.assertTrue(by["launch_discount"]["stretch"])       # 20% off a 40-cent margin
        self.assertNotEqual(p["recommended"]["type"], "launch_discount")
        self.assertIsNone(offers.plan(3.0, 3.5, 30, verdict="go")["recommended"])   # losing money: no offer

    def test_recommendation_follows_timing(self):
        self.assertEqual(offers.plan(PRICE, COST, UNITS, verdict="go")["recommended"]["type"], "free_first")
        self.assertEqual(offers.plan(PRICE, COST, UNITS, verdict="go_late")["recommended"]["type"], "second_half")
        self.assertEqual(offers.plan(PRICE, COST, UNITS, verdict="wait")["recommended"]["type"], "daily_drop")

    def test_needs_price_and_cost(self):
        p = offers.plan(None, COST, UNITS)
        self.assertFalse(p["ready"])
        self.assertEqual(p["offers"], [])


class ContentPlanTest(unittest.TestCase):
    def concept(self, **kw):
        c = fx.concept("x")
        c.update(kw)
        return c

    def test_formats_follow_the_food(self):
        filled = self.concept(description="Bar filled with pistachio cream", techniques=["tempering"],
                              key_ingredients=["pistachio cream", "kataifi"])
        self.assertEqual(content.pick_formats(filled)[0], "cross_section")
        drink = self.concept(category="drink", description="Strong coffee under salted foam",
                             techniques=["brewing"], key_ingredients=["espresso", "condensed milk"])
        self.assertEqual(content.pick_formats(drink)[0], "pour")
        plain = self.concept(description="Plain thing", techniques=["baking"], key_ingredients=["flour"])
        self.assertEqual(content.pick_formats(plain), ["build"])

    def test_dates_around_launch_day(self):
        when = {"kind": "date", "date": "2025-03-09"}
        p = content.plan(self.concept(), when, as_of="2025-02-01")
        self.assertEqual([x["date"] for x in p["posts"]],
                         ["2025-03-02", "2025-03-06", "2025-03-09", "2025-03-11", "2025-03-16"])

    def test_launch_now_moves_launch_and_drops_past_posts(self):
        when = {"kind": "now", "date": "2025-03-09"}
        p = content.plan(self.concept(), when, as_of="2025-03-09")
        self.assertEqual(p["launch_date"], "2025-03-12")                      # +3 days to announce
        self.assertNotIn("Tease", [x["label"] for x in p["posts"]])
        self.assertTrue(all(x["date"] >= "2025-03-09" for x in p["posts"]))
        self.assertIn("No time for the tease", p["when_text"])

    def test_no_date_means_relative_plan(self):
        p = content.plan(self.concept(), {"kind": "watch", "date": None}, as_of="2025-03-09")
        self.assertTrue(all(x["date"] is None for x in p["posts"]))
        self.assertEqual(len(p["posts"]), 5)

    def test_offer_shapes_the_plan(self):
        when = {"kind": "date", "date": "2025-03-09"}
        free = content.plan(self.concept(), when, "free_first", "First 50 free on launch day", as_of="2025-02-01")
        self.assertEqual(free["posts"][2]["format"], "line")
        self.assertIn("First 50 free", free["posts"][1]["on_screen"])
        drop = content.plan(self.concept(), when, "daily_drop", "Only 40 a day", as_of="2025-02-01")
        self.assertEqual(drop["posts"][-1]["format"], "sold_out")

    def test_on_screen_text_has_no_dates_or_links(self):
        from leadtime.launch import validate_plan
        when = {"kind": "date", "date": "2025-03-09"}
        p = content.plan(self.concept(), when, "free_first", "First 50 free on launch day", as_of="2025-02-01")
        for post in p["posts"]:
            # reuse the launch-plan validator's rules on everything we print over the video
            validate_plan({"method": [{"component": "Post", "steps": [post["on_screen"]]}], "swaps": [],
                           "hooks": ["a hook", "b hook", "c hook"], "caption": "cap", "offer": "off"})


if __name__ == "__main__":
    unittest.main()
