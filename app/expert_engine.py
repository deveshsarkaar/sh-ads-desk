"""Expert Engine — SH Ads Desk V2.

Encodes veteran media-buyer decision discipline as transparent rules:
an account audit scorecard, per-ad verdicts with evidence, and a
structured testing protocol. Every output is a proposal for human
approval. Nothing here executes, and nothing guarantees results:
whether this system beats any human expert can only be proven by
measured live results on real accounts, never claimed in advance.
"""

HONESTY_NOTE = (
    "Expert review is decision support built from recorded evidence "
    "and stated thresholds. It does not guarantee results, and it "
    "cannot promise to outperform any human expert; that can only be "
    "proven by measured live performance against an account baseline."
)

VERDICT_ACTIONS = {
    "scale_candidate": "Propose a staged budget increase (10-20% steps) "
                       "and watch cost per result after each step.",
    "hold": "Keep running unchanged; gather more evidence before "
            "the next decision.",
    "iterate": "Propose a creative or angle change; cost is above "
               "the target band with enough evidence to act.",
    "stop_candidate": "Propose pausing this ad; spend passed the "
                      "evidence threshold with no conversions.",
    "insufficient_data": "Not enough evidence yet; let the test "
                         "reach its minimum spend before judging.",
}


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _conversions(row):
    for key in ("qualified_leads", "conversions", "orders", "enquiries"):
        v = _num(row.get(key))
        if v is not None:
            return v
    return 0.0


def campaign_verdicts(rows, target_cpa=None):
    """Per-ad verdicts from recorded rows. Proposals only."""
    target = _num(target_cpa)
    out = []
    for row in rows or []:
        spend = _num(row.get("spend")) or 0.0
        conv = _conversions(row)
        cpa = (spend / conv) if conv > 0 else None
        notes = []
        freq = _num(row.get("frequency_end"))
        ctr_s, ctr_e = _num(row.get("ctr_start")), _num(row.get("ctr_end"))
        if freq is not None and freq >= 3:
            notes.append("frequency is high; refresh creative before "
                         "raising budget")
        if ctr_s and ctr_e is not None and ctr_s > 0 and ctr_e <= ctr_s * 0.6:
            notes.append("CTR fell sharply; fatigue is likely")
        if row.get("conversions_lagged_pending"):
            verdict = "hold"
            notes.append("conversions are still lagging; do not judge yet")
        elif target and spend >= 3 * target and conv == 0:
            verdict = "stop_candidate"
        elif target and conv >= 10 and cpa is not None and cpa <= target:
            verdict = "scale_candidate"
        elif target and conv >= 5 and cpa is not None and cpa > 1.5 * target:
            verdict = "iterate"
        elif conv < 5:
            verdict = "insufficient_data"
        else:
            verdict = "hold"
        confidence = ("high" if conv >= 20 else
                      "medium" if conv >= 5 else "low")
        out.append({
            "ad_id": row.get("ad_id") or row.get("campaign_id") or "ad",
            "verdict": verdict,
            "action": VERDICT_ACTIONS[verdict],
            "confidence": confidence,
            "evidence": {"spend": spend, "conversions": conv,
                         "cpa": (round(cpa, 2) if cpa is not None else None),
                         "target_cpa": target},
            "notes": notes,
        })
    return out


def expert_audit(signals):
    """Account scorecard across the disciplines experts check first."""
    signals = signals or {}
    pixel, capi = bool(signals.get("pixel_ok")), bool(signals.get("capi_ok"))
    tracking = 100 if (pixel and capi) else 50 if (pixel or capi) else 0
    distinct = _num(signals.get("distinct_creatives")) or 0
    creative = (100 if distinct >= 6 else 70 if distinct >= 4 else
                40 if distinct >= 2 else 15)
    budget, target = _num(signals.get("daily_budget")), _num(
        signals.get("target_cpa"))
    if budget and target:
        ratio = budget / target
        budget_score = (100 if ratio >= 10 else 70 if ratio >= 5 else
                        40 if ratio >= 2 else 15)
    else:
        budget_score = 30
    volume_n = _num(signals.get("conversions_per_week")) or 0
    volume = (100 if volume_n >= 50 else 70 if volume_n >= 20 else
              40 if volume_n >= 5 else 15)
    dims = {"tracking": tracking, "creative_diversity": creative,
            "budget_discipline": budget_score, "conversion_volume": volume}
    overall = round(sum(dims.values()) / len(dims))
    grade = ("A" if overall >= 80 else "B" if overall >= 60 else
             "C" if overall >= 40 else "D")
    fixes = {
        "tracking": "Fix Pixel + Conversions API before scaling spend.",
        "creative_diversity": "Build distinct concepts (angle x persona "
                              "x format x hook), not near-duplicates.",
        "budget_discipline": "Fund fewer cells properly: each test cell "
                             "needs multiples of the target CPA.",
        "conversion_volume": "Stay in a testing lane until conversion "
                             "volume supports Advantage+ learning.",
    }
    weakest = sorted(dims, key=lambda k: dims[k])[:2]
    return {"dimensions": dims, "overall_score": overall, "grade": grade,
            "top_actions": [fixes[k] for k in weakest if dims[k] < 70]}


def testing_protocol(target_cpa=None, daily_budget=None):
    """The structured test discipline: one variable, funded cells,
    evidence thresholds, staged scaling. Proposals only."""
    target = _num(target_cpa)
    min_spend = (round(3 * target, 2) if target else None)
    steps = [
        "State one hypothesis per test (angle, hook, format, or offer).",
        "Change one variable at a time so the result is readable.",
        ("Fund each cell to at least %s (3x target CPA) before judging."
         % min_spend) if min_spend else
        "Set a target CPA first; without it no cell can be judged.",
        "Read results on cost per qualified result, never on CTR alone.",
        "Kill below the evidence threshold, iterate above the cost band, "
        "scale winners in 10-20% steps with a read after each step.",
        "Refresh creative when frequency rises or CTR falls sharply; "
        "fatigue is a creative problem before it is a budget problem.",
    ]
    return {"min_cell_spend": min_spend, "steps": steps}


def expert_review(inputs, rows=None):
    inputs = inputs or {}
    verdicts = campaign_verdicts(rows or [], inputs.get("target_cpa"))
    counts = {}
    for v in verdicts:
        counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1
    return {
        "audit": expert_audit(inputs),
        "verdicts": verdicts,
        "verdict_counts": counts,
        "protocol": testing_protocol(inputs.get("target_cpa"),
                                     inputs.get("daily_budget")),
        "note": HONESTY_NOTE,
    }
