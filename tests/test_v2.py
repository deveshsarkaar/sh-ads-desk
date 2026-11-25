"""V2 module tests — readiness, creative matrix, test lane, fatigue,
subscription disclosure. All pure functions; no Meta writes anywhere."""
import unittest

from app import creative_matrix, fatigue, feed_catalog, subscription_disclosure, test_lane, v2_readiness


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


class FeedCatalogTests(unittest.TestCase):
    CSV = (
        "sku,product_name,mrp,offer_price,currency_code,stock_status,"
        "image_link,product_url,brand,category,permission_confirmed,"
        "proof_note,terms_checked_date\n"
        "SKU-1,Desk Lamp,1200,999,INR,in stock,"
        "https://example.com/lamp.jpg,https://example.com/lamp,"
        "Acme,Lighting,true,Supplier agreement on file,2026-11-25\n"
        "SKU-2,Blocked Item,500,,INR,in stock,"
        "https://example.com/blocked.jpg,https://example.com/blocked,"
        "Acme,Lighting,false,,\n")

    def test_csv_mapping_and_ad_ready_gate(self):
        out = feed_catalog.analyze_catalog(csv_text=self.CSV)
        self.assertEqual(out["total_items"], 2)
        self.assertEqual(out["feed_ready_count"], 2)
        self.assertEqual(out["ad_ready_count"], 1)
        ready = out["items"][0]
        self.assertTrue(ready["ad_ready"])
        self.assertEqual(ready["price_layers"][0]["text"], "INR 999")
        self.assertNotIn("% off", ready["price_layers"][0]["text"])
        self.assertEqual(len(out["video_briefs"]), 1)
        blocked = out["items"][1]
        self.assertFalse(blocked["ad_ready"])
        self.assertEqual(blocked["price_layers"], [])
        self.assertTrue(any("eligibility permission" in issue
                            for issue in blocked["issues"]))

    def test_profile_offerings_fail_closed_without_feed_fields(self):
        out = feed_catalog.analyze_inputs({}, offerings=[{
            "id": 7, "name": "Toolkit", "price": "999",
            "permission_confirmed": False,
        }], profile={"currency": "INR",
                      "website": "https://example.com"})
        self.assertEqual(out["source"], "profile_catalog")
        self.assertEqual(out["ad_ready_count"], 0)
        self.assertTrue(any("image URL" in issue
                            for issue in out["items"][0]["issues"]))


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
