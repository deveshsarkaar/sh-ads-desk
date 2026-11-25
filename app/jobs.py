"""Scheduler CLI — SH Ads Desk (full build).

No always-on agents (brief rule 7). Run these from cron on the owner's
host, e.g.:
    0 9 * * *   cd /app && python -m app.jobs daily
    0 9 * * 1   cd /app && python -m app.jobs weekly
    0 */6 * * * cd /app && python -m app.jobs collect
    30 9 * * *  cd /app && python -m app.jobs optimise

Commands:
  collect   — pull insights: MOCK datasets by default; if META_MODE=LIVE and
              a token is present it uses the UNTESTED real adapter read-only.
  optimise  — run Role 19 on stored insight rows; proposals go to the
              approval queue (PROPOSE mode — nothing is applied).
  daily     — generate + store the daily report (Role 20).
  weekly    — generate + store the weekly report (+ Meta Knowledge
              register review; strategy changes stay proposals).
  loop      — advance ONE full Growth Loop cycle for the active
              business profile (competitors, inspiration brief, creative
              production, optimisation, go-live proposals, monitoring,
              refresh) on the stored MOCK rows.
All commands are safe to re-run; optimiser proposals are de-duplicated by
(ad_id + type) among PENDING items.
"""
import argparse
import json
import os
import sys

from . import optimiser as optimiser_mod
from . import profiles as profiles_mod
from . import reports as reports_mod
from . import store
from .approval_queue import ApprovalQueue
from .common import audit, get_db, load_settings, log_role_run


def _active(conn):
    """Active business profile + its effective settings (global merged
    with profile overrides). All jobs run per active profile."""
    profile = profiles_mod.get_active_profile(conn)
    settings = profiles_mod.effective_settings(load_settings(), profile)
    return profile, settings


def cmd_collect(args):
    conn = get_db()
    profile, settings = _active(conn)
    pid = profile["id"] if profile else 0
    mode = os.environ.get("META_MODE", "MOCK").upper()
    if mode == "LIVE" and os.environ.get("META_ACCESS_TOKEN"):
        from .meta_client import MetaClient
        client = MetaClient.from_env()
        rows = client.fetch_insights()  # UNTESTED live path, read-only
        conn.execute("DELETE FROM insight_rows WHERE profile_id = ?", (pid,))
        for row in rows:
            conn.execute(
                "INSERT INTO insight_rows (dataset, row_json, created_at, profile_id) "
                "VALUES ('LIVE (UNTESTED)', ?, datetime('now'), ?)",
                (json.dumps(row), pid))
        conn.commit()
        audit(conn, "jobs_collect", "LIVE (UNTESTED) insights pull: %d rows (profile %s)"
              % (len(rows), pid))
        print("collect: LIVE (UNTESTED) — %d rows stored" % len(rows))
        return 0
    n = store.seed_insights(args.dataset, conn, profile_id=pid)
    audit(conn, "jobs_collect", "MOCK dataset '%s' ensured for profile %s (%d rows)"
          % (args.dataset, pid, len(store.load_insight_rows(conn, profile_id=pid))))
    print("collect: MOCK dataset '%s' — %d rows available (profile: %s)"
          % (args.dataset, n, profile["name"] if profile else "—"))
    return 0


def cmd_optimise(args):
    conn = get_db()
    profile, settings = _active(conn)
    pid = profile["id"] if profile else 0
    queue = ApprovalQueue()
    queue.conn = conn
    if queue.kill_switch_active():
        print("optimise: kill switch is ON — optimiser blocked, nothing proposed.")
        audit(conn, "jobs_optimise_blocked", "kill switch ON")
        return 0
    rows = store.load_insight_rows(conn, profile_id=pid)
    report = optimiser_mod.analyse(rows, settings)
    log_role_run(conn, "19_optimiser", "done", report)
    pending_keys = set()
    for item in queue.list_pending(profile_id=pid):
        p = item["payload"]
        pending_keys.add((p.get("ad_id"), p.get("type")))
    added = 0
    for p in report["proposals"]:
        if (p.get("ad_id"), p.get("type")) in pending_keys:
            continue
        payload = dict(p)
        payload["profile_id"] = pid
        queue.add_item(p["type"], payload, profile_id=pid)
        added += 1
    if report.get("safety_stop"):
        queue.engage_kill_switch("optimiser detected a spend breach (jobs)")
    audit(conn, "jobs_optimise", "proposals_added=%d notes=%d profile=%s"
          % (added, len(report["notes"]), pid))
    print("optimise: %d new proposals queued (PROPOSE mode — owner approval needed), "
          "%d notes" % (added, len(report["notes"])))
    for note in report["notes"]:
        print("  note: " + note)
    return 0


def cmd_loop(args):
    from . import growth_loop
    conn = get_db()
    profile, _settings = _active(conn)
    queue = ApprovalQueue()
    queue.conn = conn
    summary = growth_loop.run_cycle(conn=conn, profile=profile, queue=queue)
    audit(conn, "jobs_loop", "profile=%s proposals=%d auto=%d"
          % (profile["slug"] if profile else "—",
             summary.get("proposals_added", 0), summary.get("auto_applied", 0)))
    print("loop: profile=%s stages=%s proposals_added=%d auto_applied=%d"
          % (summary.get("profile"), list(summary.get("stages", {}).keys()),
             summary.get("proposals_added", 0), summary.get("auto_applied", 0)))
    if summary.get("brief"):
        print("loop: inspiration brief — %s" % summary["brief"].get("theme"))
    for note in summary.get("notes", []):
        print("  note: " + note)
    return 0


def _report(args, kind):
    conn = get_db()
    profile, settings = _active(conn)
    pid = profile["id"] if profile else 0
    queue = ApprovalQueue()
    queue.conn = conn
    rows = store.load_insight_rows(conn, profile_id=pid)
    language = (settings.get("LANGUAGES") or ["Hinglish"])[0]
    mode = os.environ.get("META_MODE", "MOCK").upper()
    fn = reports_mod.daily_report if kind == "daily" else reports_mod.weekly_report
    body = fn(rows, queue.list_pending(profile_id=pid), settings, language=language,
              source=("LIVE (UNTESTED)" if mode == "LIVE" else "MOCK"),
              profile=profile)
    if kind == "weekly":
        from . import trends as trends_mod
        review = trends_mod.knowledge_review()
        body += ("\nMeta Knowledge register (weekly review): " + review["note"])
        log_role_run(conn, "03_trend_analysis", "done", review)
    rid = store.save_report(kind, language, body, conn, profile_id=pid)
    log_role_run(conn, "20_reporter", "done", {"report_id": rid, "kind": kind})
    audit(conn, "jobs_" + kind, "report_id=%s language=%s profile=%s"
          % (rid, language, pid))
    print(body)
    print("[stored as report #%d]" % rid)
    return 0


def cmd_v2(args):
    """Run the V2 background analysis for the active profile."""
    from . import v2_jobs
    conn = get_db()
    profile, _settings = _active(conn)
    pid = profile["id"] if profile else 0
    results = v2_jobs.run_v2(conn, pid)
    print("V2 analysis done: readiness=%s fatigue=%s disclosure_ok=%s"
          % (results["readiness"]["band"], results["fatigue"]["band"],
             results["disclosure"]["ok"]))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="app.jobs",
                                     description="SH Ads Desk scheduled jobs")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_collect = sub.add_parser("collect")
    p_collect.add_argument("--dataset", default="one_big_winner",
                           choices=["thin_data", "one_big_winner", "all_losers",
                                    "cheap_junk_leads", "lagged_conversions",
                                    "spend_breach", "fatigue"])
    sub.add_parser("optimise")
    sub.add_parser("daily")
    sub.add_parser("weekly")
    sub.add_parser("loop")
    sub.add_parser("v2")
    args = parser.parse_args(argv)
    if args.cmd == "collect":
        return cmd_collect(args)
    if args.cmd == "optimise":
        return cmd_optimise(args)
    if args.cmd == "loop":
        return cmd_loop(args)
    if args.cmd == "v2":
        return cmd_v2(args)
    return _report(args, args.cmd)


if __name__ == "__main__":
    sys.exit(main())
