"""Optimiser — Role 19 of SH Ads Desk (Step 1, MOCK build).

PROPOSE mode only: this module NEVER changes anything. It returns proposals
for the approval queue. Rules from the brief (Part 2, Optimiser):
- Judge only after CONVERSION_LAG_WINDOW and only with MIN_SPEND / MIN_EVENTS.
- Main metric: cost per QUALIFIED lead (cost per enquiry only as a clearly
  labelled provisional metric when qualified data does not exist yet).
- Confidence check: two-proportion z-test on enquiry rates vs the pooled
  other ads — never raw ranking, never CPC/CTR alone.
- Budgets live at campaign or ad-set level only, never per ad. A budget
  proposal always names the budget-owning object. Pausing an ad is separate.
- A cheap-but-junk lead source is a loser.
- Spend breach vs TOTAL_DAILY_BUDGET_CAP => safety stop proposal.
"""
import math


def _rate(events, impressions):
    return (events / impressions) if impressions else 0.0


def _z_test(events_a, impr_a, events_b, impr_b):
    """Two-proportion z-test. Returns z (positive = A better than B)."""
    if impr_a == 0 or impr_b == 0:
        return 0.0
    p_a, p_b = _rate(events_a, impr_a), _rate(events_b, impr_b)
    p_pool = (events_a + events_b) / (impr_a + impr_b)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / impr_a + 1 / impr_b))
    if se == 0:
        return 0.0
    return (p_a - p_b) / se


def _proposal(kind, ad, what, why, numbers, window_days, budget_effect, target_object):
    return {
        "type": kind,
        "ad_id": ad.get("ad_id") if ad else None,
        "target_object": target_object,
        "what": what,
        "why": why,
        "numbers": numbers,
        "window_days": window_days,
        "budget_effect": budget_effect,
        "requires_approval": True,
        "label": "MOCK proposal — PROPOSE mode, nothing is applied automatically",
    }


def analyse(ads, settings):
    """Analyse MOCK (or later, real) insight rows. Returns a report dict:
    {label, status, safety_stop, proposals, notes, per_ad}"""
    target = float(settings.get("TARGET_COST_PER_QUALIFIED_LEAD") or 0)
    min_spend = float(settings.get("MIN_SPEND") or 0)
    min_events = int(settings.get("MIN_EVENTS") or 0)
    lag_days = int(settings.get("CONVERSION_LAG_WINDOW_DAYS") or 0)
    window = int(settings.get("EVALUATION_WINDOW_DAYS") or 0)
    max_pct = float(settings.get("MAX_BUDGET_CHANGE_PCT") or 0)
    min_gap = int(settings.get("MIN_DAYS_BETWEEN_CHANGES") or 0)
    daily_cap = float(settings.get("TOTAL_DAILY_BUDGET_CAP") or 0)

    proposals, notes, per_ad = [], [], {}
    safety_stop = False

    total_spend = sum(float(a.get("spend") or 0) for a in ads)
    if daily_cap > 0 and total_spend > daily_cap:
        safety_stop = True
        proposals.append(_proposal(
            "SAFETY_STOP", None,
            "Stop automation and pause managed ads (mock) — spend breach",
            "Reported total spend %s exceeds TOTAL_DAILY_BUDGET_CAP %s. "
            "Caps are best-effort because Meta reporting lags; never auto-resume after a breach."
            % (total_spend, daily_cap),
            {"total_spend": total_spend, "daily_cap": daily_cap},
            window, "All managed budgets frozen until the owner reviews", "account"))
        notes.append("SAFETY: spend breach detected — safety stop proposed.")

    if target <= 0:
        notes.append("TARGET_COST_PER_QUALIFIED_LEAD is not set (0/empty) — "
                     "winner/loser judgement is skipped; set it in settings to enable.")

    for ad in ads:
        ad_id = ad.get("ad_id")
        spend = float(ad.get("spend") or 0)
        enquiries = int(ad.get("enquiries") or 0)
        qualified = int(ad.get("qualified_leads") or 0)
        junk = int(ad.get("junk_leads") or 0)
        impr = int(ad.get("impressions") or 0)
        cpq = (spend / qualified) if qualified > 0 else None
        cpe = (spend / enquiries) if enquiries > 0 else None
        per_ad[ad_id] = {
            "spend": spend, "enquiries": enquiries, "qualified_leads": qualified,
            "cost_per_qualified_lead": cpq, "cost_per_enquiry_provisional": cpe,
            "verdict": "not enough data",
        }

        # Conversion-lag gate: never judge fresh ads.
        if int(ad.get("days_since_launch") or 0) < lag_days or ad.get("conversions_lagged_pending"):
            per_ad[ad_id]["verdict"] = "not enough data — inside conversion lag window"
            notes.append("%s: inside conversion lag window (%s days) — not judged."
                         % (ad_id, lag_days))
            continue

        # Thin-data gate.
        if spend < min_spend or enquiries < min_events:
            per_ad[ad_id]["verdict"] = "not enough data"
            notes.append("%s: not enough data (spend %s < MIN_SPEND %s or enquiries %s < MIN_EVENTS %s)."
                         % (ad_id, spend, min_spend, enquiries, min_events))
            continue

        if target <= 0:
            per_ad[ad_id]["verdict"] = "enough data, but no target set — not judged"
            continue

        # Change-frequency gate for budget changes.
        gap_ok = int(ad.get("days_since_last_change") or 0) >= min_gap

        # Fatigue: rising frequency + falling CTR (proposal is a creative
        # refresh, not a budget change, so the gap gate does not apply).
        if (float(ad.get("frequency_end") or 0) > 3.0
                and float(ad.get("ctr_end") or 0) < 0.6 * float(ad.get("ctr_start") or 0)):
            per_ad[ad_id]["verdict"] = "fatigued creative"
            proposals.append(_proposal(
                "PROPOSE_CREATIVE_REFRESH", ad,
                "Refresh the creative for ad %s" % ad_id,
                "Frequency rose %s -> %s while CTR fell %s%% -> %s%% over the window."
                % (ad.get("frequency_start"), ad.get("frequency_end"),
                   ad.get("ctr_start"), ad.get("ctr_end")),
                {"frequency_start": ad.get("frequency_start"),
                 "frequency_end": ad.get("frequency_end"),
                 "ctr_start": ad.get("ctr_start"), "ctr_end": ad.get("ctr_end"),
                 "cost_per_qualified_lead": cpq},
                window, "No budget change; new creative enters the approval queue",
                ad_id))
            continue

        # Cheap-but-junk: plenty of enquiries, (almost) none qualified.
        junk_share = (junk / enquiries) if enquiries else 0.0
        if qualified == 0 and junk_share >= 0.8:
            per_ad[ad_id]["verdict"] = "loser — cheap but junk leads"
            proposals.append(_proposal(
                "PROPOSE_PAUSE", ad,
                "Pause ad %s" % ad_id,
                "Cheap enquiries (%s cost per enquiry, provisional) but %d of %d enquiries "
                "are junk and 0 qualified leads — a cheap junk lead is a loser."
                % (cpe, junk, enquiries),
                {"spend": spend, "enquiries": enquiries, "junk_leads": junk,
                 "qualified_leads": 0, "cost_per_enquiry_provisional": cpe},
                window, "Stops this ad's spend; budgets on %s are unchanged"
                % ad.get("budget_object_id"), ad_id))
            continue

        # Loser: cost per qualified lead well above target (or no qualified
        # leads at all after minimum data).
        if cpq is None or cpq > 2 * target:
            per_ad[ad_id]["verdict"] = "loser"
            proposals.append(_proposal(
                "PROPOSE_PAUSE", ad,
                "Pause ad %s (or reduce its budget via the approval queue)" % ad_id,
                "Cost per qualified lead %s is well above target %s after minimum data."
                % (("n/a (0 qualified leads)" if cpq is None else round(cpq, 2)), target),
                {"spend": spend, "enquiries": enquiries, "qualified_leads": qualified,
                 "cost_per_qualified_lead": cpq, "target": target},
                window, "Pausing stops this ad's spend; budget object %s (%s level) unchanged"
                % (ad.get("budget_object_id"), ad.get("budget_owner")), ad_id))
            continue

        # Winner: CPQ at/below target AND enquiry rate significantly better
        # than the pooled other ads (z > 1.96), never raw ranking alone.
        others = [a for a in ads if a.get("ad_id") != ad_id]
        o_enq = sum(int(a.get("enquiries") or 0) for a in others)
        o_impr = sum(int(a.get("impressions") or 0) for a in others)
        z = _z_test(enquiries, impr, o_enq, o_impr) if others else 0.0
        if cpq is not None and cpq <= target and z > 1.96:
            per_ad[ad_id]["verdict"] = "winner"
            owner = ad.get("budget_owner")
            budget_obj = ad.get("budget_object_id")
            if owner not in ("campaign", "adset"):
                notes.append("%s: winner, but budget owner '%s' is invalid — budget "
                             "proposal skipped (budgets live at campaign/ad-set level only)."
                             % (ad_id, owner))
                continue
            if not gap_ok:
                notes.append("%s: winner, but last change was %s days ago (< MIN_DAYS_BETWEEN_CHANGES %s) — no budget proposal yet."
                             % (ad_id, ad.get("days_since_last_change"), min_gap))
                continue
            if max_pct <= 0:
                notes.append("%s: winner, but MAX_BUDGET_CHANGE_PCT is not set — no budget increase proposed."
                             % ad_id)
                continue
            current = float(ad.get("current_budget") or 0)
            new_budget = round(current * (1 + max_pct / 100.0), 2)
            proposals.append(_proposal(
                "PROPOSE_BUDGET_INCREASE", ad,
                "Increase budget of %s (%s level) from %s to %s" % (budget_obj, owner, current, new_budget),
                "Cost per qualified lead %s beats target %s, and its enquiry rate is "
                "significantly better than the pooled other ads (z=%.2f > 1.96)."
                % (round(cpq, 2), target, z),
                {"spend": spend, "enquiries": enquiries, "qualified_leads": qualified,
                 "cost_per_qualified_lead": round(cpq, 2), "target": target, "z_score": round(z, 2)},
                window, "Budget %s -> %s (+%s%%, the MAX_BUDGET_CHANGE_PCT cap) on %s only"
                % (current, new_budget, max_pct, budget_obj), budget_obj))
            continue

        per_ad[ad_id]["verdict"] = "keep running — no proposal"

    return {
        "label": "MOCK analysis (PROPOSE mode)",
        "status": "safety_stop" if safety_stop else "ok",
        "safety_stop": safety_stop,
        "proposals": proposals,
        "notes": notes,
        "per_ad": per_ad,
    }
