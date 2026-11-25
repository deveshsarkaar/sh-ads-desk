"""Creative testing-lane planner — SH Ads Desk V2.

Research basis (25 Nov 2026): practitioners run a controlled testing
lane (ABO-style cells) with pre-set spend thresholds (commonly 1-3x
target CPA), minimum read windows (often ~7 days), kill/iterate/
graduate rules, then promote winners into CBO/Advantage+ scaling with
staged budget increases (commonly ~10-20% at a time). Every output
here is a PROPOSAL for owner approval — this module never changes a
budget, pauses an ad, or touches Meta.
"""

DEFAULT_THRESHOLD_MULTIPLIER = 2.0
MIN_READ_DAYS = 7
SCALE_STEP = 0.15


def plan_cells(target_cpa, daily_budget, creative_count,
               threshold_multiplier=DEFAULT_THRESHOLD_MULTIPLIER):
    """Plan test cells. Returns {cells, warnings} or an honest refusal
    when the budget cannot fund even one threshold read."""
    if not target_cpa or target_cpa <= 0:
        return {"cells": [], "warnings": ["Target CPA not supplied — threshold math cannot be built."]}
    if not daily_budget or daily_budget <= 0:
        return {"cells": [], "warnings": ["Daily budget not supplied — test cells cannot be planned."]}
    threshold = round(target_cpa * threshold_multiplier, 2)
    max_cells_by_budget = int(daily_budget // threshold) if threshold else 0
    warnings = []
    if max_cells_by_budget < 1:
        warnings.append(
            f"Daily budget is below one threshold read ({threshold}) — "
            "raise the budget or give one creative a longer read; do not kill early.")
        return {"cells": [], "warnings": warnings, "threshold_spend": threshold}
    cells = min(int(creative_count or 0), max_cells_by_budget)
    if cells < int(creative_count or 0):
        warnings.append(
            f"The budget funds only {cells} cell(s); keep the remaining creatives queued instead of running everything at once.")
    return {"cells": [{"cell": i + 1, "threshold_spend": threshold,
                       "min_read_days": MIN_READ_DAYS} for i in range(cells)],
            "warnings": warnings, "threshold_spend": threshold}


def judge_cell(spend, conversions, target_cpa, days_run,
               threshold_multiplier=DEFAULT_THRESHOLD_MULTIPLIER):
    """Judge one test cell. Returns a proposal dict; never an action."""
    if not target_cpa or target_cpa <= 0:
        return {"decision": "insufficient_data", "reason": "Target CPA is missing."}
    threshold = target_cpa * threshold_multiplier
    if days_run < MIN_READ_DAYS and spend < threshold:
        return {"decision": "keep_reading",
                "reason": f"The read is still small ({days_run} days, spend {spend}); let it reach the {threshold:.0f} threshold or {MIN_READ_DAYS} days."}
    if spend >= threshold and conversions == 0:
        return {"decision": "kill_proposal",
                "reason": f"Spend passed the threshold ({threshold:.0f}) with 0 conversions — kill proposal for owner approval."}
    if conversions > 0:
        cpa = spend / conversions
        if cpa <= target_cpa and conversions >= 3:
            return {"decision": "graduate_proposal",
                    "reason": f"CPA {cpa:.0f} is within the {target_cpa:.0f} target with {conversions} conversions — proposal to move it to the scale lane."}
        return {"decision": "iterate_proposal",
                "reason": f"CPA {cpa:.0f} is above target or conversions are low ({conversions}) — iterate on the angle or hook."}
    return {"decision": "keep_reading", "reason": "The threshold has not been reached yet."}


def scale_steps(current_budget, steps=3):
    """Staged scale proposals (+15% each). Proposals only."""
    if not current_budget or current_budget <= 0:
        return []
    out, budget = [], float(current_budget)
    for _ in range(steps):
        budget = round(budget * (1 + SCALE_STEP), 2)
        out.append({"proposed_budget": budget,
                    "note": "Each step applies only after owner approval; keep a read window between steps."})
    return out
