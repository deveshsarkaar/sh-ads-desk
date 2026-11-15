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
        "date": "cited in owner brief, 2026-11-15",
        "verified": False,
        "note": "UNVERIFIED in this build. Supports the brief's test-design rule: "
                "one variable at a time, mutually exclusive audiences.",
    },
    {
        "title": "Ads Insights API metric availability updates (attribution windows, Jan 2026)",
        "url": "https://developers.facebook.com/blog/post/2025/10/16/ads-insights-api-metric-availability-updates/",
        "date": "2025-10-16 (post date in URL)",
        "verified": False,
        "note": "UNVERIFIED — this page returned 403 in an earlier check. Do not "
                "rely on any attribution-window claim until it loads for you.",
    },
    {
        "title": "Marketing API version pin used by this system",
        "url": "https://developers.facebook.com/docs/marketing-api/changelog",
        "date": "checked via secondary sources, 2026-11-15",
        "verified": False,
        "note": "UNVERIFIED — secondary sources indicated v26.0/v27.0 current and "
                "v25.0 available until 2027-02-23. meta_client pins v25.0; confirm "
                "on the official changelog before live use.",
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
        "date": "cited in owner brief, 2026-11-15",
        "verified": False,
        "note": "UNVERIFIED in this build. Step 2 walks through this page with the owner.",
    },
]
