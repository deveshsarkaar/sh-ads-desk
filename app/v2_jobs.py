"""V2 background analysis — SH Ads Desk V2.

The web page only saves inputs and enqueues a "v2" job; the 24x7
worker runs the analysis here and stores results in the kv table.
The page itself never blocks on computation, so the UI stays fast
while processing runs in the backend. Every output is advisory:
no Meta write, no budget change, no ad is touched.
"""
import json

from . import creative_matrix, expert_engine, fatigue, feed_catalog, store
from . import subscription_disclosure, test_lane, v2_readiness
from .common import _now, audit, get_db

MODULES = ("readiness", "expert", "creative_matrix", "feed_catalog",
           "test_lane", "fatigue", "disclosure")
MODE_DEFAULTS = {
    "customer": ("readiness", "expert", "fatigue", "disclosure"),
    "agency": MODULES,
    "enterprise": MODULES,
}


def _kv_set(conn, key, value):
    conn.execute("INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
                 (key, json.dumps(value)))
    conn.commit()


def _kv_get(conn, key, default=None):
    row = conn.execute("SELECT value FROM kv WHERE key = ?",
                       (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row["value"])
    except (ValueError, TypeError):
        return default


def save_inputs(conn, profile_id, inputs):
    _kv_set(conn, "v2_inputs:%s" % profile_id, inputs or {})


def load_inputs(conn, profile_id):
    return _kv_get(conn, "v2_inputs:%s" % profile_id, {}) or {}


def load_results(conn, profile_id):
    return _kv_get(conn, "v2_results:%s" % profile_id)


def v2_pending(conn, profile_id):
    """True while a v2 job for this profile is still queued."""
    try:
        row = conn.execute(
            "SELECT id FROM job_queue WHERE job = 'v2' AND profile_id = ? "
            "AND status = 'pending'", (int(profile_id or 0),)).fetchone()
        return row is not None
    except Exception:
        return False


def _fatigue_rows(conn, profile_id, inputs):
    rows = inputs.get("fatigue_rows") or []
    if rows:
        return rows
    out = []
    for r in store.load_insight_rows(conn, profile_id=profile_id):
        if any(k in r for k in ("ctr", "frequency", "cpm", "hook_rate")):
            out.append({k: r.get(k) for k in
                        ("ctr", "frequency", "cpm", "hook_rate")})
    return out


def run_v2(conn=None, profile_id=0):
    """Compute all V2 analyses for one profile and store results.
    Returns the results dict. Called by the worker (job "v2")."""
    conn = conn or get_db()
    inputs = load_inputs(conn, profile_id)
    from . import profiles as profiles_mod
    profile = (profiles_mod.get_profile(profile_id, conn)
               if profile_id else None)
    preset_key = (profile or {}).get("industry_preset") or "software_digital"

    readiness = v2_readiness.readiness_audit({
        "conversions_per_week": inputs.get("conversions_per_week"),
        "distinct_creatives": inputs.get("distinct_creatives"),
        "daily_budget": inputs.get("daily_budget"),
        "target_cpa": inputs.get("target_cpa"),
        "pixel_ok": bool(inputs.get("pixel_ok")),
        "capi_ok": bool(inputs.get("capi_ok")),
    })
    matrix = creative_matrix.build_matrix(
        preset_key, inputs.get("offering_name") or "Offering",
        facts=inputs.get("facts") or [])
    offerings = (profiles_mod.list_offerings(profile_id, conn)
                 if profile_id else [])
    catalog = feed_catalog.analyze_inputs(inputs, offerings, profile)
    plan = test_lane.plan_cells(
        inputs.get("target_cpa"), inputs.get("daily_budget"),
        inputs.get("distinct_creatives") or 0)
    results = {
        "ran_at": _now(),
        "readiness": readiness,
        "expert": expert_engine.expert_review(
            inputs, store.load_insight_rows(conn, profile_id=profile_id)),
        "creative_matrix": matrix,
        "feed_catalog": catalog,
        "test_lane": {"plan": plan,
                      "scale_steps": test_lane.scale_steps(
                          inputs.get("daily_budget") or 0)},
        "fatigue": fatigue.fatigue_score(
            _fatigue_rows(conn, profile_id, inputs)),
        "disclosure": subscription_disclosure.check_disclosure({
            "price_text": inputs.get("price_text") or "",
            "cancellation_text": inputs.get("cancellation_text") or "",
            "collects_pii": bool(inputs.get("collects_pii")),
            "opt_in_unchecked": bool(inputs.get("opt_in_unchecked")),
        }),
    }
    _kv_set(conn, "v2_results:%s" % profile_id, results)
    audit(conn, "v2_analysis_done",
          "profile=%s readiness=%s fatigue=%s catalog_ad_ready=%s/%s"
          % (profile_id, readiness["band"], results["fatigue"]["band"],
             catalog["ad_ready_count"], catalog["total_items"]))
    return results
