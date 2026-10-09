import unittest

from leadtime import series


class SeriesTest(unittest.TestCase):
    def test_combine_sums_aliases_and_drops_partial_weeks(self):
        rec = {"dates": ["2024-01-07", "2024-01-14", "2024-01-21"],
               "values": {"tanghulu": [1, 2, 3], "탕후루": [10, 20, 30], "糖葫芦": [50, 50, 50]},
               "is_partial": [False, False, True]}
        self.assertEqual(series.combine_terms(rec), {"2024-01-07": 61, "2024-01-14": 72})
        self.assertEqual(series.combine_terms(rec, allowed=["tanghulu", "탕후루"]),
                         {"2024-01-07": 11, "2024-01-14": 22})

    def test_build_aligns_regions_on_one_week_axis(self):
        a = {"concept_id": "x", "geo": "SG", "dates": ["2024-01-07", "2024-01-14"], "values": {"x": [1, 2]}}
        b = {"concept_id": "x", "geo": "KR", "dates": ["2024-01-14", "2024-01-21"], "values": {"x": [5, 6]}}
        snap = series.build([a, b])
        self.assertEqual(snap["weeks"], ["2024-01-07", "2024-01-14", "2024-01-21"])
        self.assertEqual(snap["series"]["x"]["SG"], [1, 2, None])
        self.assertEqual(snap["series"]["x"]["KR"], [None, 5, 6])

    def test_week_counts_only_once_finished(self):
        weeks = ["2024-01-07", "2024-01-14"]
        self.assertEqual(series.observed_count(weeks, "2024-01-12"), 0)
        self.assertEqual(series.observed_count(weeks, "2024-01-13"), 1)
        self.assertEqual(series.observed_count(weeks, "2024-01-20"), 2)


if __name__ == "__main__":
    unittest.main()
