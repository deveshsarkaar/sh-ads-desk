"""Industry-agnostic refactor tests: Business Profiles, industry presets,
generic offerings gate, Growth Loop transitions, Guardrails pre-flight,
Strategy Library / Knowledge / Policies registers.

Uses the same TempEnv pattern as test_full.py (temp DB + temp settings).
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_full import TempEnv  # noqa: E402

LOOP_SETTINGS = {
    "AUTOMATION_MODE": "PROPOSE", "DRY_RUN": True,
    "TOTAL_DAILY_BUDGET_CAP": 100000, "PER_CAMPAIGN_CAP": 60000,
    "TARGET_COST_PER_QUALIFIED_LEAD": 200, "MIN_SPEND": 1000,
    "MIN_EVENTS": 20, "EVALUATION_WINDOW_DAYS": 7,
    "CONVERSION_LAG_WINDOW_DAYS": 7, "MAX_BUDGET_CHANGE_PCT": 20,
    "MIN_DAYS_BETWEEN_CHANGES": 3, "DESTINATION_URL": "",
    "DESTINATION_READY": False, "LANGUAGES": ["Hinglish"],
}


def make_grocery(conn):
    from app import profiles
    return profiles.create_profile({
        "name": "Test Kirana", "industry_preset": "grocery_food",
        "website": "https://kirana.example", "currency": "INR",
    }, conn)


class TestProfiles(TempEnv):
    def test_software_hub_seeded_and_migration_lossless(self):
        from app import profiles
        from app.common import get_db
        conn = get_db(self.db)
        profile = profiles.get_active_profile(conn)
        self.assertEqual(profile["name"], "Software Hub")
        proof = profiles.migration_proof(conn, profile["id"])
        self.assertEqual(proof["source_count"], 33)
        self.assertEqual(proof["stored_count"], 33)
        self.assertTrue(proof["names_match"])
        self.assertTrue(proof["all_unconfirmed"])
        self.assertTrue(proof["lossless"], proof)

    def test_profile_create_switch_isolation(self):
        from app import profiles
        from app.common import get_db, load_settings
        conn = get_db(self.db)
        sh = profiles.get_active_profile(conn)
        grocery = make_grocery(conn)
        profiles.add_offering(grocery["id"],
                              {"name": "Aata 10kg", "type": "product"}, conn)
        profiles.add_offering(sh["id"],
                              {"name": "SH Only Tool", "type": "product"}, conn)
        g_names = [o["name"] for o in profiles.list_offerings(grocery["id"], conn)]
        s_names = [o["name"] for o in profiles.list_offerings(sh["id"], conn)]
        self.assertIn("Aata 10kg", g_names)
        self.assertNotIn("Aata 10kg", s_names)
        self.assertIn("SH Only Tool", s_names)
        self.assertNotIn("SH Only Tool", g_names)
        # Settings overrides don't leak either.
        profiles.update_profile(grocery["id"], {
            "settings_overrides": {"TOTAL_DAILY_BUDGET_CAP": 999}}, conn)
        grocery = profiles.get_profile(grocery["id"], conn)
        sh = profiles.get_profile(sh["id"], conn)
        g_eff = profiles.effective_settings(load_settings(), grocery)
        s_eff = profiles.effective_settings(load_settings(), sh)
        self.assertEqual(float(g_eff["TOTAL_DAILY_BUDGET_CAP"]), 999.0)
        self.assertNotEqual(float(s_eff.get("TOTAL_DAILY_BUDGET_CAP") or 0), 999.0)
        # Switch works and is recorded.
        profiles.set_active_profile(grocery["id"], conn)
        self.assertEqual(profiles.get_active_profile(conn)["id"], grocery["id"])

    def test_preset_seeding(self):
        from app import profiles
        from app.common import get_db, load_settings
        conn = get_db(self.db)
        profiles.get_active_profile(conn)
        grocery = make_grocery(conn)
        eff = profiles.effective_settings(load_settings(), grocery)
        self.assertTrue(eff.get("FUNNEL_STAGES"))
        self.assertTrue(eff.get("PRIMARY_KPI"))
        self.assertTrue(eff.get("LEAD_STAGES"))
        self.assertEqual(grocery["permission_label"],
                         "eligibility permission confirmed")
        self.assertEqual(eff.get("DESTINATION_URL"), "https://kirana.example")

    def test_all_eleven_presets_exist(self):
        from app import industries
        self.assertEqual(len(industries.PRESET_ORDER), 11)
        for key in industries.PRESET_ORDER:
            preset = industries.get_preset(key)
            self.assertTrue(preset["research_checklist"], key)
            self.assertTrue(preset["audience_hints"], key)
            self.assertGreaterEqual(len(preset["angle_templates"]), 3, key)


class TestGenericGate(TempEnv):
    def test_unconfirmed_grocery_offering_blocked_like_software(self):
        from app import policy_checker, profiles
        from app.common import get_db
        conn = get_db(self.db)
        profiles.get_active_profile(conn)
        grocery = make_grocery(conn)
        profiles.add_offering(grocery["id"],
                              {"name": "Aata 10kg", "type": "product"}, conn)
        eligibility = profiles.offerings_as_eligibility(grocery["id"], conn)
        result = policy_checker.check_product("Aata 10kg", eligibility)
        self.assertFalse(result["allowed"])
        self.assertTrue(any("eligibility permission confirmed" in r
                            for r in result["reasons"]), result["reasons"])
        # Confirmed with proof -> allowed (same gate, same strength).
        off = profiles.list_offerings(grocery["id"], conn)[0]
        profiles.update_offering(off["id"], {
            "permission_confirmed": True, "supplier": "LocalDist",
            "proof_note": "invoice", "terms_checked_date": "2026-11-16"}, conn)
        eligibility = profiles.offerings_as_eligibility(grocery["id"], conn)
        self.assertTrue(policy_checker.check_product("Aata 10kg", eligibility)["allowed"])

    def test_industry_pack_blocks_industry_claim(self):
        from app import industries, policy_checker
        health = industries.compliance_patterns("health_wellness")
        self.assertFalse(policy_checker.check_claims(
            "Ye cream har bimari ka guaranteed ilaaj hai, koi side effects nahi",
            health)["allowed"])
        edu = industries.compliance_patterns("education_courses")
        self.assertFalse(policy_checker.check_claims(
            "Admission lo — 100% placement guarantee ke saath", edu)["allowed"])
        # Pack-only claim: clean for the core checker, blocked by the pack.
        fin = industries.compliance_patterns("finance_insurance")
        text = "Is plan me assured returns milte hain, paisa safe hai"
        self.assertTrue(policy_checker.check_claims(text)["allowed"])
        self.assertFalse(policy_checker.check_claims(text, fin)["allowed"])

    def test_personal_attributes_union_enforced(self):
        from app import policy_checker
        self.assertFalse(policy_checker.check_claims(
            "Do you have diabetes? Ye product aapke liye hai")["allowed"])
        ok = policy_checker.check_claims(
            "Diabetes care ke liye nayi range available hai — details dekho")
        self.assertTrue(ok["allowed"], ok)


class TestReportsAndLoop(TempEnv):
    def test_report_header_shows_active_profile(self):
        from app import profiles, reports, store
        from app.common import get_db
        conn = get_db(self.db)
        profiles.get_active_profile(conn)
        grocery = make_grocery(conn)
        store.seed_insights("one_big_winner", conn=conn, profile_id=grocery["id"])
        rows = store.load_insight_rows(conn, profile_id=grocery["id"])
        out = reports.daily_report(rows, [], dict(LOOP_SETTINGS),
                                   profile=grocery)
        self.assertIn("Test Kirana", out)
        self.assertIn("Grocery", out)

    def _run_loop(self, dataset, settings=None):
        from app import growth_loop, profiles, store
        from app.approval_queue import ApprovalQueue
        from app.common import get_db
        conn = get_db(self.db)
        profile = profiles.get_active_profile(conn)
        store.seed_insights(dataset, conn=conn, profile_id=profile["id"])
        queue = ApprovalQueue()
        queue.conn = conn
        summary = growth_loop.run_cycle(
            conn=conn, settings=settings or dict(LOOP_SETTINGS),
            profile=profile, queue=queue)
        return conn, profile, queue, summary

    def test_loop_winner_gets_scale_proposal(self):
        conn, profile, queue, summary = self._run_loop("one_big_winner")
        types = [i["payload"].get("type")
                 for i in queue.list_pending(profile_id=profile["id"])]
        self.assertIn("PROPOSE_BUDGET_INCREASE", types)

    def test_loop_losers_get_pause_proposals(self):
        conn, profile, queue, summary = self._run_loop("all_losers")
        types = [i["payload"].get("type")
                 for i in queue.list_pending(profile_id=profile["id"])]
        self.assertIn("PROPOSE_PAUSE", types)
        self.assertNotIn("PROPOSE_BUDGET_INCREASE", types)

    def test_loop_fatigue_triggers_refresh_brief(self):
        from app import growth_loop
        conn, profile, queue, summary = self._run_loop("fatigue")
        growth_loop.add_top_creative(profile["id"], {
            "theme": "Subah ki fresh sabzi", "hook": "5 baje ki mandi",
            "format": "REEL", "cta_style": "Order Now",
            "source": "Meta Ad Library (manual note)",
            "source_date": "2026-11-15", "window_days": 7}, conn=conn)
        conn2, profile2, queue2, summary2 = self._run_loop("fatigue")
        refresh = summary2["stages"]["refresh"]
        self.assertTrue(refresh["triggered"], summary2["stages"])
        self.assertTrue(refresh["new_brief"])
        self.assertEqual(refresh["new_brief"]["theme"], "Subah ki fresh sabzi")

    def test_inspiration_brief_from_seeded_top_creative(self):
        from app import growth_loop, profiles
        from app.common import get_db
        conn = get_db(self.db)
        profile = profiles.get_active_profile(conn)
        growth_loop.add_top_creative(profile["id"], {
            "theme": "Toolkit reveal", "hook": "31 tools ek screen par",
            "format": "CAROUSEL", "cta_style": "Swipe karo",
            "source": "https://www.facebook.com/ads/library/?id=example",
            "source_date": "2026-11-14", "window_days": 7}, conn=conn)
        brief = growth_loop.inspiration_brief(profile["id"], 7, conn=conn)
        self.assertIsNotNone(brief)
        self.assertEqual(brief["theme"], "Toolkit reveal")
        self.assertIn("verbatim copy nahi hogi", brief["rule"])


class TestGuardrails(TempEnv):
    def _draft_ctx(self, **kw):
        from app import profiles
        from app.common import get_db, load_settings
        conn = get_db(self.db)
        profile = profiles.get_active_profile(conn)
        eligibility = profiles.offerings_as_eligibility(profile["id"], conn)
        ctx = {"kind": "draft", "product": "Brain.fm", "text": "Saaf copy hai",
               "settings": dict(LOOP_SETTINGS), "eligibility": eligibility,
               "extra_patterns": [], "profile": profile,
               "destination_url": "https://softwarehub.tech",
               "destination_ready": True, "kill_switch": False}
        ctx.update(kw)
        return conn, ctx

    def test_block_guardrail_refuses_queue_entry(self):
        from app import guardrails
        from app.approval_queue import ApprovalQueue
        conn, ctx = self._draft_ctx()  # Brain.fm is UNCONFIRMED
        result = guardrails.run_preflight(ctx, conn=conn)
        self.assertFalse(result["allowed"])
        self.assertTrue(any(b["check"] == "eligibility" for b in result["blocks"]))
        queue = ApprovalQueue()
        queue.conn = conn
        if result["allowed"]:  # mirrors the planner handler's logic
            queue.add_item("CAMPAIGN_DRAFT", {"kind": "CAMPAIGN_DRAFT"})
        self.assertEqual(queue.list_pending(), [])

    def test_warn_case_enters_with_warnings_attached(self):
        from app import guardrails, policy_checker, profiles
        from app.approval_queue import ApprovalQueue
        from app.common import get_db
        conn = get_db(self.db)
        profile = profiles.get_active_profile(conn)
        off = next(o for o in profiles.list_offerings(profile["id"], conn)
                   if o["name"] == "Brain.fm")
        profiles.update_offering(off["id"], {
            "permission_confirmed": True, "supplier": "S",
            "proof_note": "email", "terms_checked_date": "2026-11-16"}, conn)
        eligibility = profiles.offerings_as_eligibility(profile["id"], conn)
        settings = dict(LOOP_SETTINGS)
        settings["CREATIVES_PER_AD_SET_MIN"] = 3
        plan = {"ad_sets": [{"name": "a", "ads": [{"ad_name": "only-one"}]}]}
        ctx = {"kind": "draft", "product": "Brain.fm", "text": "Saaf copy",
               "settings": settings, "eligibility": eligibility,
               "extra_patterns": [], "profile": profile, "plan": plan,
               "destination_url": "https://softwarehub.tech",
               "destination_ready": True, "kill_switch": False}
        result = guardrails.run_preflight(ctx, conn=conn)
        self.assertTrue(result["allowed"], result["blocks"])
        self.assertTrue(result["warnings"])
        queue = ApprovalQueue()
        queue.conn = conn
        draft = {"kind": "CAMPAIGN_DRAFT",
                 "guardrail_warnings": [{"id": w["id"], "name": w["name"],
                                         "reason": w["reason"]}
                                        for w in result["warnings"]]}
        item_id = queue.add_item("CAMPAIGN_DRAFT", draft,
                                 profile_id=profile["id"])
        pending = queue.list_pending(profile_id=profile["id"])
        self.assertEqual(len(pending), 1)
        self.assertTrue(pending[0]["payload"]["guardrail_warnings"])

    def test_optimiser_never_proposes_blocked_action(self):
        from app import guardrails
        fatigued_row = {"ad_id": "fat_1", "frequency_end": 4.8,
                        "ctr_start": 3.0, "ctr_end": 0.9,
                        "days_since_launch": 10, "qualified_leads": 14,
                        "conversions": 14}
        proposal = {"type": "PROPOSE_BUDGET_INCREASE", "ad_id": "fat_1",
                    "action": "BUDGET_INCREASE", "pct": 10}
        verdict = guardrails.check_proposal(proposal, fatigued_row,
                                            dict(LOOP_SETTINGS))
        self.assertTrue(verdict["blocked"], verdict)
        self.assertTrue(any("fatigue" in r for r in verdict["reasons"]))

    def test_toggle_off_changes_outcome(self):
        from app import guardrails
        conn, ctx = self._draft_ctx()
        blocked = guardrails.run_preflight(ctx, conn=conn)
        self.assertFalse(blocked["allowed"])
        settings = dict(ctx["settings"])
        settings["GUARDRAILS_DISABLED"] = ["eligibility_unconfirmed",
                                           "D3", "D22"]
        ctx2 = dict(ctx)
        ctx2["settings"] = settings
        passed = guardrails.run_preflight(ctx2, conn=conn)
        self.assertTrue(passed["allowed"], passed["blocks"])

    def test_catalogue_seeded_d1_to_d26(self):
        from app import guardrails
        ids = [g["id"] for g in guardrails.load_registry()]
        for n in range(1, 27):
            self.assertIn("D%d" % n, ids)
        self.assertEqual(len(guardrails.PREFLIGHT_CHECKLIST), 8)


class TestRegisters(TempEnv):
    def test_knowledge_register_renders_with_sources(self):
        from app import trends
        self.assertGreaterEqual(len(trends.KNOWLEDGE_REGISTER), 10)
        for entry in trends.KNOWLEDGE_REGISTER:
            self.assertTrue(entry["url"].startswith("http"), entry)
            self.assertTrue(entry["date_read"], entry)
            self.assertIn("verified", entry)
        from app.web import pg_trends
        from app.common import get_db, load_settings
        from app.approval_queue import ApprovalQueue
        from app import profiles
        conn = get_db(self.db)
        profile = profiles.get_active_profile(conn)
        ctx = {"conn": conn, "settings": load_settings(), "profile": profile,
               "eligibility": [], "extra_patterns": [],
               "queue": ApprovalQueue(), "csrf_field": "", "flash": ""}
        ctx["queue"].conn = conn
        html = pg_trends(ctx)
        self.assertIn("Andromeda", html)
        self.assertIn("https://", html)
        self.assertIn("UNVERIFIED", html)
        self.assertIn("DISPUTED", html)

    def test_strategy_library_labels_and_screening(self):
        from app import strategy_library as sl
        damini = [e for e in sl.all_entries() if e["id"].startswith("S")]
        self.assertEqual(len(damini), 36)  # S1–S35 + S20-DNA split entry
        self.assertTrue(all("Damini Tripathi" in e["source"] for e in damini))
        dna = sl.get_entry("S20-DNA")
        self.assertEqual(dna["status"], "DO_NOT_APPLY")
        self.assertEqual(sl.get_entry("D4")["status"], "DO_NOT_APPLY")
        self.assertEqual(sl.get_entry("W1")["status"], "ACTIVE")
        self.assertEqual(sl.get_entry("V1")["status"], "ACTIVE")
        # Her unverified course numbers must NOT appear as benchmarks.
        blob = " ".join(e["summary"] for e in sl.all_entries())
        self.assertNotIn("1.2x", blob)
        self.assertNotIn("4.8x", blob)

    def test_youtube_video_strategies_seeded_and_screened(self):
        from app import strategy_library as sl
        yt = [e for e in sl.all_entries() if e["id"].startswith("YT")]
        # YT1 x8 + YT2 x7 + YT3 x8 + YT-DNA screening entry
        self.assertEqual(len(yt), 24)
        self.assertEqual(len([e for e in yt if e["id"].startswith("YT1-")]), 8)
        self.assertEqual(len([e for e in yt if e["id"].startswith("YT2-")]), 7)
        self.assertEqual(len([e for e in yt if e["id"].startswith("YT3-")]), 8)
        for e in yt:
            self.assertIn("youtu", e["source_url"])
            self.assertEqual(e["date_read"], "2026-11-16")
        self.assertIn("Sabri Suby", sl.get_entry("YT1-1")["source"])
        self.assertIn("HBA Services", sl.get_entry("YT2-1")["source"])
        self.assertIn("WsCube Tech", sl.get_entry("YT3-1")["source"])
        self.assertEqual(sl.get_entry("YT-DNA")["status"], "DO_NOT_APPLY")
        self.assertEqual(sl.get_entry("YT1-1")["status"], "ACTIVE")
        # Creators' earnings claims must not appear as benchmarks.
        blob = " ".join(e["summary"] for e in yt)
        self.assertNotIn("million", blob.lower())

    def test_policies_register_flags_preserved(self):
        from app import policies_register as pr
        self.assertEqual(len(pr.POLICIES), 10)
        terms = next(p for p in pr.POLICIES if p["id"] == "PR9")
        self.assertEqual(terms["status"], "CONTESTED")
        self.assertIn("DISPUTED", terms["note"])
        self.assertIn("age", pr.PERSONAL_ATTRIBUTES_UNION)
        self.assertIn("family status", pr.PERSONAL_ATTRIBUTES_UNION)
        self.assertIn("national origin", pr.PERSONAL_ATTRIBUTES_UNION)


if __name__ == "__main__":
    unittest.main()
