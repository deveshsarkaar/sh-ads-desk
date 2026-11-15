"""Rollback — SH Ads Desk Step 1 (MOCK build).

Restores the previous status/budget of a mock change. Rules from the brief:
- Read the FRESH live (mock) state first and show the difference.
- The owner must approve the rollback itself (approved=True) — never automatic.
- Rollback cannot refund spend or undo delivery that already happened
  (nothing has been delivered in Step 1; the note is recorded in the audit).
- Old and new values are written to the audit log. Never auto-resume: a
  rollback to a PAUSED state is fine; this module never sets anything ACTIVE
  on its own unless that was the recorded previous value AND the owner
  approved this rollback.
"""
from .common import audit, get_db


def rollback_last_change(client, object_id, approved=False, db_path=None):
    if not approved:
        return {
            "ok": False,
            "blocked": "Rollback needs the owner's explicit approval first. "
                       "Fresh state was read; no change was made.",
            "fresh_state": _public(client.get_object(object_id)),
        }
    fresh = client.get_object(object_id)  # fresh-state read before any write
    if fresh is None:
        return {"ok": False, "blocked": "Object %s not found in mock client." % object_id}
    if not fresh["history"]:
        return {"ok": False, "blocked": "No change history to roll back for %s." % object_id}

    last = fresh["history"][-1]
    field, current_value, restore_value = last["field"], fresh.get(last["field"]), last["old"]
    diff = {"object_id": object_id, "field": field,
            "current_value": current_value, "restore_value": restore_value}

    if field == "status":
        client.set_status(object_id, restore_value)
    elif field == "budget":
        client.set_budget(object_id, restore_value)
    else:
        return {"ok": False, "blocked": "Field '%s' is not rollback-supported." % field}

    conn = get_db(db_path) if db_path else get_db()
    audit(conn, "rollback_applied",
          "object=%s field=%s old(current)=%s new(restored)=%s | note: rollback cannot "
          "refund spend or undo delivery" % (object_id, field, current_value, restore_value))
    return {"ok": True, "diff": diff,
            "note": "Rollback applied to the MOCK object. Rollback cannot refund spend "
                    "or undo delivery that already happened."}


def _public(obj):
    if obj is None:
        return None
    return {k: v for k, v in obj.items() if k != "history"}
