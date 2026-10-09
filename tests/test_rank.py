import unittest

from leadtime import rank


def item(cid, status, verdict, start=None):
    window = {"start": start} if start else None
    fit = {"verdict": verdict} if verdict else None
    return {"forecast": {"concept_id": cid, "status": status, "window": window}, "fit": fit}


class RankTest(unittest.TestCase):
    def test_order_status_then_verdict_then_arrival(self):
        items = [
            item("a", "rising_abroad", "make", "2025-03-01"),
            item("b", "arriving_now", "adapt", "2025-01-01"),
            item("c", "rising_abroad", "make", "2025-02-01"),
            item("d", "arriving_now", "make", "2025-01-15"),
            item("e", "rising_abroad", "adapt", "2025-01-01"),
            item("f", "rising_abroad", "make"),                 # no window sorts last among makes
            item("g", "rising_abroad", "make", "2025-04-01"),
        ]
        top, more = rank.rank(items)
        self.assertEqual([i["forecast"]["concept_id"] for i in top], ["d", "b", "c"])
        self.assertEqual([i["forecast"]["concept_id"] for i in more], ["a", "g", "f"])

    def test_drops_skips_unjudged_and_non_candidates(self):
        items = [
            item("skip", "arriving_now", "skip"),
            item("unjudged", "arriving_now", None),
            item("here", "already_here", "make"),
            item("gone", "not_travelling", "make"),
            item("ok", "rising_abroad", "adapt"),
        ]
        top, more = rank.rank(items)
        self.assertEqual([i["forecast"]["concept_id"] for i in top], ["ok"])
        self.assertEqual(more, [])


if __name__ == "__main__":
    unittest.main()
