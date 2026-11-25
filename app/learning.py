"""Outcome learning — SH Ads Desk V2.

The Expert Engine judges ads; this module records what actually
happened after each verdict and calibrates the account's thresholds
from measured outcomes. Calibration output is a proposal only: it
never changes a threshold by itself, and accuracy is reported only
from recorded outcomes (no outcome recorded = no claim).
"""
import json

from .common import _now, audit

VERDICTS = ("scale_candidate", "hold", "iterate", "stop_candidate",
            "insufficient_data")


def _load(conn, profile_id):
    row = conn.execute("SELECT value FROM kv WHERE key = ?",
                       ("learning:%s" % profile_id,)).fetchone()
    if not row:
        return []
    try:
        data = json.loads(row["value"])
        return data if isinstance(data, list) else []
    except (ValueError, TypeError):
        return []


def _save(conn, profile_id, outcomes):
    conn.execute("INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
                 ("learning:%s" % profile_id, json.dumps(outcomes)))
    conn.commit()


def _is_correct(verdict, result_cpa, target_cpa):
    """Outcome check against the verdict's own logic. A missing result
    CPA after a stop verdict counts as correct (the ad stayed dead);
    for other verdicts a missing result cannot be judged."""
    if result_cpa is None:
        return True if verdict == "stop_candidate" else None
    if not target_cpa:
        return None
    if verdict in ("scale_candidate", "hold"):
        return result_cpa <= target_cpa
    if verdict == "stop_candidate":
        return result_cpa > target_cpa
    if verdict == "iterate":
        return result_cpa <= 1.5 * target_cpa
    return None


def record_outcome(conn, profile_id, ad_id, verdict, result_cpa=None,
                   target_cpa=None):
    if verdict not in VERDICTS:
        return "Unknown verdict; outcome not recorded."
    outcomes = _load(conn, profile_id)
    entry = {"ad_id": str(ad_id or ""), "verdict": verdict,
             "result_cpa": result_cpa, "target_cpa": target_cpa,
             "correct": _is_correct(verdict, result_cpa, target_cpa),
             "at": _now()}
    outcomes.append(entry)
    _save(conn, profile_id, outcomes)
    audit(conn, "learning_outcome_recorded",
          "profile=%s ad=%s verdict=%s correct=%s"
          % (profile_id, entry["ad_id"], verdict, entry["correct"]))
    return "Outcome recorded for %s." % (entry["ad_id"] or "ad")


def calibration(conn, profile_id):
    """Accuracy per verdict from recorded outcomes + threshold
    proposals. Proposals only; nothing auto-changes."""
    outcomes = _load(conn, profile_id)
    judged = [o for o in outcomes if o.get("correct") is not None]
    per = {}
    for v in VERDICTS:
        rows = [o for o in judged if o["verdict"] == v]
        if rows:
            per[v] = {"judged": len(rows),
                      "correct": sum(1 for o in rows if o["correct"]),
                      "accuracy_pct": round(
                          100 * sum(1 for o in rows if o["correct"])
                          / len(rows))}
    proposals = []
    scale = per.get("scale_candidate")
    if scale and scale["judged"] >= 5 and scale["accuracy_pct"] < 50:
        proposals.append(
            "Scale verdicts were right less than half the time on this "
            "account: propose requiring 20+ conversions before scaling.")
    stop = per.get("stop_candidate")
    if stop and stop["judged"] >= 5 and stop["accuracy_pct"] < 50:
        proposals.append(
            "Stop verdicts were often wrong on this account: propose "
            "waiting for 4x target-CPA spend before stopping.")
    if not judged:
        proposals.append(
            "No judged outcomes yet: record results after verdicts so "
            "the account can calibrate its own thresholds.")
    total = len(judged)
    overall = (round(100 * sum(1 for o in judged if o["correct"]) / total)
               if total else None)
    return {"outcomes_recorded": len(outcomes), "judged": total,
            "overall_accuracy_pct": overall, "per_verdict": per,
            "proposals": proposals,
            "note": "Accuracy is computed only from recorded outcomes; "
                    "threshold changes remain proposals for approval."}
