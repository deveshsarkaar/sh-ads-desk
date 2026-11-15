"""Execution layer — the ONLY path from an approval to a (mock or live) write.

Hard rules enforced here, in code:
- An item executes only when its approval-queue status is APPROVED.
- DRY_RUN=true (the default) means execution is simulated on the MOCK
  client even if META_MODE=LIVE is set later — the owner must deliberately
  turn DRY_RUN off in settings.
- Campaign drafts pass ALL gates first (eligibility + banned claims +
  destination) using the payload's product/copy — fails closed.
- Everything created is PAUSED. Activation is a separate approval and has
  no code path here.
- Kill switch ON blocks execution completely.
- Every write is recorded in meta_writes + the audit log (redacted),
  including the request IDs returned by the client.
"""
import json
import os

from . import policy_checker
from .approval_queue import ApprovalQueue
from .common import audit, get_db
from .meta_client import MetaClient
from .mock_meta import MockMetaClient


def _client_for(settings):
    mode = os.environ.get("META_MODE", "MOCK").upper()
    if mode == "LIVE" and not settings.get("DRY_RUN", True):
        return MetaClient.from_env(), "LIVE (UNTESTED)"
    return MockMetaClient(), "MOCK"


def execute_approved_item(item_id, settings, eligibility=None, conn=None, queue=None):
    conn = conn or get_db()
    queue = queue or ApprovalQueue()
    if queue.kill_switch_active():
        return {"ok": False, "blocked": "Kill switch is ON — all execution is blocked."}
    status = queue.status(item_id)
    if status != "APPROVED":
        return {"ok": False,
                "blocked": "Item %s is %s, not APPROVED — nothing was written." % (item_id, status)}
    payload = queue.get_payload(item_id)
    kind = payload.get("kind") or payload.get("type") or "UNKNOWN"

    client, mode = _client_for(settings)

    if kind == "CAMPAIGN_DRAFT":
        product = payload.get("product", "")
        text = payload.get("creative_text", "")
        gate = policy_checker.check_creative(product, text, settings=settings,
                                             eligibility=eligibility)
        if not gate["allowed"]:
            audit(conn, "execution_blocked_by_gate", "item=%s reasons=%s"
                  % (item_id, "; ".join(gate["reasons"])))
            return {"ok": False, "blocked": "Policy gate failed closed.",
                    "reasons": gate["reasons"]}
        draft = {
            "campaign_name": payload["campaign_name"],
            "adset_name": payload["adset_name"],
            "ad_name": payload["ad_name"],
            "creative_text": text,
            "daily_budget": payload.get("daily_budget") or None,
            "owner_approved": True,  # set ONLY here, from an APPROVED queue item
        }
        key = "approval-%s" % item_id
        if isinstance(client, MockMetaClient):
            camp = client.create_campaign(draft["campaign_name"], idempotency_key=key + ":c",
                                          budget=draft["daily_budget"])
            adset = client.create_adset(camp["id"], draft["adset_name"],
                                        idempotency_key=key + ":as")
            ad = client.create_ad(adset["id"], draft["ad_name"], text,
                                  idempotency_key=key + ":ad")
            result = {"campaign_id": camp["id"], "adset_id": adset["id"],
                      "ad_id": ad["id"], "status": "PAUSED",
                      "request_ids": list(client.requests)}
        else:
            result = client.create_paused_draft(draft, idempotency_key=key)
        conn.execute(
            "INSERT INTO meta_writes (proposal_id, mode, object_ids, request_ids, status, "
            "created_at) VALUES (?, ?, ?, ?, 'PAUSED', datetime('now'))",
            (item_id, mode, json.dumps(result), json.dumps(result.get("request_ids", []))))
        conn.commit()
        audit(conn, "meta_write_executed",
              "item=%s mode=%s objects=%s requests=%s status=PAUSED"
              % (item_id, mode, json.dumps(result), ",".join(result.get("request_ids", []))))
        return {"ok": True, "mode": mode, "result": result,
                "note": "Created PAUSED only. Activation is a separate owner approval."}

    # Optimiser proposals etc. are recorded as acknowledged in Step 1 scope:
    # budget/status changes on real objects arrive with Step 5 and their own
    # approvals. Here we only mark the decision in the audit log.
    audit(conn, "proposal_execution_recorded",
          "item=%s kind=%s mode=%s (no object change applied in this build)"
          % (item_id, kind, mode))
    return {"ok": True, "mode": mode,
            "note": "Proposal decision recorded. Object-level changes are applied "
                    "only through their own approved write path."}
