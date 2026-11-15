"""Small persistence helpers on top of common.get_db (SQLite).

Insight rows, lead-quality log (counts/status ONLY — never names, phones,
emails or any personal data), creatives and generated reports.
"""
import json

from . import mock_insights
from .common import _now, audit, get_db

LEAD_STATUSES = ("enquiry", "real_conversation", "reseller_application",
                 "order", "junk")


def seed_insights(dataset="one_big_winner", conn=None):
    conn = conn or get_db()
    existing = conn.execute("SELECT COUNT(*) AS n FROM insight_rows").fetchone()["n"]
    if existing:
        return existing
    for row in mock_insights.get_dataset(dataset):
        conn.execute(
            "INSERT INTO insight_rows (dataset, row_json, created_at) VALUES (?, ?, ?)",
            (dataset, json.dumps(row), _now()))
    conn.commit()
    audit(conn, "insights_seeded", "MOCK dataset '%s' loaded for demo views" % dataset)
    return len(mock_insights.get_dataset(dataset))


def load_insight_rows(conn=None):
    conn = conn or get_db()
    rows = conn.execute("SELECT row_json FROM insight_rows ORDER BY id").fetchall()
    return [json.loads(r["row_json"]) for r in rows]


def replace_insights(dataset, conn=None):
    conn = conn or get_db()
    conn.execute("DELETE FROM insight_rows")
    conn.commit()
    n = seed_insights(dataset, conn)
    audit(conn, "insights_dataset_switched", "MOCK dataset '%s' (%d rows)" % (dataset, n))
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


def save_creative(product, segment, kind, content, policy, conn=None):
    conn = conn or get_db()
    cur = conn.execute(
        "INSERT INTO creatives (product, segment, kind, content, policy_allowed, "
        "policy_reasons, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (product, segment, kind, json.dumps(content, ensure_ascii=False, default=str),
         1 if policy.get("allowed") else 0,
         json.dumps(policy.get("reasons", [])), _now()))
    conn.commit()
    return cur.lastrowid


def list_creatives(conn=None):
    conn = conn or get_db()
    return conn.execute("SELECT * FROM creatives ORDER BY id DESC LIMIT 50").fetchall()


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


def save_report(kind, language, body, conn=None):
    conn = conn or get_db()
    cur = conn.execute(
        "INSERT INTO reports (kind, language, body, created_at) VALUES (?, ?, ?, ?)",
        (kind, language, body, _now()))
    conn.commit()
    return cur.lastrowid


def list_reports(conn=None):
    conn = conn or get_db()
    return conn.execute("SELECT * FROM reports ORDER BY id DESC LIMIT 20").fetchall()
