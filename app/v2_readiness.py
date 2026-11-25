"""Advantage+ readiness audit — SH Ads Desk V2.

Research basis (25 Nov 2026): Meta's own help articles push Advantage+
audience/placement/budget with first-party data and diverse creatives;
practitioner sources converge on Advantage+ working best with enough
conversion volume (commonly ~50/week) and 5+ genuinely distinct
creatives, while low-volume or low-budget accounts need a controlled
testing lane first. This module scores readiness from supplied numbers
only. It never promises performance and never changes an account.
"""


def readiness_audit(signals):
    """Score Advantage+ readiness from supplied account signals.

    signals keys (all optional, missing = unknown, never assumed good):
      conversions_per_week, distinct_creatives, daily_budget,
      target_cpa, pixel_ok, capi_ok, purchase_cycle_days
    Returns {score, band, checks, recommendation}. Bands:
      advantage_plus_ready | testing_lane_first | fix_tracking_first
    """
    signals = signals or {}
    checks = []
    score = 0

    conv = signals.get("conversions_per_week")
    if conv is None:
        checks.append({"check": "conversion_volume", "status": "unknown",
                       "detail": "Weekly conversions not supplied — volume band unproven."})
    elif conv >= 50:
        score += 30
        checks.append({"check": "conversion_volume", "status": "ok",
                       "detail": f"{conv} conversions/week meets the commonly cited ~50/week band."})
    elif conv >= 20:
        score += 15
        checks.append({"check": "conversion_volume", "status": "thin",
                       "detail": f"{conv} conversions/week is below the ~50/week band; expect slower learning."})
    else:
        checks.append({"check": "conversion_volume", "status": "low",
                       "detail": f"{conv} conversions/week is low; a controlled testing lane fits better than full Advantage+."})

    creatives = signals.get("distinct_creatives")
    if creatives is None:
        checks.append({"check": "creative_diversity", "status": "unknown",
                       "detail": "Distinct creative count not supplied."})
    elif creatives >= 5:
        score += 25
        checks.append({"check": "creative_diversity", "status": "ok",
                       "detail": f"{creatives} distinct creatives give Advantage+ real choice."})
    elif creatives >= 3:
        score += 12
        checks.append({"check": "creative_diversity", "status": "thin",
                       "detail": f"{creatives} distinct creatives; add genuinely different angles/hooks before scaling."})
    else:
        checks.append({"check": "creative_diversity", "status": "low",
                       "detail": f"{creatives} distinct creative(s); near-duplicates do not count as diversity."})

    pixel_ok = signals.get("pixel_ok")
    capi_ok = signals.get("capi_ok")
    if pixel_ok and capi_ok:
        score += 25
        checks.append({"check": "tracking", "status": "ok",
                       "detail": "Pixel and Conversions API both reported healthy."})
    elif pixel_ok or capi_ok:
        score += 10
        checks.append({"check": "tracking", "status": "partial",
                       "detail": "Only one of Pixel / Conversions API reported healthy; first-party signal is partial."})
    else:
        checks.append({"check": "tracking", "status": "missing",
                       "detail": "Tracking not confirmed healthy; fix signal before judging Advantage+."})

    budget = signals.get("daily_budget")
    cpa = signals.get("target_cpa")
    if budget is None or cpa is None or not cpa:
        checks.append({"check": "budget_adequacy", "status": "unknown",
                       "detail": "Daily budget / target CPA not supplied; budget math unproven."})
    elif budget >= 3 * cpa:
        score += 20
        checks.append({"check": "budget_adequacy", "status": "ok",
                       "detail": "Daily budget covers at least ~3x target CPA; tests can reach thresholds."})
    elif budget >= cpa:
        score += 10
        checks.append({"check": "budget_adequacy", "status": "thin",
                       "detail": "Daily budget covers ~1x target CPA; reads will be slow, keep test cells few."})
    else:
        checks.append({"check": "budget_adequacy", "status": "low",
                       "detail": "Daily budget is below one target CPA; do not judge creatives on a day of spend."})

    tracking_missing = any(c["check"] == "tracking" and c["status"] == "missing" for c in checks)
    if tracking_missing:
        band = "fix_tracking_first"
        recommendation = ("Fix tracking first (Pixel + Conversions API); "
                          "without signal, any Advantage+ decision is blind.")
    elif score >= 70:
        band = "advantage_plus_ready"
        recommendation = ("An Advantage+ setup is worth testing — every change still needs "
                          "owner approval first, and performance is never guaranteed.")
    else:
        band = "testing_lane_first"
        recommendation = ("Run a controlled testing lane first: few test cells, "
                          "distinct creatives, threshold-based kill/graduate decisions.")

    return {"score": score, "band": band, "checks": checks,
            "recommendation": recommendation,
            "guarantee": "none — a readiness score never guarantees performance"}
