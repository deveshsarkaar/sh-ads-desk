"""Advanced autonomy upgrade tests: RESP codec, SQLite job queue,
worker scheduling rules (toggles, quiet hours, kill switch) and a
full worker tick on MOCK data."""
import json
from datetime import datetime, timedelta

from app import autonomy, job_queue, redis_layer, worker
from app.approval_queue import ApprovalQueue
from app.common import get_db


def test_resp_encoding_roundtrip_shape():
    blob = redis_layer._encode_command("SET", "k", "v")
    assert blob == b"*3\r\n$3\r\nSET\r\n$1\r\nk\r\n$1\r\nv\r\n"


def test_resp_reader_parses_replies():
    import socket
    left, right = socket.socketpair()
    reader = redis_layer._RESPReader(left)
    right.sendall(b"+PONG\r\n:42\r\n$5\r\nhello\r\n$-1\r\n*2\r\n$1\r\na\r\n:7\r\n")
    assert reader.read_reply() == "PONG"
    assert reader.read_reply() == 42
    assert reader.read_reply() == "hello"
    assert reader.read_reply() is None
    assert reader.read_reply() == ["a", 7]
    left.close()
    right.close()


def test_redis_absent_falls_back_to_sqlite(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    assert redis_layer.get_client() is None
    assert job_queue.backend_name() == "sqlite"


def test_sqlite_queue_fifo_and_dedupe():
    conn = get_db()
    job_queue._ensure_table(conn)
    conn.execute("DELETE FROM job_queue")
    conn.commit()
    assert job_queue.enqueue("collect", profile_id=3, conn=conn) is True
    assert job_queue.enqueue("collect", profile_id=3, conn=conn) is False  # dedupe
    assert job_queue.enqueue("daily", profile_id=3, conn=conn) is True
    assert job_queue.pending_count(conn) == 2
    first = job_queue.dequeue(conn)
    assert first["job"] == "collect" and first["profile_id"] == 3
    second = job_queue.dequeue(conn)
    assert second["job"] == "daily"
    assert job_queue.dequeue(conn) is None


def _settings(**over):
    base = dict(autonomy.DEFAULTS)
    base.update(over)
    return base


def test_quiet_hours_wrap_midnight():
    s = _settings(QUIET_HOURS="23-07")
    assert autonomy.in_quiet_hours(s, hour=23) is True
    assert autonomy.in_quiet_hours(s, hour=3) is True
    assert autonomy.in_quiet_hours(s, hour=12) is False
    assert autonomy.in_quiet_hours(_settings(QUIET_HOURS="")) is False


def test_due_jobs_respect_toggles_and_quiet_hours():
    conn = get_db()
    conn.execute("DELETE FROM kv WHERE key = 'kill_switch'")
    conn.execute("DELETE FROM kv WHERE key LIKE 'worker_last_%'")
    conn.commit()
    now = datetime(2026, 11, 17, 12, 0, 0)
    due = worker.due_jobs(conn, _settings(), now)
    assert "collect" in due and "daily" in due  # nothing ran yet
    worker._mark_run(conn, "collect", now)
    due2 = worker.due_jobs(conn, _settings(), now + timedelta(hours=1))
    assert "collect" not in due2  # 6h interval not reached
    due3 = worker.due_jobs(conn, _settings(AUTO_COLLECT="false"), now)
    assert "collect" not in due3  # owner toggle OFF wins
    conn.execute("DELETE FROM kv WHERE key LIKE 'worker_last_%'")
    conn.commit()
    quiet = worker.due_jobs(conn, _settings(QUIET_HOURS="11-13"), now)
    assert "collect" in quiet and "daily" not in quiet  # quiet: collect only


def test_kill_switch_idles_worker():
    conn = get_db()
    queue = ApprovalQueue()
    queue.conn = conn
    queue.engage_kill_switch("autonomy test")
    try:
        now = datetime(2026, 11, 17, 12, 0, 0)
        assert worker.due_jobs(conn, _settings(), now) == []
        summary = worker.run_tick(conn=conn, settings=_settings(), now=now)
        assert summary["kill_switch"] is True and summary["ran"] == []
    finally:
        conn.execute("DELETE FROM kv WHERE key = 'kill_switch'")
        conn.commit()


def test_worker_tick_runs_due_jobs_on_mock():
    conn = get_db()
    job_queue._ensure_table(conn)
    conn.execute("DELETE FROM kv WHERE key LIKE 'worker_last_%'")
    conn.execute("DELETE FROM kv WHERE key = 'kill_switch'")
    conn.execute("DELETE FROM job_queue")
    conn.commit()
    now = datetime(2026, 11, 17, 12, 0, 0)
    summary = worker.run_tick(conn=conn, settings=_settings(), now=now)
    assert summary["kill_switch"] is False
    assert "collect" in summary["ran"]
    assert summary["failed"] == []
    assert autonomy.heartbeat_read(conn) is not None
