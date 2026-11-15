"""MOCK insights data — SH Ads Desk Step 1. *** ALL DATA HERE IS MOCK ***
Fake ad-performance rows covering the brief's edge cases. No real account,
no real spend. Amounts are plain numbers in an unnamed currency (the account
currency is a setting and is empty in Step 1).

Row fields: spend, impressions, clicks, enquiries, qualified_leads,
junk_leads, orders, frequency/ctr at start and end of the window,
days_since_launch, days_since_last_change, budget_owner ('campaign' or
'adset' — never 'ad'), budget_object_id, current_budget.
"""


def _ad(ad_id, **kw):
    row = {
        "ad_id": ad_id, "campaign_id": "mock_campaign_x", "angle": "generic",
        "format": "reel", "budget_owner": "adset",
        "budget_object_id": "mock_adset_" + ad_id, "current_budget": 1000,
        "spend": 0, "impressions": 0, "clicks": 0, "enquiries": 0,
        "qualified_leads": 0, "junk_leads": 0, "orders": 0,
        "frequency_start": 1.0, "frequency_end": 1.2,
        "ctr_start": 2.0, "ctr_end": 1.9,
        "days_since_launch": 14, "days_since_last_change": 10,
        "conversions_lagged_pending": False,
    }
    row.update(kw)
    return row


DATASETS = {
    # Edge case: almost no spend/events — optimiser must say "not enough data".
    "thin_data": [
        _ad("thin_1", spend=60, impressions=400, clicks=5, enquiries=1,
            qualified_leads=0, junk_leads=0),
        _ad("thin_2", spend=45, impressions=300, clicks=3, enquiries=0,
            qualified_leads=0, junk_leads=0),
    ],
    # Edge case: one clear winner (cost per qualified lead far below target,
    # enquiry rate significantly better than the others) + two weak ads.
    "one_big_winner": [
        _ad("win_1", angle="workflow", spend=5000, impressions=60000, clicks=2400,
            enquiries=200, qualified_leads=80, junk_leads=20, orders=12,
            budget_object_id="mock_adset_win", current_budget=1000),
        _ad("mid_1", angle="catalog", spend=4000, impressions=55000, clicks=1100,
            enquiries=40, qualified_leads=4, junk_leads=20, orders=0,
            budget_object_id="mock_adset_mid", current_budget=1000),
        _ad("mid_2", angle="price", spend=4000, impressions=50000, clicks=1000,
            enquiries=36, qualified_leads=3, junk_leads=18, orders=0,
            budget_object_id="mock_adset_mid2", current_budget=1000),
    ],
    # Edge case: every ad is a loser on cost per qualified lead.
    "all_losers": [
        _ad("lose_1", spend=6000, impressions=70000, clicks=1400, enquiries=60,
            qualified_leads=3, junk_leads=40, budget_object_id="mock_adset_l1"),
        _ad("lose_2", spend=5500, impressions=65000, clicks=1200, enquiries=55,
            qualified_leads=2, junk_leads=38, budget_object_id="mock_adset_l2"),
        _ad("lose_3", spend=5000, impressions=60000, clicks=1100, enquiries=50,
            qualified_leads=2, junk_leads=35, budget_object_id="mock_adset_l3"),
    ],
    # Edge case: cheap enquiries that are almost all junk — still a loser.
    "cheap_junk_leads": [
        _ad("junk_1", spend=3000, impressions=90000, clicks=3000, enquiries=300,
            qualified_leads=0, junk_leads=285, budget_object_id="mock_adset_j1"),
        _ad("ok_1", spend=3000, impressions=40000, clicks=1200, enquiries=60,
            qualified_leads=15, junk_leads=10, budget_object_id="mock_adset_ok1"),
    ],
    # Edge case: conversions still inside the lag window — must not be judged.
    "lagged_conversions": [
        _ad("lag_1", spend=4000, impressions=50000, clicks=1500, enquiries=90,
            qualified_leads=1, junk_leads=5, days_since_launch=2,
            conversions_lagged_pending=True, budget_object_id="mock_adset_lag1"),
        _ad("lag_2", spend=4200, impressions=52000, clicks=1400, enquiries=85,
            qualified_leads=0, junk_leads=4, days_since_launch=3,
            conversions_lagged_pending=True, budget_object_id="mock_adset_lag2"),
    ],
    # Edge case: combined reported spend breaches the daily cap.
    "spend_breach": [
        _ad("br_1", spend=9000, impressions=80000, clicks=2000, enquiries=100,
            qualified_leads=20, budget_object_id="mock_adset_b1"),
        _ad("br_2", spend=8000, impressions=75000, clicks=1800, enquiries=90,
            qualified_leads=18, budget_object_id="mock_adset_b2"),
    ],
    # Edge case: creative fatigue — frequency up, CTR down, enough data.
    "fatigue": [
        _ad("fat_1", spend=4500, impressions=80000, clicks=900, enquiries=70,
            qualified_leads=14, junk_leads=8, frequency_start=1.1,
            frequency_end=4.8, ctr_start=3.0, ctr_end=0.9,
            budget_object_id="mock_adset_f1"),
    ],
}


def get_dataset(name):
    """Return a fresh copy of a MOCK dataset (labelled MOCK)."""
    rows = DATASETS[name]
    return [dict(r) for r in rows]
