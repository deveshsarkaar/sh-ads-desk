"""Campaign Structure Planner — Role 11 (full build).

Builds a launch-ready PLAN (data only — nothing is written to Meta here).
Separate campaigns for customers and resellers, a small number of ad sets,
3-5 ads with distinct angles per ad set (brief process rule). Names follow
AUD_ANGLE_FORMAT_DATE_VERSION. Budgets are attached at campaign level in
the plan — never per ad.
"""
from datetime import date

from . import roles

ANGLE_CODES = {"students": "TOOLKIT", "freelancers": "WORKFLOW",
               "creators": "CONTENT", "bot owners": "CATALOG",
               "agencies": "TEAMS"}


def plan_structure(product, segment="students", audience_type="customers",
                   fmt="REEL", version=1, daily_budget="", profile=None):
    stamp = date.today().strftime("%Y%m%d")
    code = ANGLE_CODES.get(segment, "GENERAL")
    aud = segment[:3].upper()
    campaign_name = "%s_%s_%s_%s_V%d" % (aud, code, fmt, stamp, version)
    angles = roles.role_06_angle_generator(segment, profile=profile)["output"]["angles"]
    ads = []
    for i, angle in enumerate(angles[:5], start=1):
        ads.append({
            "ad_name": "%s_AD%d" % (campaign_name, i),
            "angle": angle,
            "format": fmt,
            "note": "Distinct angle — one variable changed per test (brief test-design rule).",
        })
    return {
        "product": product,
        "business": (profile or {}).get("name"),
        "industry": (profile or {}).get("industry"),
        "audience_type": audience_type,  # 'customers' or 'resellers' — never mixed
        "campaign_name": campaign_name,
        "campaign": {
            "name": campaign_name,
            "objective": "OUTCOME_LEADS (UNTESTED default — owner confirms objective in Step 2)",
            "budget_owner": "campaign",
            "daily_budget": daily_budget or "",
            "status_on_create": "PAUSED — creation needs a separate owner approval; "
                                "activation is another separate approval",
        },
        "ad_sets": [{
            "name": campaign_name + "_AS1",
            "budget_owner": "adset (alternative — the plan uses campaign budget; "
                            "the optimiser detects the real owner before proposing)",
            "ads": ads,
        }],
        "naming_pattern": "AUD_ANGLE_FORMAT_DATE_VERSION",
        "label": "PLAN ONLY — nothing is written to Meta by the planner",
    }
