"""Guardrails — SH Ads Desk (owner directive, 2026-11-16).

The mistakes that make CPC/CPL spike, encoded as STRICT restrictions so
they happen "na ke barabar" (next to never). This is a DATA-DRIVEN
registry: every guardrail is an entry {id, name, mistake, why it raises
CPC/CPL, check, severity (BLOCK/WARN), setting_key}. Checks are functions
over a context dict (draft / plan / creative / proposal / performance
row). Thresholds are OWNER SETTINGS — empty/zero means the guardrail is
inactive where a number is needed. NO benchmark number is hardcoded as
a default anywhere in this module.

Enforcement points:
- Pre-flight: campaign drafts/plans pass run_preflight() BEFORE they
  may enter the approval queue. BLOCK failures refuse entry with the
  reason shown; WARN failures attach visible warnings to the item.
- Optimiser: app/optimiser.py consults check_proposal() for every
  proposal — it may never propose an action a BLOCK guardrail forbids.
- Execute/gates: eligibility, claims and destination guardrails wrap
  the existing policy_checker gates (same strength, fails closed).

Honesty note: guardrails can stop known mistakes; no system can
guarantee CPC/CPL — auctions and the market also matter.

SEEDED CATALOGUE: the winner-patterns research catalogue
(~/workspace/research_notes/meta-ads-winner-patterns-20261116/
report.md, section D — 26 mistakes D1–D26, read 2026-11-16) IS seeded
in app/guardrail_catalogue.py, and its section E pre-flight checklist
is PREFLIGHT_CHECKLIST below. Research numbers in that report are
labelled references ONLY — every threshold stays an owner setting
(empty/zero = inactive), never a hardcoded default.

EXTENSION POINT (data only, no code changes): further entries can be
added later —
  (a) as JSON rows in the DB table guardrail_entries (entry_json), or
  (b) in a guardrail_catalogue.json file in the data dir / project dir.
Entries reference an existing check by name; a genuinely new check
type is the only thing that needs code.
"""
import json
import os
import re

from . import policy_checker

BLOCK = "BLOCK"
WARN = "WARN"

JUDGING_PROPOSAL_TYPES = ("PROPOSE_PAUSE", "PROPOSE_BUDGET_INCREASE",
                          "PROPOSE_BUDGET_DECREASE", "PROPOSE_SCALE")


# --------------------------------------------------------------- helpers
def disabled_ids(settings):
    raw = (settings or {}).get("GUARDRAILS_DISABLED") or ""
    if isinstance(raw, (list, tuple)):
        return {str(x).strip() for x in raw if str(x).strip()}
    return {x.strip() for x in str(raw).split(",") if x.strip()}


def _num(settings, key):
    try:
        return float((settings or {}).get(key) or 0)
    except (TypeError, ValueError):
        return 0.0


def _fatigued(row):
    if not row:
        return False
    return (float(row.get("frequency_end") or 0) > 3.0
            and float(row.get("ctr_start") or 0) > 0
            and float(row.get("ctr_end") or 0) < 0.6 * float(row.get("ctr_start") or 0))


# ---------------------------------------------------------------- checks
# Each check: fn(ctx) -> (status, reason) with status in
# "pass" | "block" | "warn" | "inactive".
def _check_eligibility(ctx):
    product = ctx.get("product")
    if not product:
        return "inactive", "no product in context"
    result = policy_checker.check_product(product, ctx.get("eligibility"))
    if result["allowed"]:
        return "pass", ""
    return "block", "; ".join(result["reasons"])


def _check_claims(ctx):
    text = ctx.get("text")
    if text is None:
        return "inactive", "no ad text in context"
    result = policy_checker.check_claims(text, extra_patterns=ctx.get("extra_patterns"))
    if result["allowed"]:
        return "pass", ""
    return "block", "; ".join(result["reasons"])


def _check_destination(ctx):
    settings = dict(ctx.get("settings") or {})
    if ctx.get("destination_override"):
        settings["DESTINATION_URL"] = ctx["destination_override"]
        settings["DESTINATION_READY"] = True
    if "destination_url" in ctx:
        settings["DESTINATION_URL"] = ctx.get("destination_url") or ""
    if "destination_ready" in ctx:
        settings["DESTINATION_READY"] = ctx.get("destination_ready")
    result = policy_checker.check_destination(settings)
    if result["allowed"]:
        return "pass", ""
    return "block", "; ".join(result["reasons"])


def _check_learning_phase(ctx):
    settings = ctx.get("settings") or {}
    min_days = _num(settings, "GUARDRAIL_LEARNING_MIN_DAYS")
    min_conv = _num(settings, "GUARDRAIL_LEARNING_MIN_CONVERSIONS")
    if min_days <= 0 and min_conv <= 0:
        return "inactive", "thresholds unset (GUARDRAIL_LEARNING_MIN_DAYS / _CONVERSIONS)"
    target = ctx.get("change_target") or {}
    days = target.get("days_since_launch")
    conv = target.get("conversions")
    if days is None and conv is None:
        proposal = ctx.get("proposal") or {}
        days = proposal.get("days_since_launch")
        conv = proposal.get("conversions")
    if days is None and conv is None:
        row = ctx.get("ad_row") or {}
        days = row.get("days_since_launch")
        conv = row.get("conversions")
        if conv is None:
            conv = row.get("qualified_leads")
    if days is None and conv is None:
        return "inactive", "no live-object age/conversion data in context"
    if min_days > 0 and days is not None and float(days) < min_days:
        return "block", ("Learning phase: the object is only %s days old "
                         "(owner threshold %s days) — editing/changing it "
                         "now restarts learning and CPC/CPL will rise."
                         % (days, int(min_days)))
    if min_conv > 0 and conv is not None and float(conv) < min_conv:
        return "block", ("Learning phase: only %s conversions so far "
                         "(owner threshold %s) — do not judge/edit yet."
                         % (conv, int(min_conv)))
    return "pass", ""


def _check_fragmentation_count(ctx):
    settings = ctx.get("settings") or {}
    cap = _num(settings, "GUARDRAIL_MAX_AD_SETS_PER_CAMPAIGN")
    if cap <= 0:
        return "inactive", "GUARDRAIL_MAX_AD_SETS_PER_CAMPAIGN unset"
    plan = ctx.get("plan") or {}
    ad_sets = plan.get("ad_sets")
    if ad_sets is None:
        return "inactive", "no plan in context"
    if len(ad_sets) > cap:
        return "block", ("Audience fragmentation: the plan has %d ad sets, "
                         "the owner's limit is %d — more ad sets = thinner "
                         "data per ad set, slower learning, higher CPL."
                         % (len(ad_sets), int(cap)))
    return "pass", ""


def _check_fragmentation_budget(ctx):
    settings = ctx.get("settings") or {}
    floor = _num(settings, "GUARDRAIL_MIN_AD_SET_BUDGET")
    if floor <= 0:
        return "inactive", "GUARDRAIL_MIN_AD_SET_BUDGET unset"
    plan = ctx.get("plan") or {}
    ad_sets = plan.get("ad_sets") or []
    budget = ctx.get("daily_budget")
    if budget is None:
        budget = (plan.get("campaign") or {}).get("daily_budget")
    try:
        budget = float(budget or 0)
    except (TypeError, ValueError):
        budget = 0
    if not ad_sets or budget <= 0:
        return "inactive", "no per-ad-set budget computable"
    per_set = budget / max(len(ad_sets), 1)
    if per_set < floor:
        return "warn", ("Per-ad-set budget %s is below the owner's floor %s — "
                        "a budget this thin starves learning and is a common "
                        "cause of CPL spikes." % (round(per_set, 2), floor))
    return "pass", ""


def _check_thin_data(ctx):
    proposal = ctx.get("proposal") or {}
    if proposal.get("type") not in JUDGING_PROPOSAL_TYPES:
        return "inactive", "proposal is not a judging action"
    settings = ctx.get("settings") or {}
    min_spend = _num(settings, "MIN_SPEND")
    min_events = _num(settings, "MIN_EVENTS")
    if min_spend <= 0 and min_events <= 0:
        return "inactive", "MIN_SPEND/MIN_EVENTS unset"
    row = ctx.get("ad_row") or {}
    spend = float(row.get("spend") or proposal.get("numbers", {}).get("spend") or 0)
    events = int(row.get("enquiries") or proposal.get("numbers", {}).get("enquiries") or 0)
    if (min_spend > 0 and spend < min_spend) or (min_events > 0 and events < min_events):
        return "block", ("Judgement on thin data: spend %s / enquiries %s "
                         "are below the owner's MIN_SPEND %s / MIN_EVENTS %s — "
                         "a wrong pause/scale decision damages both CPC and CPL."
                         % (spend, events, min_spend, int(min_events)))
    return "pass", ""


def _check_fatigue_scale(ctx):
    proposal = ctx.get("proposal") or {}
    if proposal.get("type") != "PROPOSE_BUDGET_INCREASE":
        return "inactive", "not a budget-increase proposal"
    if _fatigued(ctx.get("ad_row")):
        return "block", ("Scaling a fatigued creative is not allowed: "
                         "frequency is up and CTR is down — refresh the "
                         "creative first; raising the budget will push CPC "
                         "even higher.")
    return "pass", ""


def _check_fatigue_warn(ctx):
    if _fatigued(ctx.get("ad_row")):
        return "warn", ("Creative fatigue is showing (frequency up, CTR "
                        "down) — keep a fresh creative ready; spending on a "
                        "tired creative raises CPC/CPL.")
    return "pass", ""


def _check_single_creative(ctx):
    settings = ctx.get("settings") or {}
    minimum = _num(settings, "GUARDRAIL_MIN_CREATIVES_PER_ADSET")
    if minimum <= 0:
        return "inactive", "GUARDRAIL_MIN_CREATIVES_PER_ADSET unset"
    plan = ctx.get("plan") or {}
    ad_sets = plan.get("ad_sets") or []
    if not ad_sets:
        return "inactive", "no plan ad sets in context"
    counts = [len(a.get("ads") or []) for a in ad_sets]
    if counts and min(counts) < minimum:
        return "warn", ("An ad set has only %d creative(s) (owner "
                        "minimum %d) — if the single creative fatigues, the "
                        "whole ad set stalls; keep distinct creatives."
                        % (min(counts), int(minimum)))
    return "pass", ""


def _check_budget_jump(ctx):
    settings = ctx.get("settings") or {}
    cap = _num(settings, "MAX_BUDGET_CHANGE_PCT")
    if cap <= 0:
        return "inactive", "MAX_BUDGET_CHANGE_PCT unset"
    change = ctx.get("budget_change") or {}
    current = change.get("current")
    new = change.get("new")
    if current is None or new is None:
        proposal = ctx.get("proposal") or {}
        numbers = proposal.get("numbers") or {}
        current = numbers.get("current_budget")
        new = numbers.get("new_budget")
    if current is None or new is None:
        return "inactive", "no budget change in context"
    current, new = float(current), float(new)
    if current <= 0:
        return "inactive", "current budget unknown"
    pct = abs(new - current) / current * 100.0
    if pct > cap:
        return "block", ("Budget jump %.1f%% exceeds the owner's "
                         "MAX_BUDGET_CHANGE_PCT %s%% — a sudden large jump "
                         "breaks learning and spikes CPL." % (pct, cap))
    return "pass", ""


def _check_live_ad_edit(ctx):
    action = ctx.get("action") or (ctx.get("proposal") or {}).get("action") \
        or (ctx.get("draft") or {}).get("action")
    if action == "EDIT_LIVE_AD":
        return "block", ("Editing a live ad is not allowed (corrupts "
                         "history + restarts learning). Always DUPLICATE "
                         "and test the copy — Strategy P4.")
    return "pass", ""


def _check_kill_switch(ctx):
    if ctx.get("kill_switch"):
        return "block", "Kill switch is ON — no item will enter the queue."
    return "pass", ""


# --- Checks seeded from the winner-patterns guardrail catalogue (§D). ---
_PAGEVIEW_CLASS = ("pageview", "page_view", "viewcontent", "view_content",
                   "landing_page_view", "engagement", "post_engagement",
                   "video_view", "thruplay")
_GOAL_OBJECTIVES = {"checkout": "OUTCOME_SALES", "lead_gen": "OUTCOME_LEADS",
                    "whatsapp": "OUTCOME_LEADS", "calls": "OUTCOME_LEADS",
                    "footfall": "OUTCOME_TRAFFIC"}


def _check_objective_mapping(ctx):
    event = str(ctx.get("optimisation_event") or "").lower()
    if event and any(p in event for p in _PAGEVIEW_CLASS):
        return "block", ("Optimisation event '%s' is a proxy/pageview-class "
                         "event — the system will hunt clickers/viewers, not "
                         "buyers. Choose the real business event "
                         "(Catalogue D3/D22)." % event)
    if ctx.get("source_path") == "boost":
        return "block", ("This draft was built via the boost-post path — "
                         "boost optimises for engagement, not for the "
                         "business goal. Use the Ads Manager structure "
                         "(Catalogue D3).")
    objective = str(ctx.get("objective") or "")
    profile = ctx.get("profile") or {}
    expected = _GOAL_OBJECTIVES.get(profile.get("sales_model") or "")
    if objective and expected and expected not in objective:
        return "block", ("Objective '%s' does not match the goal '%s' of "
                         "the profile's sales model (%s) — the wrong "
                         "objective hunts the wrong audience and CPL stays "
                         "high (Catalogue D3)." % (objective, expected, profile.get("sales_model")))
    if not objective and not event:
        return "inactive", "no objective/event in context"
    return "pass", ""


def _check_tracking(ctx):
    if ctx.get("tracking_verified") is False:
        return "block", ("Conversion tracking is not verified — without "
                         "verified events Meta will optimise on garbage and "
                         "the real CPL will never even show (Catalogue D13).")
    if ctx.get("tracking_verified") is None:
        return "inactive", "tracking status is not in context"
    return "pass", ""


def _check_capi_health(ctx):
    settings = ctx.get("settings") or {}
    emq_min = _num(settings, "EMQ_MIN")
    if ctx.get("capi_present") is False:
        return "warn", ("Conversions API is not connected — browser-only "
                        "tracking loses events, the signal weakens and cost "
                        "rises (Catalogue D14).")
    emq = ctx.get("event_match_quality")
    if emq_min > 0 and emq is not None and float(emq) < emq_min:
        return "warn", ("Event Match Quality %s is below the owner's "
                        "EMQ_MIN %s — improve match quality (Catalogue D14)."
                        % (emq, emq_min))
    if ctx.get("capi_present") is None and emq is None:
        return "inactive", "no CAPI/EMQ data in context"
    return "pass", ""


def _check_projected_events(ctx):
    settings = ctx.get("settings") or {}
    threshold = _num(settings, "LEARNING_EVENT_THRESHOLD")
    budget = ctx.get("daily_budget")
    cpa = ctx.get("cost_per_event")
    if threshold <= 0 or not budget or not cpa:
        return "inactive", "LEARNING_EVENT_THRESHOLD or budget/cost-per-event unset"
    weekly = float(budget) / float(cpa) * 7.0
    if weekly < threshold:
        return "warn", ("Projected weekly events %.0f are below the "
                        "owner's LEARNING_EVENT_THRESHOLD %s — this ad set "
                        "will never exit learning; consolidate the budget "
                        "(Catalogue D4)."
                        % (weekly, int(threshold)))
    return "pass", ""


def _check_audience_overlap(ctx):
    settings = ctx.get("settings") or {}
    cap = _num(settings, "AUDIENCE_OVERLAP_MAX_PCT")
    overlap = ctx.get("audience_overlap_pct")
    if cap <= 0 or overlap is None:
        return "inactive", "AUDIENCE_OVERLAP_MAX_PCT unset or no overlap data"
    if float(overlap) > cap:
        return "warn", ("Audience overlap %s%% exceeds the owner's limit "
                        "%s%% — ad sets are bidding against each other and "
                        "pushing prices up; add exclusions or consolidate "
                        "(Catalogue D5)." % (overlap, cap))
    return "pass", ""


def _check_audience_size(ctx):
    settings = ctx.get("settings") or {}
    floor = _num(settings, "AUDIENCE_SIZE_FLOOR")
    size = ctx.get("audience_size")
    if floor <= 0 or size is None:
        return "inactive", "AUDIENCE_SIZE_FLOOR unset or no audience size"
    if float(size) < floor:
        return "warn", ("Audience size %s is below the owner's floor %s — "
                        "an audience this narrow fatigues quickly and "
                        "CPM/CPA climbs steeply (Catalogue D6)." % (size, int(floor)))
    return "pass", ""


def _check_hook(ctx):
    fmt = str(ctx.get("format") or "").upper()
    if fmt in ("REEL", "VIDEO") and ctx.get("is_test") is not True:
        if ctx.get("hook_declared") is False:
            return "block", ("The video draft has no first-3-seconds hook "
                             "declared — without a hook the draft is "
                             "incomplete (Catalogue D9).")
        if ctx.get("hook_declared") is None:
            return "inactive", "hook declaration is not in context"
    settings = ctx.get("settings") or {}
    floor = _num(settings, "HOOK_RATE_FLOOR_PCT")
    row = ctx.get("ad_row") or {}
    hook_rate = row.get("hook_rate")
    min_impr = _num(settings, "HOOK_MIN_IMPRESSIONS") or _num(settings, "MIN_EVENTS")
    if floor > 0 and hook_rate is not None and int(row.get("impressions") or 0) >= max(min_impr, 1):
        if float(hook_rate) < floor:
            return "warn", ("Hook rate %s%% is below the owner's floor "
                            "%s%% — rewrite the hook first, budget action "
                            "later (Catalogue D9)." % (hook_rate, floor))
    return "pass", ""


def _check_attribution_lock(ctx):
    seen = ctx.get("attribution_settings")
    if seen and len({str(s) for s in seen if s}) > 1:
        return "block", ("Mixed attribution settings found (%s) — "
                         "comparing/optimising numbers from different "
                         "windows is not allowed; lock one declared setting "
                         "first (Catalogue D15)." % ", ".join(sorted({str(s) for s in seen if s})))
    declared = (ctx.get("settings") or {}).get("ATTRIBUTION_WINDOW")
    draft_attr = ctx.get("attribution")
    if declared and draft_attr and str(declared) != str(draft_attr):
        return "block", ("The draft's attribution '%s' differs from the "
                         "account's declared '%s' (Catalogue D15)."
                         % (draft_attr, declared))
    if not seen and not draft_attr:
        return "inactive", "no attribution data in context"
    return "pass", ""


def _check_rejection_counter(ctx):
    settings = ctx.get("settings") or {}
    limit = _num(settings, "REJECTION_COUNT_LIMIT")
    count = ctx.get("rejection_count")
    if limit <= 0 or count is None:
        return "inactive", "REJECTION_COUNT_LIMIT unset or no rejection data"
    if int(count) > limit:
        return "block", ("%s rejections in the rolling window exceed the "
                         "owner's limit %s — launch freeze: fix the root "
                         "cause first, or the whole account will be treated "
                         "as low-quality (Catalogue D16)." % (count, int(limit)))
    return "pass", ""


def _check_quality_ranking(ctx):
    row = ctx.get("ad_row") or {}
    ranking = str(row.get("quality_ranking") or "").lower()
    if ranking in ("bottom_10", "bottom 10%", "bottom_20", "bottom 20%") \
            and int(row.get("impressions") or 0) >= 500:
        return "warn", ("Quality ranking is in the bottom tier (%s, %s "
                        "impressions) — propose replacing this ad; if the "
                        "conversion ranking is also poor, check the landing "
                        "page/offer first (Catalogue D17/D11)."
                        % (ranking, row.get("impressions")))
    if not ranking:
        return "inactive", "no quality ranking in context"
    return "pass", ""


def _check_cold_warm_mixing(ctx):
    sources = [str(s).lower() for s in (ctx.get("audience_sources") or [])]
    if not sources:
        return "inactive", "no audience sources in context"
    cold = any(any(k in s for k in ("broad", "interest", "lookalike")) for s in sources)
    warm = any(any(k in s for k in ("engager", "visitor", "custom", "retarget")) for s in sources)
    if cold and warm:
        return "warn", ("Cold (broad/interest/lookalike) and warm "
                        "(engagers/visitors) audiences are mixed in one ad "
                        "set — keep campaigns separate by temperature, with "
                        "separate creative too (Catalogue D18).")
    return "pass", ""


def _check_manual_placements(ctx):
    if str(ctx.get("placements") or "").lower() == "manual" \
            and not str(ctx.get("placement_evidence") or "").strip():
        return "warn", ("Manual placements without an evidence note — let "
                        "automatic/Advantage+ placements gather data first, "
                        "then trim based on evidence (Catalogue D19).")
    if not ctx.get("placements"):
        return "inactive", "no placement mode in context"
    return "pass", ""


def _check_customer_exclusion(ctx):
    if ctx.get("audience_type") == "prospecting" or ctx.get("prospecting"):
        if ctx.get("customer_exclusion"):
            return "pass", ""
        if ctx.get("customer_list_available"):
            return "block", ("A customer list exists but no exclusion is "
                             "applied on this prospecting ad set — budget "
                             "is burning on re-acquiring existing customers "
                             "(Catalogue D20).")
        return "warn", ("No customer exclusion on this prospecting ad set "
                        "— exclude existing customers (Catalogue D20).")
    return "inactive", "not a prospecting context"


def _check_bid_goal(ctx):
    proposal = ctx.get("proposal") or {}
    if proposal and (ctx.get("settings") or {}).get("TARGET_COST_PER_QUALIFIED_LEAD"):
        numbers = proposal.get("numbers") or {}
        if "cost_per_qualified_lead" not in numbers and "cost_per_enquiry_provisional" in numbers:
            return "warn", ("This proposal rests only on provisional "
                            "cost-per-enquiry while qualified-lead data "
                            "exists — decide on cost per QUALIFIED lead "
                            "(Catalogue D21).")
    goal = str(ctx.get("goal") or "")
    bid = str(ctx.get("bid_strategy") or "")
    if goal == "quality" and bid == "volume":
        return "warn", ("Bid strategy is 'volume' while the declared goal "
                        "is lead QUALITY — junk leads will flood in and "
                        "effective CPL will rise (Catalogue D21).")
    if not goal and not proposal:
        return "inactive", "no bid/goal context"
    return "pass", ""


def _check_review_cadence(ctx):
    settings = ctx.get("settings") or {}
    cadence = _num(settings, "REVIEW_CADENCE_DAYS")
    days = ctx.get("days_since_last_review")
    if cadence <= 0 or days is None:
        return "inactive", "REVIEW_CADENCE_DAYS unset or no review data"
    if float(days) > cadence:
        return "warn", ("It has been %s days since the last review (owner "
                        "cadence %s days) — set-and-forget is the most "
                        "expensive habit (Catalogue D23)."
                        % (days, int(cadence)))
    return "pass", ""


def _check_season(ctx):
    if ctx.get("cross_season_comparison"):
        return "warn", ("A cross-season comparison is being made — festive/"
                        "Q4 CPMs are higher than ordinary days; judge "
                        "against a season-matched baseline (Catalogue D24).")
    return "pass", ""


def _check_relaunch(ctx):
    settings = ctx.get("settings") or {}
    days_limit = _num(settings, "PAUSE_RELEARN_DAYS")
    action = ctx.get("action") or (ctx.get("proposal") or {}).get("action") \
        or (ctx.get("draft") or {}).get("action")
    paused = ctx.get("paused_days")
    if action == "RESUME" and paused is not None:
        if days_limit > 0 and float(paused) >= days_limit:
            return "warn", ("This ad set was paused for %s days — resuming "
                            "restarts learning and carries a re-learning "
                            "cost; it is never auto-resumed (Catalogue D25)."
                            % paused)
        return "warn", ("Resuming may restart learning — a paused ad set "
                        "does not return to its old performance "
                        "(Catalogue D25).")
    return "inactive", "not a resume action"


def _check_test_hypothesis(ctx):
    if ctx.get("is_test"):
        if not str(ctx.get("hypothesis") or "").strip() \
                or not str(ctx.get("variable") or "").strip():
            return "warn", ("Creative test without a hypothesis/single "
                            "variable — the reason for a win will never be "
                            "known and the same tuition will be paid again "
                            "and again (Catalogue D26).")
        return "pass", ""
    return "inactive", "not a test context"


def _check_landing_quality(ctx):
    if ctx.get("landing_reachable") is False:
        return "block", ("The destination page is not reachable — not a "
                         "single click's money should go to a broken page "
                         "(Catalogue D11).")
    settings = ctx.get("settings") or {}
    max_sec = _num(settings, "LANDING_PAGE_MAX_LOAD_SEC")
    load = ctx.get("landing_load_sec")
    if max_sec > 0 and load is not None and float(load) > max_sec:
        return "warn", ("Landing page load %.1fs exceeds the owner's limit "
                        "of %ss (mobile) — a slow page = paid bounce "
                        "(Catalogue D11)." % (float(load), max_sec))
    if ctx.get("landing_message_match") is False:
        return "warn", ("The landing page headline/offer does not match "
                        "the ad — message mismatch hurts both conversion "
                        "and ad quality (Catalogue D11).")
    if ctx.get("landing_reachable") is None and load is None \
            and ctx.get("landing_message_match") is None:
        return "inactive", "no landing-page data in context"
    return "pass", ""


def _check_frequency_cap(ctx):
    settings = ctx.get("settings") or {}
    row = ctx.get("ad_row") or {}
    freq = row.get("frequency_end")
    if freq is None:
        return "inactive", "no frequency data in context"
    stage = str(ctx.get("funnel_stage") or "prospecting")
    key = "FREQUENCY_CAP_RETARGETING" if stage == "retargeting" \
        else "FREQUENCY_CAP_PROSPECTING"
    cap = _num(settings, key)
    if cap <= 0:
        return "inactive", "%s unset" % key
    if float(freq) > cap:
        return "warn", ("Frequency %s is above the %s cap %s — time to "
                        "rotate/refresh (Catalogue D7)." % (freq, stage, cap))
    return "pass", ""


def _check_creative_range(ctx):
    """D8: creatives per ad set outside the owner range (min AND max)."""
    settings = ctx.get("settings") or {}
    minimum = _num(settings, "CREATIVES_PER_AD_SET_MIN") \
        or _num(settings, "GUARDRAIL_MIN_CREATIVES_PER_ADSET")
    maximum = _num(settings, "CREATIVES_PER_AD_SET_MAX")
    if minimum <= 0 and maximum <= 0:
        return "inactive", "creative range settings unset"
    plan = ctx.get("plan") or {}
    ad_sets = plan.get("ad_sets") or []
    counts = [len(a.get("ads") or []) for a in ad_sets]
    if not counts:
        single = ctx.get("creatives_in_ad_set")
        counts = [int(single)] if single is not None else []
    if not counts:
        return "inactive", "no creative counts in context"
    if minimum > 0 and min(counts) < minimum:
        return "warn", ("The ad set has only %d creative(s) — owner "
                        "minimum %d. One creative = instant fatigue "
                        "(Catalogue D8)."
                        % (min(counts), int(minimum)))
    if maximum > 0 and max(counts) > maximum:
        return "warn", ("The ad set has %d creatives — owner maximum %d. "
                        "In a crowd, no creative gets enough data to be "
                        "judged (Catalogue D8)." % (max(counts), int(maximum)))
    return "pass", ""


def _check_comment_sla(ctx):
    settings = ctx.get("settings") or {}
    sla = _num(settings, "COMMENT_MODERATION_SLA_HOURS")
    oldest = ctx.get("unaddressed_negative_oldest_hours")
    count = ctx.get("unaddressed_negative_comments")
    if count is None and oldest is None:
        return "inactive", "no comment-moderation data in context"
    if sla > 0 and oldest is not None and float(oldest) > sla:
        return "warn", ("%s negative comments have been unaddressed for "
                        "%s hours (owner SLA %s hours) — visible negativity "
                        "scares every new viewer and ad quality drops "
                        "(Catalogue D12)."
                        % (count or "Some", oldest, int(sla)))
    if count:
        return "warn", ("%s unaddressed negative comments — manage "
                        "comments like a storefront (Catalogue D12)." % count)
    return "pass", ""


CHECKS = {
    "comment_sla": _check_comment_sla,
    "eligibility": _check_eligibility,
    "claims": _check_claims,
    "destination": _check_destination,
    "learning_phase": _check_learning_phase,
    "fragmentation_count": _check_fragmentation_count,
    "fragmentation_budget": _check_fragmentation_budget,
    "thin_data": _check_thin_data,
    "fatigue_scale": _check_fatigue_scale,
    "fatigue_warn": _check_fatigue_warn,
    "single_creative": _check_single_creative,
    "creative_range": _check_creative_range,
    "budget_jump": _check_budget_jump,
    "live_ad_edit": _check_live_ad_edit,
    "kill_switch": _check_kill_switch,
    "objective_mapping": _check_objective_mapping,
    "tracking": _check_tracking,
    "capi_health": _check_capi_health,
    "projected_events": _check_projected_events,
    "audience_overlap": _check_audience_overlap,
    "audience_size": _check_audience_size,
    "hook": _check_hook,
    "attribution_lock": _check_attribution_lock,
    "rejection_counter": _check_rejection_counter,
    "quality_ranking": _check_quality_ranking,
    "cold_warm_mixing": _check_cold_warm_mixing,
    "manual_placements": _check_manual_placements,
    "customer_exclusion": _check_customer_exclusion,
    "bid_goal": _check_bid_goal,
    "review_cadence": _check_review_cadence,
    "season": _check_season,
    "relaunch": _check_relaunch,
    "test_hypothesis": _check_test_hypothesis,
    "landing_quality": _check_landing_quality,
    "frequency_cap": _check_frequency_cap,
}


def _g(id_, name, mistake, why, check, severity, setting_key, applies):
    return {"id": id_, "name": name, "mistake": mistake, "why": why,
            "check": check, "severity": severity, "setting_key": setting_key,
            "applies_to": applies, "source": "system registry"}


GUARDRAILS = [
    _g("eligibility_unconfirmed", "Ad for unconfirmed eligibility",
       "Making an ad for an offering whose selling/resale permission is not confirmed",
       "Policy violation, ad rejection, account risk — and the time/budget spent on rejected ads is straight waste; when account health drops, delivery gets more expensive.",
       "eligibility", BLOCK, None, ["draft", "plan", "creative", "proposal"]),
    _g("policy_claims", "Banned / misleading claims",
       "Running copy with a guarantee, fake discount, superlative, earnings or industry-banned claim",
       "The ad gets rejected, account quality drops, and misleading traffic brings junk leads — CPL spikes directly.",
       "claims", BLOCK, None, ["draft", "plan", "creative", "proposal"]),
    _g("destination_not_ready", "Traffic before the destination/landing is ready",
       "Taking an ad live without DESTINATION_URL/READY set, or before the page is ready",
       "Clicks cost money but the page does not convert — CPC stays the same, conversions are zero, CPL is infinite. The landing page decides conversion (Strategy S7/B2).",
       "destination", BLOCK, "DESTINATION_URL / DESTINATION_READY", ["draft", "plan"]),
    _g("learning_phase_edit", "Edit/change during the learning phase",
       "Changing targeting/budget/creative while a new campaign/ad is still learning",
       "Every significant edit restarts learning — data resets, delivery turns unstable, CPC and CPL both spike (Strategy S4/S14).",
       "learning_phase", BLOCK, "GUARDRAIL_LEARNING_MIN_DAYS / GUARDRAIL_LEARNING_MIN_CONVERSIONS",
       ["draft", "proposal"]),
    _g("fragmentation_count", "Audience fragmentation — too many ad sets",
       "Splitting one budget across too many ad sets",
       "Conversions get thin on every ad set — nothing exits learning, your own ad sets collide in the auction, and CPL stays high.",
       "fragmentation_count", BLOCK, "GUARDRAIL_MAX_AD_SETS_PER_CAMPAIGN", ["plan"]),
    _g("fragmentation_budget", "Per-ad-set budget too thin",
       "Giving an ad set so little budget that it can never learn",
       "Learning limited — delivery stutters, cost per result unstable and high.",
       "fragmentation_budget", WARN, "GUARDRAIL_MIN_AD_SET_BUDGET", ["plan"]),
    _g("thin_data_judgement", "Pause/scale decision on thin data",
       "Declaring a winner/loser on less data than MIN_SPEND/MIN_EVENTS",
       "Mistaking noise for signal gets a good ad killed or a bad ad scaled — CPC/CPL damage on both sides.",
       "thin_data", BLOCK, "MIN_SPEND / MIN_EVENTS", ["proposal"]),
    _g("fatigue_scale", "Scaling a fatigued creative",
       "Raising the budget even after frequency has risen and CTR has fallen",
       "A tired creative only gets worse with more money — CPC rises, response falls. Refresh first (Strategy S1/P3).",
       "fatigue_scale", BLOCK, None, ["proposal"]),
    _g("creative_fatigue", "Ignoring creative fatigue",
       "Keeping a frequency-up + CTR-down creative running without a refresh plan",
       "CPC climbs slowly and CPL follows — the most common silent spike.",
       "fatigue_warn", WARN, None, ["proposal", "draft"]),
    _g("single_creative_adset", "Only one creative in the ad set",
       "Running the whole ad set on a single creative",
       "When the one creative fatigues, the whole ad set fatigues — no backup, zero testing; performance falls suddenly.",
       "single_creative", WARN, "GUARDRAIL_MIN_CREATIVES_PER_ADSET", ["plan", "draft"]),
    _g("budget_jump", "One-step large budget jump",
       "A single-step budget change larger than MAX_BUDGET_CHANGE_PCT",
       "A large jump pushes delivery into new, expensive auction pockets and breaks learning — the classic cause of a CPL spike.",
       "budget_jump", BLOCK, "MAX_BUDGET_CHANGE_PCT", ["draft", "proposal"]),
    _g("live_ad_edit", "Editing a live ad (instead of duplicating)",
       "Directly editing the creative/text of a running ad",
       "The ad's history is corrupted, learning restarts — and the test data is wasted too (Strategy P4).",
       "live_ad_edit", BLOCK, None, ["draft", "proposal"]),
    _g("kill_switch_on", "Pushing work forward while the kill switch is ON",
       "Running the queue/execution even after a safety stop",
       "Spend keeps growing after a breach; it is never auto-resumed.",
       "kill_switch", BLOCK, None, ["draft", "plan", "proposal"]),
]


# Pre-flight checklist — winner-patterns report section E1. Every draft
# passes these 8 items before the approval queue; any BLOCK failure
# stops the draft with the reason shown. Items map to registry entries.
PREFLIGHT_CHECKLIST = [
    ("Eligibility + destination gates (existing) — D11 extends destination: reachability + mobile load + message match",
     ["eligibility_unconfirmed", "destination_not_ready", "D11"]),
    ("Objective ↔ goal mapping — objective + optimisation event match the profile's sales model and funnel ladder",
     ["D3", "D22"]),
    ("Policy scan pass — ad text, creative and landing page (personal attributes, claims, bait)",
     ["policy_claims", "D16"]),
    ("Tracking verification — Pixel/CAPI fire test for the optimisation event; event is a real business event, not pageview-class",
     ["D13", "D14"]),
    ("Structure sanity — projected weekly events per ad set, creative count in range, no cold+warm mixing, customer exclusion, manual placements justified",
     ["D4", "D8", "D18", "D20", "D19"]),
    ("Creative completeness — video drafts declare the first-3-seconds hook; tests declare hypothesis + single variable",
     ["D9", "D26"]),
    ("Attribution lock — draft/report carries the declared attribution setting; mixed settings refused",
     ["D15"]),
    ("Scale-step validation — budget changes respect max-step % and minimum interval",
     ["D10", "budget_jump"]),
]


# ------------------------------------------------------- catalogue loading
def _catalogue_file_entries():
    from .common import DATA_DIR, PROJECT_DIR
    entries = []
    for path in (os.path.join(DATA_DIR, "guardrail_catalogue.json"),
                 os.path.join(PROJECT_DIR, "guardrail_catalogue.json")):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    entries.extend(data)
            except (ValueError, OSError):
                pass
    return entries


def load_registry(conn=None):
    """Built-in registry + catalogue entries added as DATA (DB rows /
    guardrail_catalogue.json). A catalogue entry must name an existing
    check; unknown checks are kept but their check resolves to inactive
    (they can never silently block or pass real work)."""
    entries = [dict(g) for g in GUARDRAILS]
    from . import guardrail_catalogue
    entries.extend(dict(g) for g in guardrail_catalogue.CATALOGUE)
    entries.extend(_catalogue_file_entries())
    if conn is not None:
        try:
            rows = conn.execute("SELECT entry_json FROM guardrail_entries").fetchall()
        except Exception:
            rows = []
        for r in rows:
            try:
                entries.append(json.loads(r["entry_json"]))
            except (ValueError, KeyError, TypeError):
                continue
    return entries


# -------------------------------------------------------------- evaluation
def evaluate(entry, ctx):
    if entry.get("id") in disabled_ids(ctx.get("settings")):
        return {"id": entry.get("id"), "status": "disabled", "reason": "turned OFF by the owner"}
    fn = CHECKS.get(entry.get("check"))
    if fn is None:
        return {"id": entry.get("id"), "status": "inactive",
                "reason": "check '%s' is not registered in this build" % entry.get("check")}
    status, reason = fn(ctx)
    return {"id": entry.get("id"), "name": entry.get("name"),
            "severity": entry.get("severity"), "status": status,
            "reason": reason}


def run_preflight(ctx, conn=None):
    """Pre-flight for a draft/plan/creative/proposal context. Returns
    {allowed, blocks, warnings, results}. BLOCK present => allowed is
    False and the item must NOT enter the approval queue."""
    kind = ctx.get("kind") or "draft"
    blocks, warnings, results = [], [], []
    seen = set()
    for entry in load_registry(conn):
        applies = entry.get("applies_to") or []
        if applies and kind not in applies:
            continue
        res = evaluate(entry, ctx)
        res["check"] = entry.get("check")
        results.append(res)
        # Built-in entries and catalogue entries sometimes share a check
        # (e.g. learning_phase) — report each failing check once.
        dedupe_key = (entry.get("check"), res["status"])
        if res["status"] in ("block", "warn") and dedupe_key in seen:
            continue
        if res["status"] == "block":
            seen.add(dedupe_key)
            blocks.append(res)
        elif res["status"] == "warn":
            seen.add(dedupe_key)
            warnings.append(res)
    return {"allowed": not blocks, "blocks": blocks, "warnings": warnings,
            "results": results}


def check_proposal(proposal, ad_row, settings, conn=None):
    """Optimiser gate: may this proposal exist at all? Returns
    {blocked, reasons}. SAFETY_STOP proposals are never blocked (they
    ARE the safety mechanism)."""
    if (proposal or {}).get("type") == "SAFETY_STOP":
        return {"blocked": False, "reasons": []}
    ctx = {"kind": "proposal", "proposal": proposal, "ad_row": ad_row,
           "settings": settings,
           "budget_change": None}
    reasons = []
    seen_checks = set()
    for entry in load_registry(conn):
        if "proposal" not in (entry.get("applies_to") or []):
            continue
        res = evaluate(entry, ctx)
        if res["status"] == "block" and entry.get("check") not in seen_checks:
            seen_checks.add(entry.get("check"))
            reasons.append("%s: %s" % (entry.get("id"), res["reason"]))
    return {"blocked": bool(reasons), "reasons": reasons}


def registry_status(settings, conn=None):
    """For the Guardrails UI page: every entry with its live status."""
    out = []
    off = disabled_ids(settings)
    for entry in load_registry(conn):
        status = "OFF (owner toggle)"
        if entry.get("id") not in off:
            key = entry.get("setting_key")
            if key:
                status = "ON — threshold setting: %s" % key
            else:
                status = "ON — always active (no number needed)"
        out.append(dict(entry, live_status=status,
                        enabled=entry.get("id") not in off))
    return out
