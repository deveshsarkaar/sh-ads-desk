"""Approval Queue — Role 14 of SH Ads Desk (Step 1, MOCK build).

Approve / Edit / Reject as data operations on SQLite. Nothing reaches Meta
(mock or real) without an APPROVED item. Also owns the kill switch: engaging
it disables automation and pauses everything the system manages (mock
objects only in Step 1).
"""
import json

from .common import audit, get_db


class ApprovalQueue:
    def __init__(self, db_path=None):
        self.conn = get_db(db_path) if db_path else get_db()

    def add_item(self, kind, payload):
        cur = self.conn.execute(
            "INSERT INTO proposals (kind, payload, status, created_at) "
            "VALUES (?, ?, 'PENDING', datetime('now'))",
            (kind, json.dumps(payload, ensure_ascii=False, default=str)),
        )
        self.conn.commit()
        item_id = cur.lastrowid
        audit(self.conn, "approval_item_added", "id=%s kind=%s" % (item_id, kind))
        return item_id

    def _get(self, item_id):
        row = self.conn.execute("SELECT * FROM proposals WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            raise KeyError("approval item %s not found" % item_id)
        return row

    def get_payload(self, item_id):
        return json.loads(self._get(item_id)["payload"])

    def status(self, item_id):
        return self._get(item_id)["status"]

    def approve(self, item_id):
        self._get(item_id)
        self.conn.execute("UPDATE proposals SET status = 'APPROVED' WHERE id = ?", (item_id,))
        self.conn.commit()
        audit(self.conn, "approval_approved", "id=%s" % item_id)
        return "APPROVED"

    def reject(self, item_id):
        self._get(item_id)
        self.conn.execute("UPDATE proposals SET status = 'REJECTED' WHERE id = ?", (item_id,))
        self.conn.commit()
        audit(self.conn, "approval_rejected", "id=%s" % item_id)
        return "REJECTED"

    def edit_item(self, item_id, new_payload):
        self._get(item_id)
        self.conn.execute(
            "UPDATE proposals SET payload = ? WHERE id = ?",
            (json.dumps(new_payload, ensure_ascii=False, default=str), item_id),
        )
        self.conn.commit()
        audit(self.conn, "approval_edited", "id=%s" % item_id)
        return "EDITED"

    def list_pending(self):
        rows = self.conn.execute(
            "SELECT * FROM proposals WHERE status = 'PENDING' ORDER BY id").fetchall()
        return [{"id": r["id"], "kind": r["kind"], "payload": json.loads(r["payload"])}
                for r in rows]

    # --- Kill switch ---
    def engage_kill_switch(self, reason, mock_client=None):
        self.conn.execute(
            "INSERT OR REPLACE INTO kv (key, value) VALUES ('kill_switch', '1')")
        self.conn.execute(
            "INSERT OR REPLACE INTO kv (key, value) VALUES ('automation_enabled', '0')")
        self.conn.commit()
        paused = []
        if mock_client is not None:
            paused = mock_client.pause_all()
        audit(self.conn, "kill_switch_engaged",
              "reason=%s paused_mock_objects=%s" % (reason, ",".join(paused) or "none"))
        return {"kill_switch": True, "automation_enabled": False, "paused": paused}

    def kill_switch_active(self):
        row = self.conn.execute(
            "SELECT value FROM kv WHERE key = 'kill_switch'").fetchone()
        return bool(row and row["value"] == "1")

    def automation_enabled(self):
        if self.kill_switch_active():
            return False
        row = self.conn.execute(
            "SELECT value FROM kv WHERE key = 'automation_enabled'").fetchone()
        return bool(row and row["value"] == "1")
