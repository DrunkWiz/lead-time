"""Schema rejection of malformed model output, and the provider chain's fallback."""
import unittest

from leadtime import fit
from leadtime.providers import Chain, FakeProvider, OfflineProvider, ProviderError, parse_json_text
from leadtime.schema import SchemaError
from tests import fixtures as fx

PROFILE = fit.normalise_profile({"name": "Test Café", "sells": ["dessert", "drink"],
                                 "equipment": ["stovetop", "fridge", "blender"], "price_band": "mid"})
CONCEPT = fx.concept("tanghulu", equipment=["stovetop"])
GOOD = {"verdict": "make", "adaptation": "", "missing_equipment": [], "reason": "You have a stovetop, that's all it takes.", "overlaps": []}


class FitValidatorTest(unittest.TestCase):
    def setUp(self):
        self.check = fit.make_validator(CONCEPT, PROFILE)

    def test_accepts_good_output(self):
        self.assertEqual(self.check(dict(GOOD)), GOOD)

    def test_rejects_bad_shapes(self):
        bad = [
            {},                                                   # empty
            dict(GOOD, verdict="maybe"),                          # not in enum
            dict(GOOD, extra="field"),                            # unknown key
            {k: v for k, v in GOOD.items() if k != "reason"},     # missing key
            dict(GOOD, missing_equipment="oven"),                 # wrong type
            dict(GOOD, missing_equipment=["laser"]),              # not in vocabulary
            dict(GOOD, reason="x" * 500),                         # too long
        ]
        for b in bad:
            with self.assertRaises(SchemaError, msg=b):
                self.check(b)

    def test_rejects_numbers_links_and_contradictions(self):
        bad = [
            dict(GOOD, reason="Sells about 300 a day in Seoul right now."),       # a number
            dict(GOOD, reason="See https://example.com for the method here."),    # a link
            dict(GOOD, verdict="make", missing_equipment=["fryer"]),             # make but missing kit
            dict(GOOD, verdict="adapt", adaptation=""),                          # adapt with nothing
            dict(GOOD, verdict="adapt", adaptation="Use the stove",
                 missing_equipment=["stovetop"]),                                # claims it lacks what it has
        ]
        for b in bad:
            with self.assertRaises(SchemaError, msg=b):
                self.check(b)


class ChainTest(unittest.TestCase):
    def test_invalid_output_is_dropped_and_next_provider_used(self):
        bad = dict(GOOD, verdict="definitely")
        p1 = FakeProvider([bad, bad], name="first")          # wrong twice: original + one retry
        p2 = FakeProvider([GOOD], name="second")
        result, provider, attempts = Chain([p1, p2]).run("fit", "s", "u", fit.make_validator(CONCEPT, PROFILE))
        self.assertEqual(provider, "second")
        self.assertEqual(result, GOOD)
        self.assertEqual([(a["provider"], a["ok"]) for a in attempts],
                         [("first", False), ("first", False), ("second", True)])

    def test_one_retry_with_the_rejection_reason(self):
        p1 = FakeProvider([dict(GOOD, verdict="definitely"), dict(GOOD)], name="first")
        result, provider, attempts = Chain([p1]).run("fit", "s", "u", fit.make_validator(CONCEPT, PROFILE))
        self.assertEqual(provider, "first")
        self.assertTrue(attempts[-1]["retry"])
        retry_prompt = p1.calls[1][2]
        self.assertIn("previous reply was rejected", retry_prompt)
        self.assertIn("definitely", retry_prompt)            # the reason is passed back, not guessed at

    def test_transport_error_falls_through_to_offline(self):
        p1 = FakeProvider([ProviderError("HTTP 500")], name="first")
        offline = OfflineProvider({"fit": fit.offline_fit})
        result, provider, attempts = Chain([p1], offline=offline).run(
            "fit", "s", "u", fit.make_validator(CONCEPT, PROFILE),
            context={"concept": CONCEPT, "profile": PROFILE})
        self.assertEqual(provider, "offline")
        self.assertEqual(result["verdict"], "make")
        self.assertEqual([a["provider"] for a in attempts], ["first", "offline"])

    def test_all_fail_returns_none(self):
        result, provider, attempts = Chain([FakeProvider([{"nope": 1}])]).run(
            "fit", "s", "u", fit.make_validator(CONCEPT, PROFILE))
        self.assertIsNone(result)
        self.assertIsNone(provider)

    def test_parse_json_text_strips_reasoning_blocks(self):
        # Qwen3-style models think out loud first; braces in the thinking must not confuse the parser
        text = '<think>The shop has {a stove}, so...</think>\n{"verdict": "make"}'
        self.assertEqual(parse_json_text(text), {"verdict": "make"})

    def test_soclaas_needs_key_base_and_model(self):
        import os
        from unittest import mock
        from leadtime.providers import SoclaasProvider, configured_providers
        with mock.patch.dict(os.environ, {"SOCLAAS_API_KEY": "k", "SOCLAAS_BASE_URL": ""}, clear=False):
            self.assertFalse(SoclaasProvider().available())
        with mock.patch.dict(os.environ, {"SOCLAAS_API_KEY": "k", "SOCLAAS_BASE_URL": "https://x/v1/"}, clear=False):
            p = SoclaasProvider()
            self.assertTrue(p.available())
            self.assertEqual(p.base, "https://x/v1")          # trailing slash trimmed
        with mock.patch.dict(os.environ, {"LT_PROVIDER_CHAIN": ""}, clear=False):
            os.environ.pop("LT_PROVIDER_CHAIN")
            self.assertEqual([p.name for p in configured_providers()], ["soclaas", "gemini"])

    def test_parse_json_text_handles_fences(self):
        self.assertEqual(parse_json_text('```json\n{"a": 1}\n```'), {"a": 1})
        self.assertEqual(parse_json_text('Sure! {"a": 2} hope that helps'), {"a": 2})
        with self.assertRaises(ProviderError):
            parse_json_text("no json here")


class OfflineFitTest(unittest.TestCase):
    def test_offline_rules_always_pass_validation(self):
        from leadtime.concepts import load_concepts
        profiles = [PROFILE,
                    fit.normalise_profile({"sells": ["drink"], "equipment": ["blender", "fridge"], "price_band": "budget"}),
                    fit.normalise_profile({"sells": ["bakery", "dessert"], "equipment": [], "price_band": "premium"})]
        for c in load_concepts():
            for p in profiles:
                out = fit.offline_fit({"concept": c, "profile": p})
                fit.make_validator(c, p)(out)


if __name__ == "__main__":
    unittest.main()
