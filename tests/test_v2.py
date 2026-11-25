"""V2 module tests — readiness, creative matrix, test lane, fatigue,
subscription disclosure. All pure functions; no Meta writes anywhere."""
import unittest

from app import creative_matrix, fatigue, subscription_disclosure, test_lane, v2_readiness


class ReadinessTests(unittest.TestCase):
    def test_ready_band(self):
        out = v2_readiness.readiness_audit({
            "conversions_per_week": 60, "distinct_creatives": 6,
            "pixel_ok": True, "capi_ok": True,
            "daily_budget": 3000, "target_cpa": 500})
        self.assertEqual(out["band"], "advantage_plus_ready")
        self.assertGreaterEqual(out["score"], 70)

    def test_tracking_missing_fails_closed(self):
        out = v2_readiness.readiness_audit({"conversions_per_week": 100})
        self.assertEqual(out["band"], "fix_tracking_first")

    def test_low_volume_testing_lane(self):
        out = v2_readiness.readiness_audit({
            "conversions_per_week": 5, "distinct_creatives": 2,
            "pixel_ok": True, "capi_ok": True,
            "daily_budget": 400, "target_cpa": 500})
        self.assertEqual(out["band"], "testing_lane_first")
        self.assertIn("guarantee", out)


class CreativeMatrixTests(unittest.TestCase):
    def test_matrix_builds_distinct_briefs(self):
        out = creative_matrix.build_matrix(
            "software_digital", "AI Toolkit",
            facts=["Official price proof recorded 2026-11-20"],
            personas=["students", "freelancers"])
        self.assertTrue(out["briefs"])
        self.assertGreater(out["diversity_score"], 0)
        for brief in out["briefs"]:
            self.assertEqual(brief["facts_used"],
                             ["Official price proof recorded 2026-11-20"])

    def test_missing_facts_warns(self):
        out = creative_matrix.build_matrix("software_digital", "AI Toolkit")
        self.assertTrue(any("fact" in w for w in out["warnings"]))

    def test_similarity(self):
        self.assertEqual(creative_matrix.similarity("a b c", "a b c"), 1.0)
        self.assertEqual(creative_matrix.similarity("a b", "x y"), 0.0)


class TestLaneTests(unittest.TestCase):
    def test_cells_funded_by_budget(self):
        out = test_lane.plan_cells(target_cpa=500, daily_budget=3000,
                                   creative_count=5)
        self.assertEqual(len(out["cells"]), 3)  # threshold 1000 each

    def test_budget_below_threshold_refuses(self):
        out = test_lane.plan_cells(target_cpa=500, daily_budget=300,
                                   creative_count=3)
        self.assertEqual(out["cells"], [])
        self.assertTrue(out["warnings"])

    def test_kill_and_graduate_are_proposals(self):
        kill = test_lane.judge_cell(spend=1200, conversions=0,
                                    target_cpa=500, days_run=8)
        self.assertEqual(kill["decision"], "kill_proposal")
        grad = test_lane.judge_cell(spend=1200, conversions=4,
                                    target_cpa=500, days_run=8)
        self.assertEqual(grad["decision"], "graduate_proposal")

    def test_scale_steps_staged(self):
        steps = test_lane.scale_steps(1000, steps=2)
        self.assertEqual(steps[0]["proposed_budget"], 1150.0)
        self.assertEqual(steps[1]["proposed_budget"], 1322.5)


class FatigueTests(unittest.TestCase):
    def test_fatigued_band(self):
        rows = [{"ctr": 2.0, "frequency": 1.5, "cpm": 100, "hook_rate": 30},
                {"ctr": 1.7, "frequency": 2.4, "cpm": 115, "hook_rate": 27},
                {"ctr": 1.4, "frequency": 3.8, "cpm": 130, "hook_rate": 24}]
        out = fatigue.fatigue_score(rows)
        self.assertEqual(out["band"], "fatigued")
        self.assertGreaterEqual(out["score"], 60)

    def test_insufficient_data(self):
        out = fatigue.fatigue_score([{"ctr": 1.0}])
        self.assertEqual(out["band"], "insufficient_data")


class SubscriptionDisclosureTests(unittest.TestCase):
    def test_complete_disclosure_passes(self):
        out = subscription_disclosure.check_disclosure({
            "price_text": "₹999 per month, billed monthly",
            "cancellation_text": "Cancel anytime from settings",
            "collects_pii": True, "opt_in_unchecked": True})
        self.assertTrue(out["ok"])

    def test_missing_pieces_fail_closed(self):
        out = subscription_disclosure.check_disclosure({
            "price_text": "Best price", "cancellation_text": "",
            "collects_pii": True, "opt_in_unchecked": False})
        self.assertFalse(out["ok"])
        self.assertGreaterEqual(len(out["issues"]), 3)


if __name__ == "__main__":
    unittest.main()
