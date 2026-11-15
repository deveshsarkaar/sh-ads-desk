"""Trend watch — official sources only (brief rule 8).

Every item carries a URL and a date. Items that were NOT fetched live while
building this package are marked verified=False / UNVERIFIED and must be
re-checked by the owner (or in Step 2) before anyone acts on them. A trend
never changes strategy automatically — it only creates a note for the owner.
"""

TREND_ITEMS = [
    {
        "title": "Meta restricts ads promoting devices/subscriptions used in an unauthorised manner",
        "url": "https://transparency.meta.com/policies/ad-standards/restricted-goods-services/prohibited-documents-and-financial-services/",
        "date": "cited in owner brief, 2026-11-15",
        "verified": False,
        "note": "UNVERIFIED in this build (page not fetched live). This is the "
                "policy the eligibility + banned-claims gates are built around.",
    },
    {
        "title": "Marketing API split testing on mutually exclusive audiences",
        "url": "https://developers.facebook.com/docs/marketing-api/guides/split-testing/",
        "date": "Step 2 check, 2026-11-16",
        "verified": False,
        "note": "Guide page itself still UNVERIFIED here (403 to this "
                "environment). The principle is CORROBORATED in Step 2 from "
                "Meta Business Help Center A/B-test guidance, quoted verbatim "
                "by multiple readers: each version is shown to a segment of "
                "the audience and nobody sees both. API study-object "
                "specifics stay unverified — see PRACTICES.md.",
    },
    {
        "title": "Ads Insights API metric availability updates (attribution windows, Jan 2026)",
        "url": "https://developers.facebook.com/blog/post/2025/10/16/ads-insights-api-metric-availability-updates/",
        "date": "2025-10-16 (post date in URL); Step 2 re-check 2026-11-16",
        "verified": False,
        "note": "Post itself still UNVERIFIED — 403 on every load attempt, "
                "including the Step 2 retry (2026-11-16). Its headline change "
                "is widely corroborated: from 2026-01-12 the Ads Insights API "
                "stopped returning 7-day view and 28-day view attribution "
                "windows. Do not rely on finer details (retention limits etc.) "
                "until the post itself loads — see PRACTICES.md.",
    },
    {
        "title": "Marketing API version pin used by this system",
        "url": "https://developers.facebook.com/docs/marketing-api/changelog",
        "date": "Step 2 check, 2026-11-16",
        "verified": False,
        "note": "Step 2 (2026-11-16): pin updated v25.0 -> v27.0. v27.0 is "
                "the current version (released 2026-11-04 per Meta's official "
                "changelog; v25.0 available only until 2027-02-23). The "
                "changelog page itself returns 403 to this environment, so "
                "dates are corroborated — Meta's official Authorization doc "
                "(loaded in Step 2) itself uses v27.0 in its OAuth example. "
                "See PRACTICES.md.",
    },
    {
        "title": "Meta Advertising Standards (full text)",
        "url": "https://transparency.meta.com/policies/ad-standards/",
        "date": "cited in owner brief, 2026-11-15",
        "verified": False,
        "note": "UNVERIFIED in this build. Owner should read before Step 4.",
    },
    {
        "title": "Marketing API authorisation / access tiers for your own account",
        "url": "https://developers.facebook.com/documentation/ads-commerce/marketing-api/get-started/authorization",
        "date": "read 2026-11-16 (Step 2)",
        "verified": True,
        "note": "VERIFIED in Step 2 (2026-11-16): page loaded and read. For "
                "your OWN ad account, standard access to ads_read / "
                "ads_management is sufficient; advanced access + App Review "
                "are only for managing other people's accounts. Tiers renamed "
                "(May 2026): Limited (default) / Full (500+ calls in 15 days, "
                "error rate <15%). Full details in META_ACCESS.md.",
    },
]

# ---------------------------------------------------------------------------
# Meta Knowledge register — 2026 features/changes (deliverable: extend the
# trend watch into a register). Every entry: official source URL + date
# read + VERIFIED/UNVERIFIED status. The weekly job reviews this register;
# strategy changes from it remain PROPOSALS ONLY, never silent changes.
#
# Entries O1–O10 come from the practitioner knowledge base research
# (~/workspace/research_notes/meta-ads-knowledge-20261116/report.md,
# read 2026-11-16). IMPORTANT: facebook.com/business returns 403 to this
# environment, so five official entries were verified there through
# multiple independent secondary sources quoting Meta verbatim. Those
# keep verified=False here — UNVERIFIED until re-checked on the live
# Meta page. They must NOT be upgraded without that re-check.
# ---------------------------------------------------------------------------
KNOWLEDGE_REGISTER = [
    {
        "id": "O1", "area": "Delivery system (Andromeda)",
        "title": "Andromeda rebuilt — next-generation ads retrieval (Oct 2026)",
        "url": "https://engineering.fb.com/2026/10/28/ml-applications/meta-andromeda-next-gen-ads-retrieval-gpu-co-design/",
        "date_read": "2026-11-16", "verified": True,
        "note": "VERIFIED: Engineering at Meta post (28 Oct 2026) read "
                "directly in the research pass. Rebuilt retrieval scores "
                "every eligible ad at near ranking-level quality; there "
                "is NO advertiser toggle — retrieval is creative-led, "
                "so distinct creatives are the input that matters.",
    },
    {
        "id": "O2", "area": "Delivery system (Andromeda)",
        "title": "Andromeda original launch — the foundation (Dec 2024)",
        "url": "https://engineering.fb.com/2024/12/02/production-engineering/meta-andromeda-advantage-automation-next-gen-personalized-ads-retrieval-engine/",
        "date_read": "2026-11-16", "verified": True,
        "note": "VERIFIED: Engineering at Meta post (2 Dec 2024) read "
                "directly. Background for why creative volume + "
                "diversity now outweigh micro-targeting.",
    },
    {
        "id": "O3", "area": "Creative",
        "title": "Creative diversification — Meta's official definition (Dec 2025, governs 2026)",
        "url": "https://www.facebook.com/business/news/demystifying-creative-diversification",
        "date_read": "2026-11-16", "verified": False,
        "note": "UNVERIFIED until re-checked on the live Meta page: the "
                "facebook.com/business page 403s in this environment; "
                "content was verified in research through multiple "
                "independent sources quoting the post verbatim. "
                "Substance: ads sharing visual/thematic attributes are "
                "grouped as the SAME creative (iteration is not "
                "diversification); Meta publishes NO numeric similarity "
                "threshold and NO required creative count.",
    },
    {
        "id": "O4", "area": "Creative",
        "title": "'The Creative Advantage' — targeting to creative diversification shift (Apr 2025)",
        "url": "https://www.facebook.com/business/news/the-creative-advantage-unlocking-the-power-of-diversification-with-meta-andromeda",
        "date_read": "2026-11-16", "verified": False,
        "note": "UNVERIFIED until re-checked live (403 in this "
                "environment; verified via verbatim citations in "
                "secondary sources). Meta's stated focus shifted from "
                "niche targeting to creative diversification.",
    },
    {
        "id": "O5", "area": "Campaign setup / API",
        "title": "Streamlined Advantage+ setup — Advantage+ on by default (Feb 2025, API enforcement through 2026)",
        "url": "https://developers.facebook.com/docs/marketing-api",
        "date_read": "2026-11-16", "verified": False,
        "note": "UNVERIFIED until re-checked live (Meta pages not "
                "directly loadable here; announcement + developer docs "
                "corroborated via secondary reporting). One streamlined "
                "setup for Sales/App/Leads; Marketing API v25.0 blocks "
                "creating new legacy Advantage+ shopping campaigns, "
                "v26.0 blocks editing them — never design API flows "
                "around legacy shopping endpoints.",
    },
    {
        "id": "O6", "area": "Delivery system (GEM)",
        "title": "GEM — Generative Ads Recommendation Model (Nov 2025; 2nd generation Oct 2026)",
        "url": "https://engineering.fb.com/2025/11/10/ml-applications/metas-generative-ads-model-gem-the-central-brain-accelerating-ads-recommendation-ai-innovation/",
        "date_read": "2026-11-16", "verified": False,
        "note": "UNVERIFIED until re-checked live: the Oct 2026 "
                "second-generation figures come via secondary reporting "
                "(PPC Land) and are Meta's own claims with no published "
                "baseline/method — directional only. GEM has no "
                "advertiser toggle and is not a creative tool.",
    },
    {
        "id": "O7", "area": "Measurement",
        "title": "Incremental attribution — global rollout completed (June 2025)",
        "url": "https://www.facebook.com/business/help",
        "date_read": "2026-11-16", "verified": False,
        "note": "UNVERIFIED until re-checked live (corroborated via "
                "secondary reporting of Meta's announcement + Help "
                "Center). Attribution MODEL that optimises for "
                "conversions the ML predicts the ad caused; compare "
                "models before switching anything.",
    },
    {
        "id": "O8", "area": "Optimisation",
        "title": "Opportunity Score — global rollout (June 2025)",
        "url": "https://www.facebook.com/business/help",
        "date_read": "2026-11-16", "verified": False,
        "note": "UNVERIFIED until re-checked live (rollout via "
                "secondary reporting). OFFICIAL: the feature exists "
                "(0–100 grade of recommendation adoption). "
                "PRACTITIONER criticism (kept separate): the score "
                "rewards switching on Meta automations — use it as a "
                "checklist prompt only, never as a performance result.",
    },
    {
        "id": "O9", "area": "Measurement",
        "title": "Attribution reporting changes 2026 — view windows removed; click redefined",
        "url": "https://developers.facebook.com/blog/post/2025/10/16/ads-insights-api-metric-availability-updates/",
        "date_read": "2026-11-16", "verified": False,
        "note": "UNVERIFIED until re-checked live (Meta's own post "
                "403s here; reported by multiple trade sources). From "
                "2026-01-12 the 7-day view and 28-day view windows were "
                "removed from Insights/API; from March 2026 "
                "click-through counts LINK CLICKS only, with a new "
                "1-day engage-through window. Annotate reports with "
                "these dates; compare like-for-like windows only.",
    },
    {
        "id": "O10", "area": "Policy / targeting",
        "title": "Detailed-targeting removals completing Jan 2026 + updated Ad Terms (2026)",
        "url": "https://transparency.meta.com/policies/ad-standards/",
        "date_read": "2026-11-16", "verified": False,
        "note": "UNVERIFIED until re-checked live: terms substance "
                "announced (advertiser is responsible for ALL ad "
                "content incl. AI-generated; never remove AI "
                "watermarks/authenticity data) but secondary reports "
                "CONFLICT on the effective date (30 Oct vs 20 Nov "
                "2026) — date unconfirmed. Targeting: delivery stopped "
                "after 2026-01-15 for ad sets using removed interests.",
    },
    {
        "id": "S2-1", "area": "Access / API",
        "title": "Own-account standard access is sufficient; tiers renamed Limited/Full (May 2026)",
        "url": "https://developers.facebook.com/documentation/ads-commerce/marketing-api/get-started/authorization",
        "date_read": "2026-11-16", "verified": True,
        "note": "VERIFIED in Step 2 (official Authorization page loaded "
                "and read): standard access to ads_read/ads_management "
                "suffices for your OWN account; Full tier = App Review "
                "+ 500 calls/15 days + error rate <15%. Details in "
                "META_ACCESS.md.",
    },
    {
        "id": "S2-2", "area": "API version",
        "title": "Marketing API v27.0 current (released 2026-11-04); v25.0 available until 2027-02-23",
        "url": "https://developers.facebook.com/docs/marketing-api/changelog",
        "date_read": "2026-11-16", "verified": False,
        "note": "UNVERIFIED on the changelog page itself (403 here); "
                "corroborated in Step 2 — Meta's official Authorization "
                "doc itself uses v27.0 in its OAuth example. This "
                "system pins v27.0 (app/meta_client.py). Caution: "
                "v27.0 enables new defaults on some newly created "
                "objects — Step 4 drafts must set those fields "
                "explicitly.",
    },
]


def knowledge_review():
    """Weekly-review helper: register summary for reports. Strategy
    changes from the register are proposals only — this function only
    reports; it never changes anything."""
    verified = [i for i in KNOWLEDGE_REGISTER if i["verified"]]
    unverified = [i for i in KNOWLEDGE_REGISTER if not i["verified"]]
    return {
        "total": len(KNOWLEDGE_REGISTER),
        "verified": len(verified),
        "unverified": len(unverified),
        "unverified_ids": [i["id"] for i in unverified],
        "note": "Meta Knowledge register reviewed: %d entries (%d "
                "VERIFIED, %d UNVERIFIED — UNVERIFIED items must be "
                "re-checked on the official source before anyone acts "
                "on them). Koi strategy change apne aap nahi hua — "
                "badlav hamesha proposal + owner approval se hoga."
                % (len(KNOWLEDGE_REGISTER), len(verified), len(unverified)),
    }
