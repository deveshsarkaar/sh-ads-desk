"""Growth Loop — SH Ads Desk (industry-agnostic build).

The owner's exact operating loop, run per active business profile:

  1. competitor_discovery   — maintain the profile's competitor list
  2. competitor_ads_research — which competitor ads run longest/best
                               (public Meta Ad Library ONLY, within its
                               terms; every finding carries source+date;
                               where live access is not wired, the stage
                               records an honest research task — metrics
                               are NEVER fabricated)
  3. top_creative_inspiration — top creatives of the last 7/10 days
                               (configurable window) become an
                               inspiration brief: theme, hook, format,
                               CTA style. INSPIRATION ONLY — never copy
                               another advertiser's ad verbatim, never
                               reuse their assets or text.
  4. creative_production     — brief to creative set via templates +
                               API providers; eligibility/policy/
                               destination gates unchanged
  5. optimisation_plan       — Role 19 analysis per PRACTICES.md
  6. go_live                 — PROPOSE mode (default): proposals wait in
                               the approval queue. AUTO_WITHIN_RULES:
                               only when the owner has approved written
                               rules + caps in settings; a safety stop
                               is NEVER auto-applied or auto-resumed,
                               and the kill switch blocks everything
  7. monitoring              — per-creative winners vs losers (weak CTA
                               = falling CTR, high spend, low responses)
  8. refresh                 — fatigue/decay on winners too, so a fresh
                               inspiration brief restarts the loop

One full cycle runs on MOCK data via `python -m app.jobs loop` or the
Growth Loop page. Every stage run is recorded in loop_runs (visible on
the page: current stage, last run per stage, loop history).
"""
import json
from datetime import date

from . import creative as creative_mod
from . import optimiser as optimiser_mod
from . import profiles as profiles_mod
from . import store
from . import strategy_library
from .approval_queue import ApprovalQueue
from .common import _now, audit, get_db, log_role_run
from .execute import execute_approved_item

STAGES = [
    ("competitor_discovery", "1 · Competitor discovery"),
    ("competitor_ads_research", "2 · Competitor best-ads research"),
    ("top_creative_inspiration", "3 · Top-creative inspiration (7/10 din)"),
    ("creative_production", "4 · Creative production"),
    ("optimisation_plan", "5 · Optimisation plan"),
    ("go_live", "6 · Go-live (approval-gated / AUTO_WITHIN_RULES)"),
    ("monitoring", "7 · Monitoring — winners vs losers"),
    ("refresh", "8 · Refresh — naye creatives (loop restart)"),
]
STAGE_KEYS = [k for k, _label in STAGES]

AD_LIBRARY_SOURCE = "Meta Ad Library (public) — https://www.facebook.com/ads/library"


def record_stage(conn, profile_id, stage, detail):
    conn.execute(
        "INSERT INTO loop_runs (profile_id, stage, detail, created_at) "
        "VALUES (?, ?, ?, ?)",
        (profile_id, stage, json.dumps(detail, ensure_ascii=False, default=str),
         _now()))
    conn.commit()


def loop_status(conn=None, profile_id=None):
    """Current stage per profile + last run per stage + history."""
    conn = conn or get_db()
    if profile_id is None:
        profile = profiles_mod.get_active_profile(conn)
        profile_id = profile["id"] if profile else 0
    last = {}
    for r in conn.execute(
            "SELECT stage, detail, created_at FROM loop_runs WHERE profile_id = ? "
            "ORDER BY id", (profile_id,)).fetchall():
        last[r["stage"]] = {"detail": r["detail"], "at": r["created_at"]}
    history = conn.execute(
        "SELECT stage, detail, created_at FROM loop_runs WHERE profile_id = ? "
        "ORDER BY id DESC LIMIT 40", (profile_id,)).fetchall()
    current = None
    for key in STAGE_KEYS:
        if key not in last:
            current = key
            break
    if current is None and last:
        current = "refresh (loop dobara chalega)"
    stages = [{"key": key, "label": label,
               "last_run": last.get(key, {}).get("at"),
               "detail": last.get(key, {}).get("detail")}
              for key, label in STAGES]
    return {"profile_id": profile_id, "current_stage": current or STAGE_KEYS[0],
            "stages": stages,
            "history": [{"stage": h["stage"], "detail": h["detail"],
                         "at": h["created_at"]} for h in history]}


# ------------------------------------------------------------ top creatives
def add_top_creative(profile_id, data, conn=None):
    conn = conn or get_db()
    cur = conn.execute(
        "INSERT INTO top_creatives (profile_id, theme, hook, format, cta_style, "
        "source, source_date, window_days, score_note, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (profile_id, data.get("theme", ""), data.get("hook", ""),
         data.get("format", ""), data.get("cta_style", ""),
         data.get("source", ""), data.get("source_date", "") or str(date.today()),
         int(data.get("window_days") or 7), data.get("score_note", ""), _now()))
    conn.commit()
    return cur.lastrowid


def list_top_creatives(profile_id, conn=None):
    conn = conn or get_db()
    rows = conn.execute(
        "SELECT * FROM top_creatives WHERE profile_id = ? ORDER BY id DESC",
        (profile_id,)).fetchall()
    return [dict(r) for r in rows]


def inspiration_brief(profile_id, window_days=7, conn=None, profile=None):
    """Build an inspiration brief from the profile's top-creative
    records inside the window. Inspiration ONLY: theme/hook/format/CTA
    style patterns — never another advertiser's copy or assets.
    Falls back to the best-performing angle in the (MOCK) insight rows,
    labelled as such. Returns None when there is no source at all."""
    conn = conn or get_db()
    window_days = 10 if int(window_days or 7) == 10 else 7
    rows = list_top_creatives(profile_id, conn)
    in_window = [r for r in rows if int(r.get("window_days") or 7) <= window_days]
    if in_window:
        top = in_window[0]
        return {
            "theme": top["theme"], "hook": top["hook"],
            "format": top["format"] or "REEL", "cta_style": top["cta_style"],
            "window_days": window_days,
            "source": top["source"] or "owner-recorded top creative",
            "source_date": top["source_date"],
            "score_note": top["score_note"],
            "basis": "top-creative record #%s" % top["id"],
            "rule": "INSPIRATION ONLY — theme/hook/format/CTA pattern "
                    "seekho; kisi aur advertiser ki ad verbatim copy "
                    "nahi hogi, unke assets/text reuse nahi honge.",
        }
    insight_rows = store.load_insight_rows(conn, profile_id=profile_id)
    if insight_rows:
        best, best_cpq = None, None
        for r in insight_rows:
            q = int(r.get("qualified_leads") or 0)
            if q:
                cpq = float(r.get("spend") or 0) / q
                if best_cpq is None or cpq < best_cpq:
                    best, best_cpq = r, cpq
        if best is not None:
            return {
                "theme": "Apna winning angle: %s" % best.get("angle", "generic"),
                "hook": "Winning ad %s ke hook pattern par naya hook "
                        "(3-second rule — hook pehle 3 second me)" % best.get("ad_id"),
                "format": (best.get("format") or "reel").upper(),
                "cta_style": "One specific CTA (Strategy S15)",
                "window_days": window_days,
                "source": "MOCK insight rows (apna data) — koi bahari ad copy nahi hua",
                "source_date": str(date.today()),
                "score_note": "cost per qualified lead %s (MOCK)" % round(best_cpq, 2),
                "basis": "own insight rows",
                "rule": "INSPIRATION ONLY — apne winning pattern se seekho; "
                        "bahari ad kabhi copy nahi hoti.",
            }
    return None


# ---------------------------------------------------------------- the cycle
def _auto_rules_ok(settings):
    """AUTO_WITHIN_RULES go-live needs ALL of: the mode set, the owner's
    written rules text present, and the owner's explicit rules-approved
    flag. Anything missing => PROPOSE behaviour."""
    return (settings.get("AUTOMATION_MODE") == "AUTO_WITHIN_RULES"
            and settings.get("AUTO_RULES_APPROVED") is True
            and bool(str(settings.get("AUTO_RULES_TEXT") or "").strip()))


def run_cycle(conn=None, settings=None, profile=None, queue=None):
    """Advance ONE full loop cycle for a profile on the stored (MOCK)
    insight rows. Returns a summary dict. Nothing here weakens a gate:
    creative production still passes the policy checker; go-live still
    goes through the approval queue / execute path."""
    conn = conn or get_db()
    profile = profile or profiles_mod.get_active_profile(conn)
    if profile is None:
        return {"ok": False, "blocked": "No business profile exists."}
    from .common import load_settings
    global_settings = load_settings()
    settings = profiles_mod.effective_settings(
        settings if settings is not None else global_settings, profile)
    queue = queue or ApprovalQueue()
    queue.conn = conn
    pid = profile["id"]
    summary = {"profile": profile["name"], "profile_id": pid, "stages": {},
               "proposals_added": 0, "auto_applied": 0, "notes": []}

    # 1 — competitor discovery
    competitors = profiles_mod.list_competitors(pid, conn)
    if not competitors:
        summary["notes"].append(
            "Competitor list khaali hai — Growth Loop page se competitors "
            "add karo (research role sirf suggestions dega, list owner ki hai).")
    record_stage(conn, pid, "competitor_discovery",
                 {"competitors": len(competitors),
                  "names": [c["name"] for c in competitors]})
    summary["stages"]["competitor_discovery"] = len(competitors)

    # 2 — competitor best-ads research (honest: live pull not wired)
    findings = []
    for c in competitors:
        findings.append({
            "competitor": c["name"],
            "status": "RESEARCH TASK — live Ad Library pull is UNTESTED/not "
                      "wired in this build. Manual public Ad Library check "
                      "required: kaunsi ads 3–6 mahine se lagatar chal "
                      "rahi hain (longevity = proven-winner signal, "
                      "Strategy S10). Koi metric invent NAHI kiya gaya.",
            "source": AD_LIBRARY_SOURCE, "date": str(date.today()),
        })
    record_stage(conn, pid, "competitor_ads_research",
                 {"findings": findings, "label": "UNTESTED live pull"})
    log_role_run(conn, "02_competitor_watch", "done",
                 {"entries": competitors, "findings": findings})
    summary["stages"]["competitor_ads_research"] = len(findings)

    # 3 — inspiration brief from the top-creative window
    window = settings.get("TOP_CREATIVE_WINDOW_DAYS") or 7
    brief = inspiration_brief(pid, window_days=window, conn=conn, profile=profile)
    record_stage(conn, pid, "top_creative_inspiration",
                 brief or {"status": "No top-creative record aur koi "
                                      "insight data nahi — brief nahi bana."})
    summary["brief"] = brief
    summary["stages"]["top_creative_inspiration"] = bool(brief)

    # 4 — creative production from the brief (gates unchanged)
    offerings = profiles_mod.list_offerings(pid, conn)
    production = {"status": "skipped — catalog khaali hai"}
    if brief and offerings:
        segment = "students"
        result = creative_mod.generate_creative_set(
            offerings[0]["name"], segment, settings=settings,
            eligibility=profiles_mod.offerings_as_eligibility(pid, conn),
            extra_patterns=profiles_mod.compliance_patterns_for(profile),
            profile=profile)
        cid = store.save_creative(offerings[0]["name"], segment,
                                  "loop_creative_set", result,
                                  result["policy"], conn, profile_id=pid)
        production = {"creative_id": cid, "offering": offerings[0]["name"],
                      "policy_allowed": result["policy"]["allowed"],
                      "policy_reasons": result["policy"]["reasons"]}
    record_stage(conn, pid, "creative_production", production)
    summary["stages"]["creative_production"] = production

    # 5 — optimisation plan (Role 19)
    rows = store.load_insight_rows(conn, profile_id=pid)
    report = optimiser_mod.analyse(rows, settings)
    log_role_run(conn, "19_optimiser", "done", report)
    record_stage(conn, pid, "optimisation_plan",
                 {"proposals": len(report["proposals"]),
                  "safety_stop": report["safety_stop"],
                  "notes": report["notes"]})
    summary["stages"]["optimisation_plan"] = len(report["proposals"])

    # 6 — go-live: PROPOSE by default; AUTO_WITHIN_RULES only with the
    # owner's written approved rules + caps. Safety stop is never
    # auto-applied and never auto-resumed.
    auto = _auto_rules_ok(settings)
    go_live = {"mode": settings.get("AUTOMATION_MODE") or "PROPOSE",
               "auto_within_rules": auto, "added": 0, "applied": 0}
    if queue.kill_switch_active():
        go_live["blocked"] = "Kill switch ON — go-live blocked."
    elif report["safety_stop"]:
        queue.engage_kill_switch("growth loop: optimiser spend breach")
        go_live["blocked"] = ("SAFETY STOP — spend breach. Kill switch "
                              "engage ho gaya; auto-resume kabhi nahi hoga.")
    else:
        pending_keys = set()
        for item in queue.list_pending(profile_id=pid):
            p = item["payload"]
            pending_keys.add((p.get("ad_id"), p.get("type")))
        for p in report["proposals"]:
            if (p.get("ad_id"), p.get("type")) in pending_keys:
                continue
            payload = dict(p)
            payload["profile_id"] = pid
            item_id = queue.add_item(p["type"], payload, profile_id=pid)
            go_live["added"] += 1
            if auto:
                queue.approve(item_id)
                res = execute_approved_item(item_id, settings, conn=conn,
                                            queue=queue)
                if res.get("ok"):
                    go_live["applied"] += 1
    record_stage(conn, pid, "go_live", go_live)
    summary["proposals_added"] = go_live["added"]
    summary["auto_applied"] = go_live["applied"]
    summary["stages"]["go_live"] = go_live

    # 7 — monitoring: winners vs losers per creative
    verdicts = {ad_id: v.get("verdict") for ad_id, v in report["per_ad"].items()}
    record_stage(conn, pid, "monitoring",
                 {"verdicts": verdicts,
                  "weak_cta_rule": "falling CTR + high spend + low "
                                   "responses = loser (pause proposal); "
                                   "acha response = winner (scale proposal)"})
    summary["stages"]["monitoring"] = verdicts

    # 8 — refresh: fatigue/decay triggers a fresh brief (loop restarts)
    fatigued = [a for a, v in report["per_ad"].items()
                if v.get("verdict") == "fatigued creative"]
    refresh = {"fatigued": fatigued, "triggered": bool(fatigued)}
    if fatigued:
        refresh["new_brief"] = inspiration_brief(
            pid, window_days=window, conn=conn, profile=profile)
        refresh["note"] = ("Fatigue/decay mila — naya inspiration brief "
                           "bankar loop stage 3 se dobara chalega.")
    record_stage(conn, pid, "refresh", refresh)
    summary["stages"]["refresh"] = refresh
    audit(conn, "growth_loop_cycle",
          "profile=%s proposals=%d auto_applied=%d brief=%s"
          % (profile["slug"], go_live["added"], go_live["applied"],
             bool(brief)))
    return summary
