"""Mission Control (reel-style UI) tests — data asli records se
aata hai: role_runs, approval queue, worker heartbeat."""
from datetime import datetime, timedelta

from app import mission
from app.approval_queue import ApprovalQueue
from app.common import _now, get_db, load_settings, log_role_run


def _queue(conn):
    q = ApprovalQueue()
    q.conn = conn
    return q


def test_departments_cover_20_agents_in_4_departments():
    assert len(mission.DEPARTMENTS) == 4
    total = sum(len(roles) for _name, _color, roles in mission.DEPARTMENTS)
    assert total == 20


def test_status_waiting_without_runs_done_after_run():
    conn = get_db()
    conn.execute("DELETE FROM role_runs WHERE role = '05_budget_planning'")
    conn.commit()
    data = mission.mission_data(conn, load_settings(), queue=_queue(conn))
    agents = {a["id"]: a for d in data["departments"] for a in d["agents"]}
    assert agents["05_budget_planning"]["status"] in ("WAITING", "NEXT")
    log_role_run(conn, "05_budget_planning", "done", {"ok": True})
    from datetime import timezone
    later = datetime.now(timezone.utc) + timedelta(minutes=30)
    data2 = mission.mission_data(conn, load_settings(), queue=_queue(conn),
                                 now=later)
    agents2 = {a["id"]: a for d in data2["departments"] for a in d["agents"]}
    assert agents2["05_budget_planning"]["status"] == "DONE"
    assert agents2["05_budget_planning"]["last_run"] is not None


def test_recent_run_shows_doing():
    conn = get_db()
    log_role_run(conn, "16_data_collector", "done", {"rows": 3})
    data = mission.mission_data(conn, load_settings(), queue=_queue(conn))
    agents = {a["id"]: a for d in data["departments"] for a in d["agents"]}
    assert agents["16_data_collector"]["status"] == "DOING"


def test_pending_approval_marks_role14_next():
    conn = get_db()
    conn.execute("DELETE FROM role_runs WHERE role = '14_approval_queue_manager'")
    conn.commit()
    q = _queue(conn)
    q.add_item("budget_increase", {"campaign": "t"}, profile_id=0)
    data = mission.mission_data(conn, load_settings(), queue=q)
    agents = {a["id"]: a for d in data["departments"] for a in d["agents"]}
    assert data["kpis"]["pending_approvals"] >= 1
    assert agents["14_approval_queue_manager"]["status"] == "NEXT"


def test_mission_page_renders_reel_layout():
    from app import web
    conn = get_db()
    ctx = {"conn": conn, "settings": load_settings(), "profile": None,
           "queue": _queue(conn), "flash": "", "csrf_field": ""}
    html = web.pg_mission(ctx)
    assert "META ADS AGENT" in html
    for dept in ("Research &amp; Strategy", "Creative Production",
                 "Campaign Management", "Performance &amp; Optimisation"):
        assert dept in html
    for label in ("Audience Research", "Copywriter", "Campaign Builder",
                  "Optimiser", "Reporter"):
        assert label in html
    assert "WAITING" in html or "DONE" in html
