"""Owner autonomy controls — SH Ads Desk (advanced upgrade).

The owner's deal is simple: set everything ONCE, then the system
runs 24x7 by itself — and the owner keeps the power to customise or
stop any part of it at any time.

Two different kinds of "auto" live here, and they are NOT the same:

  1. HOUSEKEEPING AUTO (this module's toggles, default ON):
     collect, research tasks, inspiration briefs, creative DRAFTS,
     policy/guardrail checks, analysis, reports, queue processing.
     None of these touch Meta or spend money, so they may run
     unattended around the clock.

  2. META-WRITE AUTO (NOT in this module): pausing a loser,
     scaling a winner, creating a PAUSED draft. These stay governed
     by AUTOMATION_MODE + the signed AUTOPILOT_RULES (see
     AUTOPILOT_RULES.md and growth_loop._auto_rules_ok). The worker
     never widens that gate: with AUTOMATION_MODE=PROPOSE (default)
     the 24x7 engine only ever prepares proposals for the owner.

Owner customisation (Settings page, per business profile):
  AUTO_COLLECT, AUTO_RESEARCH, AUTO_CREATIVE_DRAFTS, AUTO_REPORTS,
  AUTO_OPTIMISE_PROPOSALS — each can be turned off individually.
  WORKER_TICK_SECONDS — how often the worker checks the schedule.
  QUIET_HOURS — "23-07" style window where only collect runs.

The kill switch outranks everything here: when it is engaged the
worker idles and enqueues nothing.
"""
from .common import _now

TOGGLES = (
    ("AUTO_COLLECT", "Data collect (insights refresh)"),
    ("AUTO_RESEARCH", "Competitor research tasks + briefs"),
    ("AUTO_CREATIVE_DRAFTS", "Creative drafts from winning patterns"),
    ("AUTO_REPORTS", "Daily / weekly reports"),
    ("AUTO_OPTIMISE_PROPOSALS", "Optimisation proposals (queue tak)"),
)

DEFAULTS = {
    "AUTO_COLLECT": "true",
    "AUTO_RESEARCH": "true",
    "AUTO_CREATIVE_DRAFTS": "true",
    "AUTO_REPORTS": "true",
    "AUTO_OPTIMISE_PROPOSALS": "true",
    "WORKER_TICK_SECONDS": "60",
    "QUIET_HOURS": "",
}


def _truthy(value):
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def toggle_on(settings, key):
    return _truthy(settings.get(key, DEFAULTS.get(key, "false")))


def in_quiet_hours(settings, hour=None):
    """QUIET_HOURS format '23-07' (start-end, wraps midnight)."""
    spec = str(settings.get("QUIET_HOURS", "") or "").strip()
    if "-" not in spec:
        return False
    try:
        start, end = (int(x) for x in spec.split("-", 1))
    except ValueError:
        return False
    if hour is None:
        from datetime import datetime
        hour = datetime.now().hour
    if start <= end:
        return start <= hour < end
    return hour >= start or hour < end


def heartbeat_write(conn):
    conn.execute(
        "INSERT OR REPLACE INTO kv (key, value) VALUES "
        "('worker_heartbeat', ?)", (_now(),))
    conn.commit()


def heartbeat_read(conn):
    row = conn.execute(
        "SELECT value FROM kv WHERE key = 'worker_heartbeat'").fetchone()
    return row["value"] if row else None


def autonomy_summary(conn, settings):
    """One status dict for the Settings page / health checks."""
    from . import job_queue
    from .approval_queue import ApprovalQueue
    queue = ApprovalQueue()
    queue.conn = conn
    return {
        "toggles": {key: toggle_on(settings, key) for key, _ in TOGGLES},
        "labels": dict(TOGGLES),
        "queue_backend": job_queue.backend_name(),
        "queue_pending": job_queue.pending_count(conn),
        "worker_heartbeat": heartbeat_read(conn),
        "kill_switch": queue.kill_switch_active(),
        "quiet_hours": str(settings.get("QUIET_HOURS", "") or ""),
        "in_quiet_hours": in_quiet_hours(settings),
    }
