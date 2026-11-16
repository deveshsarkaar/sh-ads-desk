"""24x7 worker daemon — SH Ads Desk (advanced upgrade).

The always-on engine the owner asked for: connect once, set the
rules once, and this worker keeps the whole system running around
the clock — collect, research, creative drafts, optimisation
proposals, reports — until the OWNER stops it (kill switch, toggle,
or stopping the service). It needs nobody in the loop:

  * runs as its own Docker service with restart: unless-stopped —
    a crash or a host reboot brings it back by itself
  * schedule lives in code + kv markers, not in anyone's crontab
  * every job runs through the existing jobs pipeline, so every
    safety gate (eligibility, destination, guardrails, kill
    switch, AUTOMATION_MODE) applies exactly as before
  * a failing job is logged to the audit trail and skipped — one
    bad job never kills the daemon
  * heartbeat in kv (`worker_heartbeat`) so the Settings page can
    show "worker alive" honestly

What the worker NEVER does: widen any gate. With the default
AUTOMATION_MODE=PROPOSE it only prepares proposals; Meta-writes
still need the owner's approval or the signed AUTOPILOT_RULES
(AUTO_WITHIN_RULES within caps). Kill switch engaged = worker
idles and enqueues nothing.

Run:  python -m app.worker          (daemon)
      python -m app.worker --once   (one tick — tests/debugging)
"""
import argparse
import signal
import sys
import time
from datetime import datetime, timedelta

from . import autonomy, job_queue, jobs as jobs_mod
from .approval_queue import ApprovalQueue
from .common import audit, get_db, load_settings

# job -> (min interval, toggle key, quiet-hours allowed?)
SCHEDULE = (
    ("collect", timedelta(hours=6), "AUTO_COLLECT", True),
    ("optimise", timedelta(hours=24), "AUTO_OPTIMISE_PROPOSALS", False),
    ("daily", timedelta(hours=24), "AUTO_REPORTS", False),
    ("loop", timedelta(days=7), "AUTO_RESEARCH", False),
    ("weekly", timedelta(days=7), "AUTO_REPORTS", False),
)

_STOP = False


def _handle_signal(signum, frame):
    global _STOP
    _STOP = True


def _queue(conn):
    queue = ApprovalQueue()
    queue.conn = conn
    return queue


def _last_run(conn, job):
    row = conn.execute(
        "SELECT value FROM kv WHERE key = ?", ("worker_last_" + job,)
    ).fetchone()
    if not row:
        return None
    try:
        return datetime.fromisoformat(row["value"])
    except ValueError:
        return None


def _mark_run(conn, job, when):
    conn.execute(
        "INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
        ("worker_last_" + job, when.isoformat(timespec="seconds")))
    conn.commit()


def due_jobs(conn, settings, now=None):
    """Which scheduled jobs are due right now, honouring toggles,
    quiet hours and the kill switch."""
    now = now or datetime.now()
    if _queue(conn).kill_switch_active():
        return []
    quiet = autonomy.in_quiet_hours(settings, hour=now.hour)
    due = []
    for job, interval, toggle, quiet_ok in SCHEDULE:
        if not autonomy.toggle_on(settings, toggle):
            continue
        if job == "loop" and not autonomy.toggle_on(
                settings, "AUTO_CREATIVE_DRAFTS"):
            continue  # loop produces creative drafts too
        if quiet and not quiet_ok:
            continue
        last = _last_run(conn, job)
        if last is None or now - last >= interval:
            due.append(job)
    return due


def run_job(job):
    """Run one job through the existing CLI pipeline. Returns 0 on
    success; raises on failure (the tick catches and audits it)."""
    return jobs_mod.main([job])


def run_tick(conn=None, settings=None, now=None):
    """One scheduling tick: heartbeat, enqueue due jobs, drain the
    queue. Returns a summary dict (also what --once prints)."""
    conn = conn or get_db()
    settings = settings or load_settings()
    now = now or datetime.now()
    autonomy.heartbeat_write(conn)
    summary = {"enqueued": [], "ran": [], "failed": [],
               "kill_switch": _queue(conn).kill_switch_active()}
    if summary["kill_switch"]:
        return summary
    profile_id = 0
    try:
        from . import profiles as profiles_mod
        profile = profiles_mod.get_active_profile(conn)
        profile_id = profile["id"] if profile else 0
    except Exception:
        pass
    for job in due_jobs(conn, settings, now):
        if job_queue.enqueue(job, profile_id=profile_id, conn=conn):
            summary["enqueued"].append(job)
        _mark_run(conn, job, now)
    while True:
        payload = job_queue.dequeue(conn)
        if not payload:
            break
        job = payload.get("job")
        try:
            run_job(job)
            summary["ran"].append(job)
        except Exception as exc:  # one bad job never kills the daemon
            summary["failed"].append({"job": job, "error": str(exc)[:200]})
            audit(conn, "worker_job_failed",
                  "job=%s error=%s" % (job, str(exc)[:200]))
    if summary["ran"] or summary["failed"]:
        audit(conn, "worker_tick",
              "ran=%s failed=%d" % (",".join(summary["ran"]),
                                    len(summary["failed"])))
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(prog="app.worker")
    parser.add_argument("--once", action="store_true",
                        help="run a single tick and exit")
    args = parser.parse_args(argv)
    if args.once:
        print(run_tick())
        return 0
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
    print("SH Ads Desk worker started (24x7). Stop: kill switch in "
          "the app, or stop the service.", flush=True)
    while not _STOP:
        try:
            settings = load_settings()
            tick = int(settings.get("WORKER_TICK_SECONDS",
                                    autonomy.DEFAULTS["WORKER_TICK_SECONDS"])
                       or 60)
        except Exception:
            tick = 60
        try:
            run_tick()
        except Exception as exc:  # daemon must survive anything
            print("worker tick failed: %s" % exc, flush=True)
        for _ in range(max(5, tick)):
            if _STOP:
                break
            time.sleep(1)
    print("worker stopped by signal.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
