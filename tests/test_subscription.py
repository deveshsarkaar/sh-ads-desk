"""Subscription vertical training pack (2026-11-20).

Guards the SUB-* strategy entries, the Subscription Business
Profile module, the competitor-board seeds, and — most important —
the guardrails the pack must never move: eligibility stays
unconfirmed, AUTOMATION_MODE stays PROPOSE, DRY_RUN stays on, and
no seller marketing numbers leak in as benchmarks.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestSubscriptionStrategies(unittest.TestCase):
    def test_sub_entries_seeded_and_labelled(self):
        from app import strategy_library as sl
        subs = [e for e in sl.all_entries() if e["id"].startswith("SUB-")]
        active = [e for e in subs if e["status"] == "ACTIVE"]
        dna = [e for e in subs if e["status"] == "DO_NOT_APPLY"]
        self.assertEqual(len(active), 12)          # SUB-1 .. SUB-12
        self.assertEqual(len(dna), 2)              # SUB-DNA1, SUB-DNA2
        for e in subs:
            self.assertIn("Subscription vertical research", e["source"])
            self.assertEqual(e["date_read"], "2026-11-20")

    def test_sub_screening_entries(self):
        from app import strategy_library as sl
        self.assertEqual(sl.get_entry("SUB-DNA1")["status"], "DO_NOT_APPLY")
        self.assertEqual(sl.get_entry("SUB-DNA2")["status"], "DO_NOT_APPLY")
        self.assertEqual(sl.get_entry("SUB-11")["status"], "ACTIVE")
        blob = " ".join(e["summary"] for e in sl.all_entries()
                        if e["id"].startswith("SUB-") and e["status"] == "ACTIVE")
        # No winner/performance language may leak into active entries.
        for banned in ("CTR", "CPC", "ROAS", "conversion rate of"):
            self.assertNotIn(banned, blob)


class TestSubscriptionProfile(unittest.TestCase):
    def test_profile_loads_with_core_sections(self):
        from app import subscription_profile as sp
        prof = sp.load()
        self.assertEqual(prof["slug"], "subscription-business")
        fams = {f["family"] for f in prof["product_families"]}
        for expected in ("Canva Pro", "ChatGPT Plus",
                         "Gemini AI Pro (Google AI Pro)",
                         "CapCut Pro", "Netflix / OTT bundles",
                         "Spotify Premium", "Telegram Premium"):
            self.assertIn(expected, fams)
        self.assertEqual(len(prof["creative_patterns"]), 10)  # T1-T10
        self.assertTrue(prof["compliance_do"])
        self.assertTrue(prof["compliance_dont"])
        self.assertTrue(prof["coverage_limits"])

    def test_profile_accessors(self):
        from app import subscription_profile as sp
        self.assertEqual(sp.product_family("canva pro")["family"], "Canva Pro")
        self.assertIsNone(sp.product_family("no such product"))
        self.assertEqual(sp.creative_pattern("T2")["name"],
                         "Official-vs-ours strike-through")
        self.assertIsNone(sp.creative_pattern("T99"))

    def test_profile_carries_no_invented_metrics(self):
        from app import subscription_profile as sp
        blob = str(sp.load())
        for banned in ("CTR", "CPC", "ROAS", "cost per lead of"):
            self.assertNotIn(banned, blob)


class TestCompetitorSeeds(unittest.TestCase):
    def test_vertical_seeds_present_with_honesty_notes(self):
        from app import competitor_seeds
        seeds = competitor_seeds.seeded_for("software-hub")
        names = {s["name"] for s in seeds}
        for expected in ("Tradeello", "OTT Services BD", "SubsHub",
                         "AcademicTools", "GroupAITools", "OTTSeller"):
            self.assertIn(expected, names)
        for s in seeds:
            if "subscription-vertical" in s.get("tags", []):
                self.assertIn("UNMEASURED", s["followers_note"])
                self.assertTrue(s["ad_library_url"].startswith(
                    "https://www.facebook.com/ads/library/"))


class TestGuardrailsUntouched(unittest.TestCase):
    def test_eligibility_still_all_unconfirmed(self):
        text = (ROOT / "PRODUCT_ELIGIBILITY.yaml").read_text()
        self.assertNotIn("resale_permission_confirmed: true", text)
        self.assertIn("resale_permission_confirmed: false", text)

    def test_settings_still_propose_and_dry_run(self):
        yaml_text = (ROOT / "settings.yaml").read_text()
        self.assertIn("DRY_RUN: true", yaml_text)
        self.assertIn('AUTOMATION_MODE: "PROPOSE"', yaml_text)
        json_text = (ROOT / "settings.json").read_text()
        self.assertIn('"AUTOMATION_MODE": "PROPOSE"', json_text)
        self.assertIn('"DRY_RUN": true', json_text)


if __name__ == "__main__":
    unittest.main()
