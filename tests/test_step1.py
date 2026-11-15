"""Step 1 tests for SH Ads Desk (MOCK build). unittest style — runs under
both `python3 -m pytest tests/` and `python3 -m unittest discover tests`."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import mock_insights
from app import optimiser
from app import policy_checker
from app.approval_queue import ApprovalQueue
from app.common import load_eligibility, load_settings
from app.mock_meta import MockMetaClient
from app.rollback import rollback_last_change

BASE_SETTINGS = load_settings()


def settings(**overrides):
    s = dict(BASE_SETTINGS)
    s.update(overrides)
    return s


TEST_SETTINGS = settings(
    TOTAL_DAILY_BUDGET_CAP=10000, PER_CAMPAIGN_CAP=6000, LIFETIME_CAP=100000,
    TARGET_COST_PER_QUALIFIED_LEAD=200, MIN_SPEND=1000, MIN_EVENTS=20,
    EVALUATION_WINDOW_DAYS=7, CONVERSION_LAG_WINDOW_DAYS=7,
    MAX_BUDGET_CHANGE_PCT=20, MIN_DAYS_BETWEEN_CHANGES=3,
)


class TestEligibilityGate(unittest.TestCase):
    def test_unknown_product_fails_closed(self):
        result = policy_checker.check_product("Totally Unknown Product XYZ")
        self.assertFalse(result["allowed"])
        self.assertTrue(any("NOT listed" in r for r in result["reasons"]))

    def test_listed_product_with_permission_false_is_blocked(self):
        eligibility = load_eligibility()
        names = [e["product"] for e in eligibility]
        self.assertIn("Brain.fm", names)  # catalog is loaded
        result = policy_checker.check_product("Brain.fm", eligibility)
        self.assertFalse(result["allowed"])
        self.assertTrue(any("resale_permission_confirmed" in r for r in result["reasons"]))

    def test_all_catalog_entries_default_false(self):
        for entry in load_eligibility():
            self.assertIs(entry["resale_permission_confirmed"], False, entry["product"])
            self.assertEqual(entry["supplier"], "")


class TestBannedClaims(unittest.TestCase):
    def test_banned_claims_blocked(self):
        text = ("Guaranteed lifetime access! Official partner — 90% off, "
                "earn 50000 every month, 100% result, best in India!")
        result = policy_checker.check_claims(text)
        self.assertFalse(result["allowed"])
        self.assertGreaterEqual(len(result["reasons"]), 3)

    def test_clean_copy_passes_claims(self):
        text = ("Apna AI toolkit ek jagah ready karo — Software Hub par "
                "collections dekho aur apne kaam ke hisaab se chuno.")
        result = policy_checker.check_claims(text)
        self.assertTrue(result["allowed"], result["reasons"])

    def test_destination_gate_closed_by_default(self):
        result = policy_checker.check_destination(BASE_SETTINGS)
        self.assertFalse(result["allowed"])


class TestOptimiser(unittest.TestCase):
    def test_thin_data_not_enough(self):
        report = optimiser.analyse(mock_insights.get_dataset("thin_data"), TEST_SETTINGS)
        self.assertFalse(report["safety_stop"])
        self.assertEqual(report["proposals"], [])
        for verdict in report["per_ad"].values():
            self.assertEqual(verdict["verdict"], "not enough data")

    def test_one_big_winner_budget_proposal(self):
        report = optimiser.analyse(mock_insights.get_dataset("one_big_winner"), TEST_SETTINGS)
        increases = [p for p in report["proposals"] if p["type"] == "PROPOSE_BUDGET_INCREASE"]
        self.assertEqual(len(increases), 1)
        prop = increases[0]
        self.assertEqual(prop["ad_id"], "win_1")
        # Budget target is the ad-set (budget-owning) object, never the ad.
        self.assertEqual(prop["target_object"], "mock_adset_win")
        self.assertNotEqual(prop["target_object"], prop["ad_id"])
        self.assertIn("1000", prop["budget_effect"])
        self.assertIn("1200", prop["budget_effect"])  # +20% cap applied
        self.assertEqual(report["per_ad"]["win_1"]["verdict"], "winner")

    def test_all_losers_get_pause_proposals(self):
        report = optimiser.analyse(mock_insights.get_dataset("all_losers"), TEST_SETTINGS)
        pauses = [p for p in report["proposals"] if p["type"] == "PROPOSE_PAUSE"]
        self.assertEqual(len(pauses), 3)

    def test_cheap_junk_is_a_loser(self):
        report = optimiser.analyse(mock_insights.get_dataset("cheap_junk_leads"), TEST_SETTINGS)
        self.assertEqual(report["per_ad"]["junk_1"]["verdict"], "loser — cheap but junk leads")
        self.assertTrue(any(p["ad_id"] == "junk_1" and p["type"] == "PROPOSE_PAUSE"
                            for p in report["proposals"]))

    def test_lagged_conversions_not_judged(self):
        report = optimiser.analyse(mock_insights.get_dataset("lagged_conversions"), TEST_SETTINGS)
        self.assertEqual(report["proposals"], [])
        for verdict in report["per_ad"].values():
            self.assertIn("lag window", verdict["verdict"])

    def test_spend_breach_triggers_safety_stop(self):
        report = optimiser.analyse(mock_insights.get_dataset("spend_breach"), TEST_SETTINGS)
        self.assertTrue(report["safety_stop"])
        self.assertTrue(any(p["type"] == "SAFETY_STOP" for p in report["proposals"]))

    def test_fatigue_proposes_creative_refresh(self):
        report = optimiser.analyse(mock_insights.get_dataset("fatigue"), TEST_SETTINGS)
        self.assertTrue(any(p["type"] == "PROPOSE_CREATIVE_REFRESH"
                            for p in report["proposals"]))


class TestMockMetaIdempotency(unittest.TestCase):
    def test_duplicate_retry_creates_no_duplicate(self):
        client = MockMetaClient()
        first = client.create_campaign("Camp A", idempotency_key="key-1")
        second = client.create_campaign("Camp A", idempotency_key="key-1")
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(client.count("campaign"), 1)

    def test_per_ad_budget_write_is_rejected(self):
        client = MockMetaClient()
        camp = client.create_campaign("C", idempotency_key="k-c")
        adset = client.create_adset(camp["id"], "AS", idempotency_key="k-as")
        ad = client.create_ad(adset["id"], "AD", "text", idempotency_key="k-ad")
        with self.assertRaises(ValueError):
            client.set_budget(ad["id"], 500)


class TestRollbackAndKillSwitch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "state.db")

    def test_rollback_restores_previous_budget(self):
        client = MockMetaClient()
        camp = client.create_campaign("C", idempotency_key="r-c", budget=1000)
        client.set_budget(camp["id"], 1500)
        blocked = rollback_last_change(client, camp["id"], approved=False, db_path=self.db)
        self.assertFalse(blocked["ok"])  # approval required first
        self.assertEqual(client.get_object(camp["id"])["budget"], 1500)
        done = rollback_last_change(client, camp["id"], approved=True, db_path=self.db)
        self.assertTrue(done["ok"])
        self.assertEqual(done["diff"]["current_value"], 1500)
        self.assertEqual(done["diff"]["restore_value"], 1000)
        self.assertEqual(client.get_object(camp["id"])["budget"], 1000)

    def test_kill_switch_pauses_everything_and_disables_automation(self):
        queue = ApprovalQueue(db_path=self.db)
        client = MockMetaClient()
        camp = client.create_campaign("C", idempotency_key="ks-c")
        client.set_status(camp["id"], "ACTIVE")
        result = queue.engage_kill_switch("test", mock_client=client)
        self.assertTrue(result["kill_switch"])
        self.assertFalse(result["automation_enabled"])
        self.assertTrue(queue.kill_switch_active())
        self.assertFalse(queue.automation_enabled())
        self.assertEqual(client.get_object(camp["id"])["status"], "PAUSED")

    def test_approval_queue_flow(self):
        queue = ApprovalQueue(db_path=self.db)
        item = queue.add_item("PROPOSE_PAUSE", {"ad_id": "x"})
        self.assertEqual(len(queue.list_pending()), 1)
        queue.edit_item(item, {"ad_id": "y"})
        self.assertEqual(queue.get_payload(item)["ad_id"], "y")
        queue.approve(item)
        self.assertEqual(queue.status(item), "APPROVED")
        self.assertEqual(queue.list_pending(), [])


if __name__ == "__main__":
    unittest.main()
