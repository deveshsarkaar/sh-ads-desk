"""Mission Control data — SH Ads Desk (reel-style UI).

The reel the owner shared showed a visual agent office: a central
META ADS AGENT orchestrator, 4 departments, 20 agents, each with a
live DOING / NEXT / DONE status. This module assembles that view
from the system's REAL records — nothing here is simulated:

  * agent status comes from `role_runs` (every role execution is
    logged there by the orchestrator and the jobs pipeline)
  * NEXT comes from real pending work: items waiting in the
    approval queue and jobs waiting in the 24x7 worker queue
  * the centre panel shows the real worker heartbeat, automation
    mode, kill-switch state and active business profile

Status rules (display heuristics over real records, labelled as
such in the UI):
  DOING   — the role ran within the last 5 minutes (active cycle)
  DONE    — the role has run at least once; chip shows last run time
  NEXT    — pending work is waiting that this role owns
            (approvals for Role 14, queued worker jobs mapped below)
  WAITING — the role has not run yet
"""
from datetime import datetime, timedelta, timezone

DEPARTMENTS = [
    ("A. Research & Strategy", "#2563eb", [
        ("01_audience_research", "Audience Research"),
        ("02_competitor_watch", "Competitor Watch"),
        ("03_trend_analysis", "Trend Analysis"),
        ("04_funnel_strategy", "Funnel Strategy"),
        ("05_budget_planning", "Budget Planning"),
    ]),
    ("B. Creative Production", "#7c3aed", [
        ("06_angle_generator", "Angle Generator"),
        ("07_copywriter", "Copywriter"),
        ("08_visual_poster_brief", "Visual / Poster Brief"),
        ("09_reel_script", "Reel Script"),
        ("10_policy_checker", "Policy Checker"),
    ]),
    ("C. Campaign Management", "#0891b2", [
        ("11_structure_planner", "Structure Planner"),
        ("12_targeting_planner", "Targeting Planner"),
        ("13_campaign_builder", "Campaign Builder"),
        ("14_approval_queue_manager", "Approval Queue Manager"),
        ("15_account_health_monitor", "Health Monitor"),
    ]),
    ("D. Performance & Optimisation", "#059669", [
        ("16_data_collector", "Data Collector"),
        ("17_lead_quality_tracker", "Lead Quality Tracker"),
        ("18_creative_analyst", "Creative Analyst"),
        ("19_optimiser", "Optimiser"),
        ("20_reporter", "Reporter"),
    ]),
]

# Worker job -> roles it drives (for the NEXT chip).
JOB_ROLES = {
    "collect": {"16_data_collector"},
    "optimise": {"19_optimiser", "18_creative_analyst"},
    "daily": {"20_reporter"},
    "weekly": {"20_reporter", "03_trend_analysis"},
    "loop": {"02_competitor_watch", "03_trend_analysis",
             "06_angle_generator", "07_copywriter",
             "08_visual_poster_brief", "09_reel_script",
             "19_optimiser"},
}


def _parse(ts):
    try:
        parsed = datetime.fromisoformat(str(ts))
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None:  # stored timestamps are UTC (_now)
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _activity_series(conn, now, days=7):
    """Role-run counts per day for the last `days` days (UTC dates),
    oldest first — the Task Activity chart series. Real rows only."""
    start = (now - timedelta(days=days - 1)).date()
    per_day = {start + timedelta(days=i): 0 for i in range(days)}
    try:
        rows = conn.execute("SELECT created_at FROM role_runs").fetchall()
    except Exception:
        rows = []
    for row in rows:
        ts = _parse(row["created_at"])
        if ts is not None and ts.date() in per_day:
            per_day[ts.date()] += 1
    return [{"date": d.isoformat(), "label": d.strftime("%d %b"),
             "count": per_day[d]} for d in sorted(per_day)]


def mission_data(conn, settings, profile=None, queue=None, now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    pid = profile["id"] if profile else 0

    last_runs = {}
    for row in conn.execute(
            "SELECT role, status, created_at FROM role_runs "
            "ORDER BY id").fetchall():
        last_runs[row["role"]] = row  # latest wins (ordered by id)

    pending_approvals = 0
    if queue is not None:
        try:
            pending_approvals = len(queue.list_pending(profile_id=pid))
        except Exception:
            pending_approvals = 0

    from . import autonomy, job_queue
    queued_roles = set()
    try:
        pending_jobs = conn.execute(
            "SELECT job FROM job_queue WHERE status = 'pending'"
        ).fetchall()
        for r in pending_jobs:
            queued_roles |= JOB_ROLES.get(r["job"], set())
    except Exception:
        pass  # job_queue table may not exist before first enqueue

    heartbeat = autonomy.heartbeat_read(conn)
    hb_time = _parse(heartbeat)
    worker_live = bool(hb_time and now - hb_time <= timedelta(minutes=3))

    departments = []
    counts = {"DOING": 0, "DONE": 0, "NEXT": 0, "WAITING": 0}
    for dept_name, color, roles in DEPARTMENTS:
        agents = []
        for role_id, label in roles:
            run = last_runs.get(role_id)
            last_at = _parse(run["created_at"]) if run else None
            if run and last_at and now - last_at <= timedelta(minutes=5):
                status = "DOING"
            elif role_id == "14_approval_queue_manager" and pending_approvals:
                status = "NEXT"
            elif role_id in queued_roles:
                status = "NEXT"
            elif run:
                status = "DONE"
            else:
                status = "WAITING"
            counts[status] += 1
            agents.append({
                "id": role_id, "label": label, "status": status,
                "last_run": run["created_at"] if run else None,
                "last_status": run["status"] if run else None,
            })
        active = sum(1 for a in agents if a["status"] in ("DONE", "DOING"))
        progress = int(round(100.0 * active / len(agents))) if agents else 0
        departments.append({"name": dept_name, "color": color,
                            "agents": agents, "progress": progress})

    def _count(sql):
        try:
            return conn.execute(sql, (pid,)).fetchone()["n"]
        except Exception:
            return 0

    kpis = {
        "pending_approvals": pending_approvals,
        "reports": _count("SELECT COUNT(*) AS n FROM reports "
                          "WHERE profile_id IN (?, 0)"),
        "creatives": _count("SELECT COUNT(*) AS n FROM creatives "
                            "WHERE profile_id IN (?, 0)"),
        "queue_pending": job_queue.pending_count(conn),
    }
    centre = {
        "profile": (profile or {}).get("name") or "Software Hub",
        "automation_mode": settings.get("AUTOMATION_MODE", "PROPOSE"),
        "worker_live": worker_live,
        "heartbeat": heartbeat,
        "kill_switch": bool(queue.kill_switch_active()) if queue else False,
        "counts": counts,
    }
    return {"departments": departments, "kpis": kpis, "centre": centre,
            "activity": _activity_series(conn, now)}
