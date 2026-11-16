"""Job queue — SH Ads Desk (advanced upgrade).

One queue abstraction, two backends:

  * Redis list (fast lane) when REDIS_URL is set and reachable
  * SQLite table `job_queue` otherwise (zero-dependency fallback)

Jobs are small JSON payloads: {"job": "collect"|"optimise"|"daily"|
"weekly"|"loop", "profile_id": int, "enqueued_at": iso}. Enqueueing
the same (job, profile_id) twice while one is still pending is a
no-op (dedupe) — a slow worker never piles up duplicate work.

The 24x7 worker (app/worker.py) is the consumer. The web app and CLI
only ever enqueue or inspect; they never block on the queue.
"""
import json

from .common import _now, get_db
from . import redis_layer

QUEUE_KEY = "sh_ads_desk:jobs"


def _ensure_table(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS job_queue ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " job TEXT NOT NULL, profile_id INTEGER NOT NULL DEFAULT 0,"
        " payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',"
        " created_at TEXT NOT NULL, done_at TEXT)")
    conn.commit()


def enqueue(job, profile_id=0, conn=None):
    """Add a job unless an identical one is already pending.
    Returns True when a new job was queued."""
    payload = {"job": job, "profile_id": int(profile_id or 0),
               "enqueued_at": _now()}
    client = redis_layer.get_client()
    if client is not None:
        try:
            # Dedupe scan: the queue is small by design.
            pending = _redis_pending(client)
            if any(p.get("job") == job and
                   int(p.get("profile_id", 0)) == payload["profile_id"]
                   for p in pending):
                return False
            client.lpush(QUEUE_KEY, json.dumps(payload))
            return True
        except Exception:
            pass  # fall through to SQLite — never lose a job
        finally:
            client.close()
    conn = conn or get_db()
    _ensure_table(conn)
    row = conn.execute(
        "SELECT id FROM job_queue WHERE job = ? AND profile_id = ? "
        "AND status = 'pending'", (job, payload["profile_id"])).fetchone()
    if row:
        return False
    conn.execute(
        "INSERT INTO job_queue (job, profile_id, payload, created_at) "
        "VALUES (?, ?, ?, ?)",
        (job, payload["profile_id"], json.dumps(payload), _now()))
    conn.commit()
    return True


def _redis_pending(client):
    """Read (without removing) everything currently in the Redis
    list, parsed back into payload dicts."""
    out = []
    for raw in client.lrange(QUEUE_KEY):
        try:
            out.append(json.loads(raw))
        except (ValueError, TypeError):
            continue
    return out


def dequeue(conn=None):
    """Pop the oldest pending job (FIFO). Returns the payload dict
    or None when the queue is empty."""
    client = redis_layer.get_client()
    if client is not None:
        try:
            raw = client.rpop(QUEUE_KEY)
            if raw:
                return json.loads(raw)
            return None
        except Exception:
            pass
        finally:
            client.close()
    conn = conn or get_db()
    _ensure_table(conn)
    row = conn.execute(
        "SELECT id, payload FROM job_queue WHERE status = 'pending' "
        "ORDER BY id LIMIT 1").fetchone()
    if not row:
        return None
    conn.execute(
        "UPDATE job_queue SET status = 'done', done_at = ? WHERE id = ?",
        (_now(), row["id"]))
    conn.commit()
    return json.loads(row["payload"])


def pending_count(conn=None):
    client = redis_layer.get_client()
    if client is not None:
        try:
            return int(client.llen(QUEUE_KEY))
        except Exception:
            pass
        finally:
            client.close()
    conn = conn or get_db()
    _ensure_table(conn)
    return conn.execute(
        "SELECT COUNT(*) AS n FROM job_queue WHERE status = 'pending'"
    ).fetchone()["n"]


def backend_name():
    return "redis" if redis_layer.redis_available() else "sqlite"
