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
  weekly    — generate + store the weekly report.
All commands are safe to re-run; optimiser proposals are de-duplicated by
(ad_id + type) among PENDING items.
"""
import argparse
import json
import os
import sys

from . import optimiser as optimiser_mod
from . import reports as reports_mod
from . import store
from .approval_queue import ApprovalQueue
from .common import audit, get_db, load_settings, log_role_run


def cmd_collect(args):
    settings = load_settings()
    conn = get_db()
    mode = os.environ.get("META_MODE", "MOCK").upper()
    if mode == "LIVE" and os.environ.get("META_ACCESS_TOKEN"):
        from .meta_client import MetaClient
        client = MetaClient.from_env()
        rows = client.fetch_insights()  # UNTESTED live path, read-only
        conn.execute("DELETE FROM insight_rows")
        for row in rows:
            conn.execute(
                "INSERT INTO insight_rows (dataset, row_json, created_at) "
                "VALUES ('LIVE (UNTESTED)', ?, datetime('now'))",
                (json.dumps(row),))
        conn.commit()
        audit(conn, "jobs_collect", "LIVE (UNTESTED) insights pull: %d rows" % len(rows))
        print("collect: LIVE (UNTESTED) — %d rows stored" % len(rows))
        return 0
    n = store.seed_insights(args.dataset)
    audit(conn, "jobs_collect", "MOCK dataset '%s' ensured (%d rows total)"
          % (args.dataset, store.load_insight_rows(conn).__len__()))
    print("collect: MOCK dataset '%s' — %d rows available" % (args.dataset, n))
    return 0


def cmd_optimise(args):
    settings = load_settings()
    conn = get_db()
    queue = ApprovalQueue()
    if queue.kill_switch_active():
        print("optimise: kill switch is ON — optimiser blocked, nothing proposed.")
        audit(conn, "jobs_optimise_blocked", "kill switch ON")
        return 0
    rows = store.load_insight_rows(conn)
    report = optimiser_mod.analyse(rows, settings)
    log_role_run(conn, "19_optimiser", "done", report)
    pending_keys = set()
    for item in queue.list_pending():
        p = item["payload"]
        pending_keys.add((p.get("ad_id"), p.get("type")))
    added = 0
    for p in report["proposals"]:
        if (p.get("ad_id"), p.get("type")) in pending_keys:
            continue
        queue.add_item(p["type"], p)
        added += 1
    if report.get("safety_stop"):
        queue.engage_kill_switch("optimiser detected a spend breach (jobs)")
    audit(conn, "jobs_optimise", "proposals_added=%d notes=%d" % (added, len(report["notes"])))
    print("optimise: %d new proposals queued (PROPOSE mode — owner approval needed), "
          "%d notes" % (added, len(report["notes"])))
    for note in report["notes"]:
        print("  note: " + note)
    return 0


def _report(args, kind):
    settings = load_settings()
    conn = get_db()
    queue = ApprovalQueue()
    rows = store.load_insight_rows(conn)
    language = (settings.get("LANGUAGES") or ["Hinglish"])[0]
    mode = os.environ.get("META_MODE", "MOCK").upper()
    fn = reports_mod.daily_report if kind == "daily" else reports_mod.weekly_report
    body = fn(rows, queue.list_pending(), settings, language=language,
              source=("LIVE (UNTESTED)" if mode == "LIVE" else "MOCK"))
    rid = store.save_report(kind, language, body, conn)
    log_role_run(conn, "20_reporter", "done", {"report_id": rid, "kind": kind})
    audit(conn, "jobs_" + kind, "report_id=%s language=%s" % (rid, language))
    print(body)
    print("[stored as report #%d]" % rid)
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
    args = parser.parse_args(argv)
    if args.cmd == "collect":
        return cmd_collect(args)
    if args.cmd == "optimise":
        return cmd_optimise(args)
    return _report(args, args.cmd)


if __name__ == "__main__":
    sys.exit(main())
