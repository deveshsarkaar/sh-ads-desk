"""The 20 logical roles of SH Ads Desk (Step 1, MOCK build).

Each role is a separate function with its own auditable output (the
orchestrator logs every output separately). Cheap roles use templates and
facts stated in the brief — NO external API calls, NO LLM keys, NO secrets.
Every output is labelled MOCK or UNTESTED honestly.
"""
from datetime import date

from . import mock_insights
from . import optimiser as optimiser_mod
from . import policy_checker
from .mock_meta import MockMetaClient

LABEL = "MOCK (Step 1)"


def _out(role, output):
    return {"role": role, "label": LABEL, "output": output}


def _business_name(profile):
    return (profile or {}).get("name") or "Software Hub"


# ---------- A. Research and Strategy ----------
def role_01_audience_research(goal="both", profile=None):
    if profile is not None and profile.get("industry_preset") not in (None, "software_digital"):
        from . import industries
        preset = industries.get_preset(profile.get("industry_preset"))
        hints = preset.get("audience_hints", [])
        segments = {
            "customers": [
                {"segment": h, "pain_points": [], "interests": [],
                 "source": "industry preset audience hint (editable starting point)"}
                for h in hints],
            "note": "Profile '%s' (%s) — segments seeded from the industry "
                    "preset + profile target text: %s"
                    % (profile.get("name"), profile.get("industry"),
                       profile.get("target_text") or "—"),
            "research_checklist": preset.get("research_checklist", []),
        }
        return _out("01_audience_research", segments)
    segments = {
        "customers": [
            {"segment": "students", "pain_points": ["AI tools costly on a student budget",
             "needs tools for projects and placements"], "interests": ["AI tools", "coding", "productivity"]},
            {"segment": "freelancers", "pain_points": ["per-tool subscriptions add up",
             "needs client-ready output fast"], "interests": ["design tools", "AI writing", "video"]},
            {"segment": "creators", "pain_points": ["editing and content tools are expensive",
             "needs a steady content workflow"], "interests": ["video editing", "AI voice", "design"]},
        ],
        "resellers": [
            {"segment": "bot owners", "pain_points": ["needs a reliable catalog and supply",
             "margin pressure"], "interests": ["reseller API", "software catalog"]},
            {"segment": "agencies", "pain_points": ["needs seats for client teams",
             "billing simplicity"], "interests": ["team plans", "productivity suites"]},
        ],
    }
    if goal in segments:
        segments = {goal: segments[goal]}
    return _out("01_audience_research", segments)


def role_02_competitor_watch(profile_slug="software-hub", conn=None, profile_id=None):
    from . import competitor_seeds
    entries = None
    if conn is not None and profile_id is not None:
        from . import profiles as profiles_mod
        entries = profiles_mod.list_competitors(profile_id, conn)
    if entries is None:
        entries = competitor_seeds.seeded_for(profile_slug)
    return _out("02_competitor_watch", {
        "status": "UNTESTED in Step 1 — no live Ad Library pull is wired. "
                  "Manual check of the public Meta Ad Library is the Step 1 method; "
                  "any API route must be eligibility-checked in Step 2. "
                  "Entries below are the profile's competitor list (owner-editable; "
                  "seeded entries carry their 'source') — tracked for "
                  "inspiration/research from public sources only; figures on "
                  "them are as the owner shared, not system-verified.",
        "entries": entries,
    })


def role_03_trend_analysis():
    return _out("03_trend_analysis", {
        "status": "UNTESTED in Step 1 — official-source trend watch starts in Step 2. "
                  "No strategy change is ever made automatically from a trend.",
        "official_sources": [
            "https://www.facebook.com/business/help (Meta Business Help Center)",
            "https://developers.facebook.com/docs/marketing-api/changelog (Marketing API changelog)",
            "https://transparency.meta.com/policies/ad-standards/ (Meta Advertising Standards)",
        ],
        "changes": [],
    })


_FUNNEL_BY_SALES_MODEL = {
    "checkout": ["ad", "product/store page", "checkout", "paid order", "repeat order"],
    "lead_gen": ["ad", "enquiry (message/lead)", "qualification", "conversation", "order"],
    "whatsapp": ["ad", "WhatsApp chat", "qualification", "order"],
    "calls": ["ad", "call", "booking", "job/order done"],
    "footfall": ["ad", "direction/call", "store visit", "purchase"],
}


def role_04_funnel_strategy(profile=None):
    if profile is not None:
        overrides = profile.get("settings_overrides") or {}
        stages = overrides.get("FUNNEL_STAGES")
        model = profile.get("sales_model") or "lead_gen"
        return _out("04_funnel_strategy", {
            "business": profile.get("name"), "industry": profile.get("industry"),
            "sales_model": model,
            "funnel": ([s.strip() for s in str(stages).split(">")] if stages
                       else _FUNNEL_BY_SALES_MODEL.get(model,
                                                       _FUNNEL_BY_SALES_MODEL["lead_gen"])),
            "lead_stages": overrides.get("LEAD_STAGES", []),
            "note": "Funnel/KPI defaults come from the profile's settings "
                    "overrides (seeded by the industry preset, editable) — "
                    "kabhi code me hardcoded nahi.",
        })
    return _out("04_funnel_strategy", {
        "customers": ["ad", "enquiry (message/lead)", "product page / order", "paid order"],
        "resellers": ["ad", "catalog / API info", "conversation", "reseller application"],
        "note": "Separate campaigns for customers and resellers (brief process rule).",
    })


def role_05_budget_planning(settings):
    caps = {
        "TOTAL_DAILY_BUDGET_CAP": settings.get("TOTAL_DAILY_BUDGET_CAP"),
        "PER_CAMPAIGN_CAP": settings.get("PER_CAMPAIGN_CAP"),
        "LIFETIME_CAP": settings.get("LIFETIME_CAP"),
    }
    if not caps["TOTAL_DAILY_BUDGET_CAP"]:
        plan = "Caps are not set (empty/zero) — no split can be planned. Owner sets caps in settings first."
    else:
        plan = "Split the daily cap across the customer and reseller test campaigns inside PER_CAMPAIGN_CAP; exact split is a proposal for the approval queue."
    return _out("05_budget_planning", {"caps": caps, "plan": plan})


# ---------- B. Creative Production ----------
ANGLES = {
    "students": [
        "Ek jagah saare study + AI tools, taaki har tool ke liye alag jagah na bhatakna pade",
        "Project aur placement ke kaam ke liye apna AI toolkit ready rakho",
        "Freelance gigs ke liye professional tools apne workflow me add karo",
    ],
    "creators": [
        "Content workflow ke saare tools ek collection me — video, voice, design",
        "Roz ke content ke liye apna creator toolkit ek hi jagah se manage karo",
        "Naye AI tools pehle try karke apne content ko alag banao",
    ],
    "resellers": [
        "Apne bot/catalog ke liye software supply ki jaankari ek jagah",
        "Agencies ke liye team tools ki catalog jaankari",
        "Reseller API aur catalog kaise kaam karta hai — pehle samjho, phir judho",
    ],
}


def role_06_angle_generator(segment="students", profile=None):
    if segment in ANGLES:
        angles = ANGLES[segment]
    elif profile is not None:
        from . import industries
        preset = industries.get_preset(profile.get("industry_preset"))
        angles = preset.get("angle_templates", []) or ANGLES["students"]
    else:
        angles = ANGLES["students"]
    return _out("06_angle_generator", {"segment": segment, "angles": angles,
                                       "count": len(angles)})


def role_07_copywriter(angle, profile=None):
    business = _business_name(profile)
    return _out("07_copywriter", {
        "angle": angle,
        "hinglish": {
            "headline": "Apna AI toolkit ek jagah ready karo",
            "text": angle + " — %s par collections dekho aur apne kaam ke hisaab se chuno." % business,
            "cta": "Learn More",
        },
        "english": {
            "headline": "Build your AI toolkit in one place",
            "text": angle + " — browse the collections on %s and pick what fits your work." % business,
            "cta": "Learn More",
        },
        "note": "Draft copy only (SCRIPT/BRIEF, not a generated asset). Must pass Role 10 policy check and owner approval.",
    })


def role_08_visual_poster_brief(angle, profile=None):
    business = _business_name(profile)
    return _out("08_visual_poster_brief", {
        "type": "BRIEF (text only — no image generated in Step 1)",
        "brief": "Clean poster: one headline line, product collection visual without "
                 "unauthorised brand logos, %s name, no price or claim text "
                 "until verified. Angle: %s" % (business, angle),
        "visual_check_required": ["readable text", "correct product names",
                                  "no misleading claims", "no unauthorised brand marks"],
    })


def role_09_reel_script(angle):
    return _out("09_reel_script", {
        "type": "SCRIPT (text only — no video generated in Step 1)",
        "duration_sec": 30,
        "script": [
            "0-3s hook: " + angle,
            "3-15s: dikhao kaun-kaun se kaam ke tools ek collection me milte hain (screen record, koi claim nahi)",
            "15-25s: apne kaam ke hisaab se collection kaise chunein",
            "25-30s CTA: profile/website par jaakar collections dekho",
        ],
    })


def role_10_policy_checker(product, text, settings=None):
    result = policy_checker.check_creative(product, text, settings=settings)
    return _out("10_policy_checker", result)


# ---------- C. Campaign Management ----------
def role_11_structure_planner(audience="students", angle_code="TOOLKIT", fmt="REEL", version=1):
    stamp = date.today().strftime("%Y%m%d")
    name = "%s_%s_%s_%s_V%d" % (audience[:3].upper(), angle_code, fmt, stamp, version)
    return _out("11_structure_planner", {
        "campaign_name_pattern": "AUD_ANGLE_FORMAT_DATE_VERSION",
        "example_campaign": name,
        "layout": {"campaigns": ["customers", "resellers"],
                   "ad_sets_per_campaign": "small number (owner-approved plan only)",
                   "ads_per_ad_set": "3 to 5, distinct angles"},
    })


def role_12_targeting_planner(segment="students"):
    return _out("12_targeting_planner", {
        "segment": segment,
        "note": "UNTESTED in Step 1. Broad vs interest targeting must follow current "
                "official guidance (PRACTICES.md, Step 2 verification) — nothing is set live.",
        "candidate_interests": ["artificial intelligence", "productivity software", "video editing"],
    })


def role_13_campaign_builder(draft, approved=False, client=None):
    if not approved:
        return _out("13_campaign_builder", {
            "blocked": "Campaign Builder runs only after the owner approves that specific "
                       "draft in the approval queue. Nothing was created."})
    client = client or MockMetaClient()
    camp = client.create_campaign(draft["campaign"], idempotency_key=draft["key"] + ":campaign")
    adset = client.create_adset(camp["id"], draft["adset"], idempotency_key=draft["key"] + ":adset")
    ad = client.create_ad(adset["id"], draft["ad"], draft.get("creative_text", ""),
                          idempotency_key=draft["key"] + ":ad")
    return _out("13_campaign_builder", {
        "created_mock_ids": [camp["id"], adset["id"], ad["id"]],
        "status": "PAUSED (mock) — activation is a separate approval, never automatic",
    })


def role_14_approval_queue_manager(queue):
    return _out("14_approval_queue_manager", {"pending_items": queue.list_pending()})


NO_SPEND_CHECKLIST = [
    "Account spending limit reached (naye accounts par Meta ka daily threshold chhota hota hai)",
    "Learning limited — audience too small / budget too low / duplicate ad sets competing",
    "Payment issues — expired card, insufficient balance, billing verification, unpaid balance",
    "Meta-side technical glitch — uneven/zero spend, usually resolves in a day or two",
    "Too many creatives in one ad set — budget fragments; 3–5 winning creatives per ad set rakho",
    "Policy violation — ad copy/creative ya LANDING PAGE par bhi (Strategy S19, Damini Tripathi / Marketian)",
]


def role_15_account_health_monitor(flags=None):
    flags = flags or []
    if flags:
        return _out("15_account_health_monitor", {
            "flags": flags,
            "action": "STOP automation and inform the owner. Never work around a rejection.",
            "no_spend_checklist": NO_SPEND_CHECKLIST})
    return _out("15_account_health_monitor", {
        "flags": [], "action": "No flags in Step 1 (mock). Live monitoring starts after Step 3.",
        "no_spend_checklist": NO_SPEND_CHECKLIST})


# ---------- D. Performance and Optimisation ----------
def role_16_data_collector(dataset_name="thin_data"):
    rows = mock_insights.get_dataset(dataset_name)
    return _out("16_data_collector", {
        "source": "MOCK insights dataset '%s' — not a live Insights pull" % dataset_name,
        "rows": len(rows),
        "data_quality": {"currency": "unset (setting)", "timezone": "unset (setting)",
                         "freshness": "MOCK data — no freshness guarantee",
                         "attribution_window": "unset (setting)"},
    })


def role_17_lead_quality_tracker(rows):
    counts = {"enquiries": 0, "qualified": 0, "junk": 0, "orders": 0}
    for r in rows:
        counts["enquiries"] += int(r.get("enquiries") or 0)
        counts["qualified"] += int(r.get("qualified_leads") or 0)
        counts["junk"] += int(r.get("junk_leads") or 0)
        counts["orders"] += int(r.get("orders") or 0)
    counts["note"] = "Counts and status only — no personal data is stored (brief rule)."
    return _out("17_lead_quality_tracker", counts)


def role_18_creative_analyst(rows):
    by_angle = {}
    for r in rows:
        a = by_angle.setdefault(r.get("angle", "generic"),
                                {"spend": 0, "enquiries": 0, "qualified": 0})
        a["spend"] += float(r.get("spend") or 0)
        a["enquiries"] += int(r.get("enquiries") or 0)
        a["qualified"] += int(r.get("qualified_leads") or 0)
    for v in by_angle.values():
        v["cost_per_qualified_lead"] = (v["spend"] / v["qualified"]) if v["qualified"] else None
    return _out("18_creative_analyst", {
        "by_angle": by_angle,
        "note": "Angles are compared on cost per qualified lead, never on CPC/CTR alone.",
    })


def role_19_optimiser(rows, settings):
    return _out("19_optimiser", optimiser_mod.analyse(rows, settings))


def role_20_reporter(rows, proposals, language="Hinglish", business_name=None,
                     industry=None):
    total_spend = sum(float(r.get("spend") or 0) for r in rows)
    total_enq = sum(int(r.get("enquiries") or 0) for r in rows)
    total_q = sum(int(r.get("qualified_leads") or 0) for r in rows)
    cpe = (total_spend / total_enq) if total_enq else None
    cpq = (total_spend / total_q) if total_q else None
    if language == "Hinglish":
        summary = ("MOCK daily report: kul kharch %s, enquiries %d, qualified leads %d. "
                   "Cost per enquiry (provisional) %s; cost per qualified lead %s. "
                   "Approval ke liye %d proposals pending hain."
                   % (total_spend, total_enq, total_q,
                      ("n/a" if cpe is None else round(cpe, 2)),
                      ("n/a" if cpq is None else round(cpq, 2)), len(proposals)))
    else:
        summary = ("MOCK daily report: total spend %s, enquiries %d, qualified leads %d. "
                   "Cost per enquiry (provisional) %s; cost per qualified lead %s. "
                   "%d proposals waiting for approval."
                   % (total_spend, total_enq, total_q,
                      ("n/a" if cpe is None else round(cpe, 2)),
                      ("n/a" if cpq is None else round(cpq, 2)), len(proposals)))
    if business_name:
        header = "Business: %s%s" % (
            business_name, (" · Industry: %s" % industry) if industry else "")
        summary = header + "\n" + summary
    return _out("20_reporter", {"language": language, "summary": summary,
                                "business": business_name, "industry": industry})


ALL_ROLES = [
    role_01_audience_research, role_02_competitor_watch, role_03_trend_analysis,
    role_04_funnel_strategy, role_05_budget_planning, role_06_angle_generator,
    role_07_copywriter, role_08_visual_poster_brief, role_09_reel_script,
    role_10_policy_checker, role_11_structure_planner, role_12_targeting_planner,
    role_13_campaign_builder, role_14_approval_queue_manager,
    role_15_account_health_monitor, role_16_data_collector,
    role_17_lead_quality_tracker, role_18_creative_analyst, role_19_optimiser,
    role_20_reporter,
]
