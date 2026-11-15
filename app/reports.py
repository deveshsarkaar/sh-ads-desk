"""Reporter — Role 20 (full build): daily + weekly reports.

Plain language, Hinglish option (settings LANGUAGES[0] by default).
Data-quality notes are always included: currency/timezone settings,
freshness, and whether the numbers are MOCK. Cost per qualified lead is the
main metric; cost per enquiry is always labelled provisional.
"""
from . import roles


def _rank(rows):
    def cpq(r):
        q = int(r.get("qualified_leads") or 0)
        return (float(r.get("spend") or 0) / q) if q else float("inf")
    ordered = sorted(rows, key=cpq)
    return ordered[:3], list(reversed(ordered[-3:])) if len(ordered) > 3 else list(reversed(ordered))


def daily_report(rows, proposals_pending, settings, language="Hinglish", source="MOCK"):
    base = roles.role_20_reporter(rows, proposals_pending, language)["output"]["summary"]
    top, bottom = _rank(rows)
    quality = (
        "Data quality: source=%s; currency=%s; timezone=%s; attribution window=%s. "
        "Meta reporting lags — spend figures can still move; treat cost per "
        "qualified lead as final only after the conversion lag window (%s days)."
        % (source, settings.get("ACCOUNT_CURRENCY") or "unset (setting)",
           settings.get("ACCOUNT_TIMEZONE") or "unset (setting)",
           settings.get("ATTRIBUTION_WINDOW") or "unset (setting)",
           settings.get("CONVERSION_LAG_WINDOW_DAYS") or 0))
    fmt = lambda r: "%s (spend %s, qualified %s)" % (
        r.get("ad_id"), r.get("spend"), r.get("qualified_leads"))
    lines = [base, quality,
             "Top 3: " + ("; ".join(fmt(r) for r in top) or "none"),
             "Bottom 3: " + ("; ".join(fmt(r) for r in bottom) or "none"),
             "Proposals waiting for approval: %d" % len(proposals_pending)]
    return "\n".join(lines)


def weekly_report(rows, proposals_pending, settings, language="Hinglish", source="MOCK"):
    analyst = roles.role_18_creative_analyst(rows)["output"]["by_angle"]
    winner = None
    for angle, v in analyst.items():
        if v["cost_per_qualified_lead"] is not None:
            if winner is None or v["cost_per_qualified_lead"] < analyst[winner]["cost_per_qualified_lead"]:
                winner = angle
    lines = [
        daily_report(rows, proposals_pending, settings, language, source),
        "Weekly: winning angle (by cost per qualified lead, never CPC/CTR alone): %s"
        % (winner or "not enough data"),
        "Test next: one new angle against the winner, one variable changed, "
        "mutually exclusive audience where possible (brief test-design rule).",
        "Budget recommendation: none automatic — any change is a proposal in "
        "the approval queue inside your caps and MAX_BUDGET_CHANGE_PCT.",
        "Trend watch: see the Trends page — items are UNVERIFIED until re-checked "
        "on the official source; strategy never changes automatically.",
    ]
    return "\n".join(lines)
