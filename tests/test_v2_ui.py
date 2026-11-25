"""V2 Desk UI tests: background job stores results, page renders in
English only, workspace customization persists per profile."""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class V2UITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._old = {k: os.environ.get(k) for k in
                     ("SH_ADS_DB_PATH", "SH_ADS_SETTINGS_PATH", "META_MODE")}
        os.environ["SH_ADS_DB_PATH"] = os.path.join(self.tmp, "state.db")
        os.environ["SH_ADS_SETTINGS_PATH"] = os.path.join(
            self.tmp, "settings.json")
        with open(os.environ["SH_ADS_SETTINGS_PATH"], "w",
                  encoding="utf-8") as f:
            json.dump({"AUTOMATION_MODE": "PROPOSE", "DRY_RUN": True}, f)
        from app.common import get_db, load_settings
        from app import profiles as profiles_mod
        self.conn = get_db()
        profiles_mod.ensure_seeded(self.conn)
        self.profile = profiles_mod.get_active_profile(self.conn)
        self.settings = profiles_mod.effective_settings(
            load_settings(), self.profile)

    def tearDown(self):
        for k, v in self._old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _ctx(self, settings=None):
        return {"conn": self.conn, "settings": settings or self.settings,
                "profile": self.profile, "flash": "",
                "csrf_field": '<input type="hidden" name="csrf" value="t">'}

    def test_v2_job_stores_results(self):
        from app import v2_jobs
        pid = self.profile["id"]
        v2_jobs.save_inputs(self.conn, pid, {
            "conversions_per_week": 60, "distinct_creatives": 6,
            "daily_budget": 3000, "target_cpa": 500,
            "pixel_ok": True, "capi_ok": True,
            "offering_name": "AI Toolkit", "facts": ["Price proof recorded"],
            "catalog_csv_text": (
                "id,title,price,currency,availability,image_url,link,"
                "permission_confirmed,proof_note,terms_checked_date\n"
                "SKU-1,Desk Lamp,999,INR,in stock,"
                "https://example.com/lamp.jpg,https://example.com/lamp,"
                "true,Supplier agreement on file,2026-11-25\n"),
            "price_text": "Rs 999 per month", "cancellation_text": "Cancel anytime",
            "collects_pii": True, "opt_in_unchecked": True})
        results = v2_jobs.run_v2(self.conn, pid)
        self.assertEqual(results["readiness"]["band"],
                         "advantage_plus_ready")
        self.assertTrue(results["disclosure"]["ok"])
        self.assertEqual(results["feed_catalog"]["ad_ready_count"], 1)
        stored = v2_jobs.load_results(self.conn, pid)
        self.assertEqual(stored["ran_at"], results["ran_at"])

    def test_v2_page_renders_english_only(self):
        from app import v2_jobs
        from app.web import pg_v2
        pid = self.profile["id"]
        v2_jobs.save_inputs(self.conn, pid, {
            "conversions_per_week": 60, "distinct_creatives": 6,
            "daily_budget": 3000, "target_cpa": 500,
            "pixel_ok": True, "capi_ok": True,
            "offering_name": "AI Toolkit", "facts": []})
        v2_jobs.run_v2(self.conn, pid)
        html = pg_v2(self._ctx())
        self.assertIn("V2 Desk", html)
        self.assertIn("Run in background", html)
        self.assertIn("Advantage+ Readiness", html)
        for hinglish in ("Pehle", "karo", "chahiye", "mat jodo", "banao"):
            self.assertNotIn(hinglish, html)

    def test_agency_page_shows_feed_catalog(self):
        from app import v2_jobs
        from app.web import pg_v2
        pid = self.profile["id"]
        v2_jobs.save_inputs(self.conn, pid, {
            "catalog_csv_text": (
                "id,title,price,currency,availability,image_url,link,"
                "permission_confirmed,proof_note,terms_checked_date\n"
                "SKU-1,Desk Lamp,999,INR,in stock,"
                "https://example.com/lamp.jpg,https://example.com/lamp,"
                "true,Supplier agreement on file,2026-11-25\n")})
        v2_jobs.run_v2(self.conn, pid)
        agency = dict(self.settings, V2_MODE="agency")
        html = pg_v2(self._ctx(settings=agency))
        self.assertIn("Feed & Catalog", html)
        self.assertIn("Catalog CSV", html)
        self.assertIn("1/1 ad-ready", html)

    def test_v2_run_queues_background_job(self):
        from app import v2_jobs
        from app.web import post_v2_run
        msg = post_v2_run(self._ctx(), {
            "conversions_per_week": "60", "distinct_creatives": "6",
            "daily_budget": "3000", "target_cpa": "500",
            "pixel_ok": "on", "capi_ok": "on", "offering_name": "Toolkit"})
        self.assertIn("background", msg)
        self.assertTrue(v2_jobs.v2_pending(self.conn, self.profile["id"]))

    def test_nav_simplifies_by_mode(self):
        from app.web import pg_v2
        customer = dict(self.settings, V2_MODE="customer")
        html = pg_v2(self._ctx(settings=customer))
        self.assertNotIn('href="/guardrails"', html)
        self.assertIn('href="/v2"', html)
        enterprise = dict(self.settings, V2_MODE="enterprise")
        html = pg_v2(self._ctx(settings=enterprise))
        self.assertIn('href="/guardrails"', html)

    def test_background_chip_shows_when_job_pending(self):
        from app import job_queue
        from app.web import pg_v2
        job_queue.enqueue("v2", profile_id=self.profile["id"],
                          conn=self.conn)
        html = pg_v2(self._ctx())
        self.assertIn("Background:", html)

    def test_audit_csv_export(self):
        from app.common import audit
        from app.web import audit_csv_text
        audit(self.conn, "enterprise_check", "audit export test row")
        text = audit_csv_text(self.conn)
        self.assertIn("id,event,detail,created_at", text)
        self.assertIn("enterprise_check", text)

    def test_expert_verdicts_use_evidence_thresholds(self):
        from app import expert_engine
        rows = [
            {"ad_id": "win", "spend": 5000, "qualified_leads": 80},
            {"ad_id": "dead", "spend": 2000, "qualified_leads": 0},
            {"ad_id": "lag", "spend": 2000, "qualified_leads": 0,
             "conversions_lagged_pending": True},
            {"ad_id": "new", "spend": 100, "qualified_leads": 1},
        ]
        verdicts = {v["ad_id"]: v["verdict"]
                    for v in expert_engine.campaign_verdicts(rows, 500)}
        self.assertEqual(verdicts["win"], "scale_candidate")
        self.assertEqual(verdicts["dead"], "stop_candidate")
        self.assertEqual(verdicts["lag"], "hold")
        self.assertEqual(verdicts["new"], "insufficient_data")

    def test_expert_audit_and_review_in_v2_results(self):
        from app import expert_engine, v2_jobs
        audit = expert_engine.expert_audit({
            "pixel_ok": True, "capi_ok": True, "distinct_creatives": 6,
            "daily_budget": 5000, "target_cpa": 500,
            "conversions_per_week": 60})
        self.assertEqual(audit["grade"], "A")
        results = v2_jobs.run_v2(self.conn, self.profile["id"])
        self.assertIn("expert", results)
        self.assertIn("guarantee", results["expert"]["note"].lower()
                      .replace("does not guarantee", "guarantee"))

    def test_customize_persists_per_profile(self):
        from app import profiles as profiles_mod
        from app.web import post_v2_customize
        msg = post_v2_customize(self._ctx(), {
            "mode": "agency", "module_readiness": "on",
            "module_fatigue": "on"})
        self.assertIn("saved", msg)
        fresh = profiles_mod.get_profile(self.profile["id"], self.conn)
        self.assertEqual(fresh["settings_overrides"]["V2_MODE"], "agency")
        self.assertEqual(fresh["settings_overrides"]["V2_MODULES"],
                         ["readiness", "fatigue"])


if __name__ == "__main__":
    unittest.main()
