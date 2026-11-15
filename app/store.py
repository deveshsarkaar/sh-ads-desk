"""Small persistence helpers on top of common.get_db (SQLite).

Insight rows, lead-quality log (counts/status ONLY — never names, phones,
emails or any personal data), creatives and generated reports.
"""
import json

from . import mock_insights
from .common import _now, audit, get_db

LEAD_STATUSES = ("enquiry", "real_conversation", "reseller_application",
                 "order", "junk")


def _resolve_profile_id(conn, profile_id):
    """profile_id=None means 'the active business profile' (seeded on
    first use). An explicit id (including 0 = legacy/unscoped) is used
    as given, so old unscoped rows keep working."""
    if profile_id is not None:
        return profile_id
    from . import profiles
    profile = profiles.get_active_profile(conn)
    return profile["id"] if profile else 0


def seed_insights(dataset="one_big_winner", conn=None, profile_id=None):
    conn = conn or get_db()
    pid = _resolve_profile_id(conn, profile_id)
    existing = conn.execute(
        "SELECT COUNT(*) AS n FROM insight_rows WHERE profile_id = ?",
        (pid,)).fetchone()["n"]
    if existing:
        return existing
    for row in mock_insights.get_dataset(dataset):
        conn.execute(
            "INSERT INTO insight_rows (dataset, row_json, created_at, profile_id) "
            "VALUES (?, ?, ?, ?)",
            (dataset, json.dumps(row), _now(), pid))
    conn.commit()
    audit(conn, "insights_seeded",
          "MOCK dataset '%s' loaded for profile %s" % (dataset, pid))
    return len(mock_insights.get_dataset(dataset))


def load_insight_rows(conn=None, profile_id=None):
    conn = conn or get_db()
    pid = _resolve_profile_id(conn, profile_id)
    rows = conn.execute(
        "SELECT row_json FROM insight_rows WHERE profile_id IN (?, 0) ORDER BY id",
        (pid,)).fetchall()
    return [json.loads(r["row_json"]) for r in rows]


def replace_insights(dataset, conn=None, profile_id=None):
    conn = conn or get_db()
    pid = _resolve_profile_id(conn, profile_id)
    conn.execute("DELETE FROM insight_rows WHERE profile_id = ?", (pid,))
    conn.commit()
    n = seed_insights(dataset, conn, profile_id=pid)
    audit(conn, "insights_dataset_switched",
          "MOCK dataset '%s' (%d rows) for profile %s" % (dataset, n, pid))
    return n


def add_lead(ad_ref, status, count=1, conn=None):
    if status not in LEAD_STATUSES:
        raise ValueError("Lead status must be one of: %s" % ", ".join(LEAD_STATUSES))
    conn = conn or get_db()
    conn.execute(
        "INSERT INTO lead_log (ad_ref, status, count, created_at) VALUES (?, ?, ?, ?)",
        (str(ad_ref)[:60], status, int(count), _now()))
    conn.commit()
    audit(conn, "lead_logged", "ad_ref=%s status=%s count=%s (counts only, no personal data)"
          % (ad_ref, status, count))


def lead_summary(conn=None):
    conn = conn or get_db()
    out = {s: 0 for s in LEAD_STATUSES}
    for r in conn.execute(
            "SELECT status, SUM(count) AS n FROM lead_log GROUP BY status").fetchall():
        out[r["status"]] = int(r["n"] or 0)
    return out


def save_creative(product, segment, kind, content, policy, conn=None, profile_id=None):
    conn = conn or get_db()
    pid = _resolve_profile_id(conn, profile_id)
    cur = conn.execute(
        "INSERT INTO creatives (product, segment, kind, content, policy_allowed, "
        "policy_reasons, created_at, profile_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (product, segment, kind, json.dumps(content, ensure_ascii=False, default=str),
         1 if policy.get("allowed") else 0,
         json.dumps(policy.get("reasons", [])), _now(), pid))
    conn.commit()
    return cur.lastrowid


def list_creatives(conn=None, profile_id=None):
    conn = conn or get_db()
    if profile_id is None:
        return conn.execute("SELECT * FROM creatives ORDER BY id DESC LIMIT 50").fetchall()
    return conn.execute(
        "SELECT * FROM creatives WHERE profile_id IN (?, 0) ORDER BY id DESC LIMIT 50",
        (profile_id,)).fetchall()


def register_asset(filename, kind, source="manual upload (owner)", provider=None,
                   model=None, prompt=None, cost_note=None, remote_url=None,
                   checklist=None, conn=None):
    """Register an asset (manual upload OR API-generated) with visual check
    PENDING — it can only enter the approval flow after the owner ticks the
    full visual checklist. Generated assets record provider/model/prompt and
    cost as 'unknown — provider billing' (never an invented price)."""
    from .creative import VISUAL_CHECKLIST
    conn = conn or get_db()
    cur = conn.execute(
        "INSERT INTO assets (filename, kind, checklist, visual_check, source, "
        "provider, model, prompt, cost_note, remote_url, created_at) "
        "VALUES (?, ?, ?, 'PENDING', ?, ?, ?, ?, ?, ?, ?)",
        (filename, kind, json.dumps(checklist or VISUAL_CHECKLIST), source,
         provider, model, prompt, cost_note, remote_url, _now()))
    conn.commit()
    audit(conn, "asset_registered",
          "file=%s kind=%s source=%s provider=%s model=%s (visual check PENDING)"
          % (filename, kind, source, provider or "-", model or "-"))
    return cur.lastrowid


def list_assets(conn=None, limit=30):
    conn = conn or get_db()
    return conn.execute("SELECT * FROM assets ORDER BY id DESC LIMIT ?",
                        (limit,)).fetchall()


# --- Async video jobs (submitted via a provider; polled from the studio) ---
def add_video_job(job, conn=None):
    conn = conn or get_db()
    jobs = list_video_jobs(conn)
    jobs.append(job)
    conn.execute("INSERT OR REPLACE INTO kv (key, value) VALUES ('video_jobs', ?)",
                 (json.dumps(jobs),))
    conn.commit()
    audit(conn, "video_job_submitted",
          "job=%s provider=%s model=%s" % (job.get("job_id"),
                                           job.get("provider"),
                                           job.get("model")))


def list_video_jobs(conn=None):
    conn = conn or get_db()
    row = conn.execute("SELECT value FROM kv WHERE key = 'video_jobs'").fetchone()
    if not row:
        return []
    try:
        jobs = json.loads(row["value"])
        return jobs if isinstance(jobs, list) else []
    except ValueError:
        return []


def update_video_job(job_id, updates, conn=None):
    conn = conn or get_db()
    jobs = list_video_jobs(conn)
    for job in jobs:
        if str(job.get("job_id")) == str(job_id):
            job.update(updates)
    conn.execute("INSERT OR REPLACE INTO kv (key, value) VALUES ('video_jobs', ?)",
                 (json.dumps(jobs),))
    conn.commit()


def save_report(kind, language, body, conn=None, profile_id=None):
    conn = conn or get_db()
    pid = _resolve_profile_id(conn, profile_id)
    cur = conn.execute(
        "INSERT INTO reports (kind, language, body, created_at, profile_id) "
        "VALUES (?, ?, ?, ?, ?)",
        (kind, language, body, _now(), pid))
    conn.commit()
    return cur.lastrowid


def list_reports(conn=None):
    conn = conn or get_db()
    return conn.execute("SELECT * FROM reports ORDER BY id DESC LIMIT 20").fetchall()
