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
        return "block", ("Learning phase: object sirf %s din purana hai "
                         "(owner threshold %s din) — abhi edit/change karne "
                         "se learning restart hogi aur CPC/CPL badhega."
                         % (days, int(min_days)))
    if min_conv > 0 and conv is not None and float(conv) < min_conv:
        return "block", ("Learning phase: sirf %s conversions hue hain "
                         "(owner threshold %s) — judge/edit abhi mat karo."
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
        return "block", ("Audience fragmentation: plan me %d ad sets hain, "
                         "owner ki limit %d hai — zyada ad sets = har ad set "
                         "par data patla, learning slow, CPL high."
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
        return "warn", ("Per-ad-set budget %s owner ke floor %s se kam hai — "
                        "itna patla budget learning ko bhooka rakhta hai, "
                        "CPL spike ka common kaaran." % (round(per_set, 2), floor))
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
        return "block", ("Thin data par judgement: spend %s / enquiries %s "
                         "owner ke MIN_SPEND %s / MIN_EVENTS %s se kam — "
                         "galat pause/scale decision CPC/CPL dono bigaadta hai."
                         % (spend, events, min_spend, int(min_events)))
    return "pass", ""


def _check_fatigue_scale(ctx):
    proposal = ctx.get("proposal") or {}
    if proposal.get("type") != "PROPOSE_BUDGET_INCREASE":
        return "inactive", "not a budget-increase proposal"
    if _fatigued(ctx.get("ad_row")):
        return "block", ("Fatigued creative ko scale karna mana hai: "
                         "frequency up + CTR down hai — pehle creative "
                         "refresh karo, budget badhana CPC aur badhayega.")
    return "pass", ""


def _check_fatigue_warn(ctx):
    if _fatigued(ctx.get("ad_row")):
        return "warn", ("Creative fatigue dikh raha hai (frequency up, CTR "
                        "down) — naya creative ready rakho; thake hue "
                        "creative par kharch CPC/CPL badhata hai.")
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
        return "warn", ("Ek ad set me sirf %d creative(s) hain (owner "
                        "minimum %d) — ek hi creative thakta hai to poora "
                        "ad set ruk jata hai; distinct creatives rakho."
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
        return "block", ("Budget jump %.1f%% owner ki MAX_BUDGET_CHANGE_PCT "
                         "%s%% se zyada hai — achanak bada jump learning "
                         "todta hai aur CPL spike karta hai." % (pct, cap))
    return "pass", ""


def _check_live_ad_edit(ctx):
    action = ctx.get("action") or (ctx.get("proposal") or {}).get("action") \
        or (ctx.get("draft") or {}).get("action")
    if action == "EDIT_LIVE_AD":
        return "block", ("Live ad ko edit karna mana hai (history corrupt "
                         "+ learning restart). Hamesha DUPLICATE karke "
                         "test karo — Strategy P4.")
    return "pass", ""


def _check_kill_switch(ctx):
    if ctx.get("kill_switch"):
        return "block", "Kill switch ON hai — koi item queue me nahi jayega."
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
        return "block", ("Optimisation event '%s' ek proxy/pageview-class "
                         "event hai — system click/view waalo ko dhundhega, "
                         "buyers ko nahi. Asli business event chuno "
                         "(Catalogue D3/D22)." % event)
    if ctx.get("source_path") == "boost":
        return "block", ("Boost-post path se draft bana hai — boost "
                         "engagement ke liye optimise karta hai, business "
                         "goal ke liye nahi. Ads Manager structure use karo "
                         "(Catalogue D3).")
    objective = str(ctx.get("objective") or "")
    profile = ctx.get("profile") or {}
    expected = _GOAL_OBJECTIVES.get(profile.get("sales_model") or "")
    if objective and expected and expected not in objective:
        return "block", ("Objective '%s' profile ke sales model (%s) ke "
                         "goal '%s' se match nahi karta — galat objective "
                         "galat audience dhundhta hai, CPL high rehta hai "
                         "(Catalogue D3)." % (objective, profile.get("sales_model"), expected))
    if not objective and not event:
        return "inactive", "no objective/event in context"
    return "pass", ""


def _check_tracking(ctx):
    if ctx.get("tracking_verified") is False:
        return "block", ("Conversion tracking verify nahi hua — bina "
                         "verified events ke Meta garbage par optimise "
                         "karega aur asli CPL dikhega hi nahi (Catalogue D13).")
    if ctx.get("tracking_verified") is None:
        return "inactive", "tracking status context me nahi hai"
    return "pass", ""


def _check_capi_health(ctx):
    settings = ctx.get("settings") or {}
    emq_min = _num(settings, "EMQ_MIN")
    if ctx.get("capi_present") is False:
        return "warn", ("Conversions API connected nahi hai — browser-only "
                        "tracking events kho deta hai, signal kamzor, cost "
                        "zyada (Catalogue D14).")
    emq = ctx.get("event_match_quality")
    if emq_min > 0 and emq is not None and float(emq) < emq_min:
        return "warn", ("Event Match Quality %s owner ke EMQ_MIN %s se kam "
                        "hai — match quality badhao (Catalogue D14)."
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
        return "inactive", "LEARNING_EVENT_THRESHOLD ya budget/cost-per-event unset"
    weekly = float(budget) / float(cpa) * 7.0
    if weekly < threshold:
        return "warn", ("Projected weekly events %.0f owner ke "
                        "LEARNING_EVENT_THRESHOLD %s se kam — ye ad set "
                        "learning se bahar hi nahi aayega; budget "
                        "consolidate karo (Catalogue D4)."
                        % (weekly, int(threshold)))
    return "pass", ""


def _check_audience_overlap(ctx):
    settings = ctx.get("settings") or {}
    cap = _num(settings, "AUDIENCE_OVERLAP_MAX_PCT")
    overlap = ctx.get("audience_overlap_pct")
    if cap <= 0 or overlap is None:
        return "inactive", "AUDIENCE_OVERLAP_MAX_PCT unset ya overlap data nahi"
    if float(overlap) > cap:
        return "warn", ("Audience overlap %s%% owner ki limit %s%% se zyada "
                        "— ad sets ek dusre ke against bid karke prices "
                        "badha rahe hain; exclusions ya consolidation "
                        "karo (Catalogue D5)." % (overlap, cap))
    return "pass", ""


def _check_audience_size(ctx):
    settings = ctx.get("settings") or {}
    floor = _num(settings, "AUDIENCE_SIZE_FLOOR")
    size = ctx.get("audience_size")
    if floor <= 0 or size is None:
        return "inactive", "AUDIENCE_SIZE_FLOOR unset ya audience size nahi"
    if float(size) < floor:
        return "warn", ("Audience size %s owner ke floor %s se chhota — "
                        "itni tang audience jaldi thakti hai, CPM/CPA "
                        "steeply chadhta hai (Catalogue D6)." % (size, int(floor)))
    return "pass", ""


def _check_hook(ctx):
    fmt = str(ctx.get("format") or "").upper()
    if fmt in ("REEL", "VIDEO") and ctx.get("is_test") is not True:
        if ctx.get("hook_declared") is False:
            return "block", ("Video draft ka first-3-seconds hook declare "
                             "nahi hai — bina hook ke draft incomplete hai "
                             "(Catalogue D9).")
        if ctx.get("hook_declared") is None:
            return "inactive", "hook declaration context me nahi"
    settings = ctx.get("settings") or {}
    floor = _num(settings, "HOOK_RATE_FLOOR_PCT")
    row = ctx.get("ad_row") or {}
    hook_rate = row.get("hook_rate")
    min_impr = _num(settings, "HOOK_MIN_IMPRESSIONS") or _num(settings, "MIN_EVENTS")
    if floor > 0 and hook_rate is not None and int(row.get("impressions") or 0) >= max(min_impr, 1):
        if float(hook_rate) < floor:
            return "warn", ("Hook rate %s%% owner ke floor %s%% se kam — "
                            "pehle hook rewrite karo, budget action baad me "
                            "(Catalogue D9)." % (hook_rate, floor))
    return "pass", ""


def _check_attribution_lock(ctx):
    seen = ctx.get("attribution_settings")
    if seen and len({str(s) for s in seen if s}) > 1:
        return "block", ("Mixed attribution settings mile (%s) — alag "
                         "windows ke numbers compare/optimise karna "
                         "mana hai; pehle ek declared setting par lock "
                         "karo (Catalogue D15)." % ", ".join(sorted({str(s) for s in seen if s})))
    declared = (ctx.get("settings") or {}).get("ATTRIBUTION_WINDOW")
    draft_attr = ctx.get("attribution")
    if declared and draft_attr and str(declared) != str(draft_attr):
        return "block", ("Draft ka attribution '%s' account ke declared "
                         "'%s' se alag hai (Catalogue D15)."
                         % (draft_attr, declared))
    if not seen and not draft_attr:
        return "inactive", "no attribution data in context"
    return "pass", ""


def _check_rejection_counter(ctx):
    settings = ctx.get("settings") or {}
    limit = _num(settings, "REJECTION_COUNT_LIMIT")
    count = ctx.get("rejection_count")
    if limit <= 0 or count is None:
        return "inactive", "REJECTION_COUNT_LIMIT unset ya rejection data nahi"
    if int(count) > limit:
        return "block", ("Rolling window me %s rejections owner ki limit "
                         "%s se zyada — launch freeze: pehle root cause "
                         "fix karo, warna poora account low-quality "
                         "mana jayega (Catalogue D16)." % (count, int(limit)))
    return "pass", ""


def _check_quality_ranking(ctx):
    row = ctx.get("ad_row") or {}
    ranking = str(row.get("quality_ranking") or "").lower()
    if ranking in ("bottom_10", "bottom 10%", "bottom_20", "bottom 20%") \
            and int(row.get("impressions") or 0) >= 500:
        return "warn", ("Quality ranking bottom tier me hai (%s, %s "
                        "impressions) — is ad ko replace karne ka "
                        "proposal banao; conversion-ranking kharab ho "
                        "to pehle landing page/offer dekho (Catalogue "
                        "D17/D11)." % (ranking, row.get("impressions")))
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
        return "warn", ("Ek hi ad set me cold (broad/interest/lookalike) "
                        "aur warm (engagers/visitors) audience mix hai — "
                        "temperature ke hisaab se campaigns alag rakho, "
                        "creative bhi alag (Catalogue D18).")
    return "pass", ""


def _check_manual_placements(ctx):
    if str(ctx.get("placements") or "").lower() == "manual" \
            and not str(ctx.get("placement_evidence") or "").strip():
        return "warn", ("Manual placements bina evidence note ke — pehle "
                        "automatic/Advantage+ placements se data aane do, "
                        "phir evidence par trim karo (Catalogue D19).")
    if not ctx.get("placements"):
        return "inactive", "no placement mode in context"
    return "pass", ""


def _check_customer_exclusion(ctx):
    if ctx.get("audience_type") == "prospecting" or ctx.get("prospecting"):
        if ctx.get("customer_exclusion"):
            return "pass", ""
        if ctx.get("customer_list_available"):
            return "block", ("Customer list maujood hai phir bhi "
                             "prospecting ad set me exclusion nahi laga — "
                             "purane customers ko dobara kharidne me "
                             "budget jal raha hai (Catalogue D20).")
        return "warn", ("Prospecting ad set me customer exclusion nahi "
                        "dikha — existing customers ko exclude karo "
                        "(Catalogue D20).")
    return "inactive", "not a prospecting context"


def _check_bid_goal(ctx):
    proposal = ctx.get("proposal") or {}
    if proposal and (ctx.get("settings") or {}).get("TARGET_COST_PER_QUALIFIED_LEAD"):
        numbers = proposal.get("numbers") or {}
        if "cost_per_qualified_lead" not in numbers and "cost_per_enquiry_provisional" in numbers:
            return "warn", ("Proposal sirf provisional cost-per-enquiry "
                            "par hai jabki qualified-lead data maujood "
                            "hai — faisla cost per QUALIFIED lead par "
                            "ho (Catalogue D21).")
    goal = str(ctx.get("goal") or "")
    bid = str(ctx.get("bid_strategy") or "")
    if goal == "quality" and bid == "volume":
        return "warn", ("Bid strategy 'volume' hai jabki declared goal "
                        "lead QUALITY hai — junk leads flood honge, "
                        "effective CPL badhega (Catalogue D21).")
    if not goal and not proposal:
        return "inactive", "no bid/goal context"
    return "pass", ""


def _check_review_cadence(ctx):
    settings = ctx.get("settings") or {}
    cadence = _num(settings, "REVIEW_CADENCE_DAYS")
    days = ctx.get("days_since_last_review")
    if cadence <= 0 or days is None:
        return "inactive", "REVIEW_CADENCE_DAYS unset ya review data nahi"
    if float(days) > cadence:
        return "warn", ("Pichhle review ko %s din ho gaye (owner cadence "
                        "%s din) — set-and-forget sabse mehngi aadat hai "
                        "(Catalogue D23)." % (days, int(cadence)))
    return "pass", ""


def _check_season(ctx):
    if ctx.get("cross_season_comparison"):
        return "warn", ("Cross-season comparison ho raha hai — festive/"
                        "Q4 ke CPMs aam dinon se zyada hote hain; "
                        "verdict season-matched baseline par do "
                        "(Catalogue D24).")
    return "pass", ""


def _check_relaunch(ctx):
    settings = ctx.get("settings") or {}
    days_limit = _num(settings, "PAUSE_RELEARN_DAYS")
    action = ctx.get("action") or (ctx.get("proposal") or {}).get("action") \
        or (ctx.get("draft") or {}).get("action")
    paused = ctx.get("paused_days")
    if action == "RESUME" and paused is not None:
        if days_limit > 0 and float(paused) >= days_limit:
            return "warn", ("Ye ad set %s din se paused tha — resume par "
                            "learning restart hogi aur re-learning ki "
                            "cost lagegi; kabhi auto-resume nahi hota "
                            "(Catalogue D25)." % paused)
        return "warn", ("Resume par learning restart ho sakti hai — "
                        "paused ad set purani performance par wapas "
                        "nahi aata (Catalogue D25).")
    return "inactive", "not a resume action"


def _check_test_hypothesis(ctx):
    if ctx.get("is_test"):
        if not str(ctx.get("hypothesis") or "").strip() \
                or not str(ctx.get("variable") or "").strip():
            return "warn", ("Creative test bina hypothesis/single-variable "
                            "ke — jeet ka kaaran kabhi pata nahi chalega, "
                            "wahi tuition baar-baar lagegi (Catalogue D26).")
        return "pass", ""
    return "inactive", "not a test context"


def _check_landing_quality(ctx):
    if ctx.get("landing_reachable") is False:
        return "block", ("Destination page reachable nahi hai — toote hue "
                         "page par ek bhi click ka paisa nahi (Catalogue D11).")
    settings = ctx.get("settings") or {}
    max_sec = _num(settings, "LANDING_PAGE_MAX_LOAD_SEC")
    load = ctx.get("landing_load_sec")
    if max_sec > 0 and load is not None and float(load) > max_sec:
        return "warn", ("Landing page load %.1fs owner ki limit %ss se "
                        "zyada (mobile) — slow page = paid bounce "
                        "(Catalogue D11)." % (float(load), max_sec))
    if ctx.get("landing_message_match") is False:
        return "warn", ("Landing page ka headline/offer ad se match nahi "
                        "karta — message mismatch conversion aur ad "
                        "quality dono girata hai (Catalogue D11).")
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
        return "warn", ("Frequency %s %s cap %s se upar — rotation/refresh "
                        "ka time hai (Catalogue D7)." % (freq, stage, cap))
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
        return "warn", ("Ad set me sirf %d creative(s) — owner minimum %d. "
                        "Ek creative = turant fatigue (Catalogue D8)."
                        % (min(counts), int(minimum)))
    if maximum > 0 and max(counts) > maximum:
        return "warn", ("Ad set me %d creatives — owner maximum %d. "
                        "Bheed me kisi creative ko judge karne layak data "
                        "nahi milta (Catalogue D8)." % (max(counts), int(maximum)))
    return "pass", ""


def _check_comment_sla(ctx):
    settings = ctx.get("settings") or {}
    sla = _num(settings, "COMMENT_MODERATION_SLA_HOURS")
    oldest = ctx.get("unaddressed_negative_oldest_hours")
    count = ctx.get("unaddressed_negative_comments")
    if count is None and oldest is None:
        return "inactive", "no comment-moderation data in context"
    if sla > 0 and oldest is not None and float(oldest) > sla:
        return "warn", ("%s negative comments %s ghante se unaddressed "
                        "hain (owner SLA %s ghante) — visible negativity "
                        "har naye viewer ko daraati hai aur ad quality "
                        "girti hai (Catalogue D12)."
                        % (count or "Kuch", oldest, int(sla)))
    if count:
        return "warn", ("%s unaddressed negative comments hain — storefront "
                        "ki tarah comments sambhalo (Catalogue D12)." % count)
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
    _g("eligibility_unconfirmed", "Unconfirmed eligibility par ad",
       "Jis offering ki selling/resale permission confirm nahi, uska ad banana",
       "Policy violation, ad rejection, account risk — aur reject hue ads par laga time/budget seedha waste; account health bigadti hai to delivery mehngi hoti hai.",
       "eligibility", BLOCK, None, ["draft", "plan", "creative", "proposal"]),
    _g("policy_claims", "Banned / misleading claims",
       "Guarantee, fake discount, superlative, earnings ya industry-banned claim wali copy chalana",
       "Ad reject hota hai, account quality girti hai, aur misleading traffic junk leads laata hai — CPL seedha spike.",
       "claims", BLOCK, None, ["draft", "plan", "creative", "proposal"]),
    _g("destination_not_ready", "Destination/landing ready hue bina traffic",
       "DESTINATION_URL/READY set hue bina ya page ready hue bina ad live karna",
       "Click ka paisa lagta hai par page convert nahi karta — CPC wahi, conversions zero, CPL infinite. Landing page hi conversion tay karta hai (Strategy S7/B2).",
       "destination", BLOCK, "DESTINATION_URL / DESTINATION_READY", ["draft", "plan"]),
    _g("learning_phase_edit", "Learning phase me edit/change",
       "Naya campaign/ad seekh raha ho tabhi targeting/budget/creative badal dena",
       "Har significant edit learning restart karta hai — data reset, delivery unstable, CPC/CPL dono spike (Strategy S4/S14).",
       "learning_phase", BLOCK, "GUARDRAIL_LEARNING_MIN_DAYS / GUARDRAIL_LEARNING_MIN_CONVERSIONS",
       ["draft", "proposal"]),
    _g("fragmentation_count", "Audience fragmentation — bahut zyada ad sets",
       "Ek hi budget ko bahut saare ad sets me baant dena",
       "Har ad set par conversions patle — koi learning se bahar nahi aata, auction me apne hi ad sets takrate hain, CPL high rehta hai.",
       "fragmentation_count", BLOCK, "GUARDRAIL_MAX_AD_SETS_PER_CAMPAIGN", ["plan"]),
    _g("fragmentation_budget", "Per-ad-set budget bahut patla",
       "Ad set ko itna kam budget dena ki wo seekh hi na sake",
       "Learning limited — delivery ruk-ruk kar, cost per result unstable aur high.",
       "fragmentation_budget", WARN, "GUARDRAIL_MIN_AD_SET_BUDGET", ["plan"]),
    _g("thin_data_judgement", "Thin data par pause/scale ka faisla",
       "MIN_SPEND/MIN_EVENTS se kam data par winner/loser ghoshit karna",
       "Shor ko signal samajhkar achha ad band ya kharab ad scale ho jata hai — dono taraf CPC/CPL ka nuksan.",
       "thin_data", BLOCK, "MIN_SPEND / MIN_EVENTS", ["proposal"]),
    _g("fatigue_scale", "Fatigued creative ko scale karna",
       "Frequency badh gaya aur CTR gir gaya, phir bhi budget badhana",
       "Thaka hua creative zyada paiso me aur kharab hota hai — CPC badhta hai, response girta hai. Pehle refresh (Strategy S1/P3).",
       "fatigue_scale", BLOCK, None, ["proposal"]),
    _g("creative_fatigue", "Creative fatigue ignore karna",
       "Frequency up + CTR down wale creative ko bina refresh plan ke chalate rehna",
       "Dheere-dheere CPC chadhta hai aur CPL follow karta hai — sabse common silent spike.",
       "fatigue_warn", WARN, None, ["proposal", "draft"]),
    _g("single_creative_adset", "Ad set me ek hi creative",
       "Poora ad set ek hi creative par chalana",
       "Ek creative thaka to poora ad set thaka — koi backup nahi, testing bhi zero; performance achanak girti hai.",
       "single_creative", WARN, "GUARDRAIL_MIN_CREATIVES_PER_ADSET", ["plan", "draft"]),
    _g("budget_jump", "Ek baar me bada budget jump",
       "MAX_BUDGET_CHANGE_PCT se zyada ka ek-step budget badlav",
       "Bada jump delivery ko naye, mehnge auction pockets me dhakelta hai aur learning todta hai — CPL spike ka classic kaaran.",
       "budget_jump", BLOCK, "MAX_BUDGET_CHANGE_PCT", ["draft", "proposal"]),
    _g("live_ad_edit", "Live ad ko edit karna (duplicate ki jagah)",
       "Chalte hue ad ka creative/text seedha edit kar dena",
       "Ad ki history corrupt hoti hai, learning restart — test ka data bhi bekaar (Strategy P4).",
       "live_ad_edit", BLOCK, None, ["draft", "proposal"]),
    _g("kill_switch_on", "Kill switch ON hote hue kaam aage badhana",
       "Safety stop ke baad bhi queue/execution chalana",
       "Breach ke baad kharch aur badhta hai; kabhi auto-resume nahi hota.",
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
        return {"id": entry.get("id"), "status": "disabled", "reason": "owner ne OFF kiya hai"}
    fn = CHECKS.get(entry.get("check"))
    if fn is None:
        return {"id": entry.get("id"), "status": "inactive",
                "reason": "check '%s' is build me registered nahi hai" % entry.get("check")}
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
                status = "ON — hamesha active (koi number nahi chahiye)"
        out.append(dict(entry, live_status=status,
                        enabled=entry.get("id") not in off))
    return out
