"""SH Ads Desk web app — full build (stdlib only, no framework).

Professional, mobile-friendly, single-owner UI. Pages (brief Part 3):
Today, Connect wizard, Roles (20), Settings, Eligibility & destination
gate, Creative studio, Planner, Approval queue, Budget, Leads, Reports,
Trends, Errors & audit — plus Login / first-run Setup / Logout.

Safety wiring:
- Every page sits behind the owner login (except /login and /setup).
- Every POST needs the session CSRF token.
- Every action states what it will do BEFORE it does it (page copy).
- DRY_RUN + PROPOSE are the defaults; the live Meta path is UNTESTED and
  banner-labelled; the kill switch blocks approvals/execution.
"""
import html
import json
import os
import urllib.parse
from http import cookies as http_cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import auth, creative as creative_mod, optimiser as optimiser_mod
from . import guardrails as guardrails_mod
from . import growth_loop as loop_mod
from . import industries as industries_mod
from . import planner as planner_mod, policy_checker, providers
from . import profiles as profiles_mod
from . import reports as reports_mod
from . import roles, store, strategy_library, trends as trends_mod
from .approval_queue import ApprovalQueue
from .common import (audit, get_db, load_eligibility, load_settings,
                     log_error, redact, save_eligibility, save_settings)
from .execute import execute_approved_item
from .meta_client import API_VERSION_LABEL

CSS = """
/* Clean, minimal shell (owner UI directive 2026-11-16): whitespace first,
   one clear action per screen, detail behind <details> — no text walls. */
:root{--ink:#1f2430;--mut:#6b7280;--line:#e8e8f0;--bg:#f7f7fb;--card:#fff;
--brand:#7c3aed;--brand2:#6d28d9;--violetbg:#ede9fe;--ok:#0d7a4a;--bad:#b3261e;--warn:#9a6a00;
--warnbg:#fff8e1;--okbg:#e7f6ee;--badbg:#fdecea;--radius:14px}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;
background:var(--bg);color:var(--ink);font-size:15px;line-height:1.6}
a{color:var(--brand);text-decoration:none}a:hover{text-decoration:underline}
.layout{display:flex;min-height:100vh;align-items:stretch}
aside.sidebar{width:252px;flex:none;background:#fff;border-right:1px solid var(--line);
position:sticky;top:0;height:100vh;display:flex;flex-direction:column;
padding:18px 14px;overflow-y:auto}
.sb-brand{font-weight:800;font-size:19px;padding:2px 8px 14px;letter-spacing:-.2px}
.sb-ws{background:var(--bg);border:1px solid var(--line);border-radius:12px;
padding:10px 12px;margin-bottom:14px}
.sb-ws .t{font-weight:700;font-size:13.5px}.sb-ws .s{color:var(--mut);font-size:12px}
nav.side{display:flex;flex-direction:column;gap:2px}
nav.side a{padding:8px 12px;border-radius:10px;color:var(--mut);font-size:14px;font-weight:500}
nav.side a:hover{background:#f5f2ff;text-decoration:none;color:var(--ink)}
nav.side a.on{background:var(--violetbg);color:var(--brand2);font-weight:700}
.sb-spacer{flex:1}
.sb-profile{border-top:1px solid var(--line);padding-top:12px;margin-top:12px}
.sb-user{display:flex;gap:10px;align-items:center;padding:2px 6px 10px}
.sb-avatar{width:34px;height:34px;border-radius:50%;background:var(--brand);color:#fff;
display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex:none}
.shell{flex:1;min-width:0;display:flex;flex-direction:column}
.topbar{background:#fff;border-bottom:1px solid var(--line);padding:12px 22px;
display:flex;gap:10px;align-items:center;flex-wrap:wrap;position:sticky;top:0;z-index:5}
.topbar .ctx{font-weight:700;font-size:16px}
.tag{font-size:11.5px;background:#f1f0fb;color:var(--mut);border-radius:20px;padding:3px 11px}
main{width:100%;max-width:1180px;margin:0 auto;padding:26px 22px 60px}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
padding:22px 24px;margin:0 0 18px;box-shadow:0 1px 3px rgba(31,27,80,.05)}
h1{font-size:26px;margin:2px 0 8px;letter-spacing:-.3px;font-weight:800}
h2{font-size:17px;margin:2px 0 12px;font-weight:700}
h3{font-size:15px;margin:16px 0 6px}.mut{color:var(--mut)}.small{font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
.ihead{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap}
.ihead h1{margin-bottom:2px}
.igrid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:0 0 18px}
@media(max-width:1000px){.igrid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:640px){.igrid{grid-template-columns:1fr}}
.icard{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
padding:18px;box-shadow:0 1px 3px rgba(31,27,80,.05);display:flex;flex-direction:column}
.icard .ihead2{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:6px}
.icard .ititle{display:flex;gap:10px;align-items:center;font-weight:700;font-size:16px}
.iicon{width:36px;height:36px;border-radius:10px;background:var(--violetbg);color:var(--brand2);
display:flex;align-items:center;justify-content:center;font-size:19px;flex:none}
.ichips{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 14px}
.ichip{background:#f1f0fb;color:var(--mut);border-radius:20px;padding:2px 10px;font-size:12px;font-weight:600}
.ibtn{display:block;text-align:center}
.keyrow{display:flex;gap:8px;align-items:stretch}
.keyrow input{flex:1;margin:0;min-width:0}
.keyrow button{white-space:nowrap}
.kpi{font-size:28px;font-weight:800;letter-spacing:-.5px}
.pill{display:inline-block;border-radius:20px;padding:2px 11px;font-size:12px;font-weight:600;white-space:nowrap}
.pill.ok{background:var(--okbg);color:var(--ok)}.pill.bad{background:var(--badbg);color:var(--bad)}
.pill.warn{background:var(--warnbg);color:var(--warn)}.pill.info{background:var(--violetbg);color:var(--brand2)}
.pill.dim{background:#f1f0fb;color:var(--mut)}
.banner{border-radius:var(--radius);padding:13px 17px;margin:0 0 18px;font-size:14px}
.banner.warn{background:var(--warnbg);border:1px solid #ecd28a}
.banner.bad{background:var(--badbg);border:1px solid #f0b6b1}
.banner.ok{background:var(--okbg);border:1px solid #a9dcc2}
.twrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}
th,td{border-bottom:1px solid var(--line);padding:9px 8px;text-align:left;vertical-align:top}
tr:last-child td{border-bottom:0}
th{color:var(--mut);font-weight:600;font-size:12.5px;text-transform:uppercase;letter-spacing:.4px}
input,select,textarea{width:100%;padding:10px 12px;border:1px solid var(--line);
border-radius:10px;font:inherit;background:#fff;margin:4px 0 12px}
input:focus,select:focus,textarea:focus{outline:2px solid #ddd0fb;border-color:var(--brand)}
label{font-weight:600;font-size:13.5px}
button,.btn{display:inline-block;background:var(--brand);color:#fff;border:0;border-radius:10px;
padding:10px 18px;font:inherit;font-weight:600;cursor:pointer}
button:hover,.btn:hover{background:var(--brand2);text-decoration:none}
button.secondary,.btn.secondary{background:#f1f0fb;color:var(--ink)}
button.danger{background:var(--bad)}button:disabled{opacity:.5;cursor:not-allowed}
.inline{display:inline}.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.row>div{flex:1;min-width:150px}
pre{background:#0f1a2c;color:#d7e3f5;border-radius:12px;padding:13px;overflow:auto;
font-size:12.5px;white-space:pre-wrap;word-break:break-word;max-height:260px}
.flash{border-radius:12px;padding:11px 15px;margin:0 0 16px;background:#f3efff;border:1px solid #ddd0fb}
.check li{margin:3px 0}.footer{color:var(--mut);font-size:12.5px;text-align:center;padding:20px}
details{border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin:0 0 14px;background:#fcfdff}
details summary{cursor:pointer;font-weight:600;font-size:14px;color:var(--mut)}
details[open ] summary{margin-bottom:8px;color:var(--ink)}
.stages{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 2px}
.stage{display:flex;align-items:center;gap:7px;background:#f2f5fa;border-radius:20px;
padding:6px 13px;font-size:13px;font-weight:500}
.stage .dot{width:8px;height:8px;border-radius:50%;background:#c3cedd}
.stage.done .dot{background:var(--ok)}.stage.now{background:var(--violetbg);color:var(--brand2)}
.stage.now .dot{background:var(--brand)}
.bigbtn{font-size:16px;padding:13px 26px;border-radius:12px}
@media(max-width:860px){.layout{flex-direction:column}
aside.sidebar{width:100%;height:auto;position:static}
nav.side{flex-direction:row;overflow-x:auto;padding-bottom:6px}
nav.side a{white-space:nowrap}.sb-spacer{display:none}
.sb-profile{border-top:0;margin-top:4px}}
@media(max-width:640px){main{padding:18px 12px 56px}h1{font-size:22px}
.topbar .tag{display:none}table{font-size:13px}.card{padding:17px 16px}}
"""

NAV = [
    ("/", "Today"), ("/mission", "Mission Control"), ("/campaigns", "Campaigns"), ("/profiles", "Profiles"), ("/loop", "Growth Loop"),
    ("/connect", "Connect"), ("/roles", "Roles"),
    ("/settings", "Settings"), ("/guardrails", "Guardrails"),
    ("/eligibility", "Eligibility"),
    ("/creative", "Creative Studio"), ("/providers", "API Providers"),
    ("/planner", "Planner"),
    ("/approvals", "Approvals"), ("/budget", "Budget"), ("/leads", "Leads"),
    ("/reports", "Reports"), ("/trends", "Knowledge"), ("/audit", "Errors & Audit"),
]

ROLE_NAMES = [
    ("01_audience_research", "1 · Audience Research", "A. Research & Strategy"),
    ("02_competitor_watch", "2 · Competitor Watch", "A. Research & Strategy"),
    ("03_trend_analysis", "3 · Trend Analysis", "A. Research & Strategy"),
    ("04_funnel_strategy", "4 · Funnel Strategy", "A. Research & Strategy"),
    ("05_budget_planning", "5 · Budget Planning", "A. Research & Strategy"),
    ("06_angle_generator", "6 · Angle Generator", "B. Creative Production"),
    ("07_copywriter", "7 · Copywriter", "B. Creative Production"),
    ("08_visual_poster_brief", "8 · Visual / Poster Brief", "B. Creative Production"),
    ("09_reel_script", "9 · Reel / Video Script", "B. Creative Production"),
    ("10_policy_checker", "10 · Policy Checker", "B. Creative Production"),
    ("11_structure_planner", "11 · Structure Planner", "C. Campaign Management"),
    ("12_targeting_planner", "12 · Audience / Targeting Planner", "C. Campaign Management"),
    ("13_campaign_builder", "13 · Campaign Builder", "C. Campaign Management"),
    ("14_approval_queue_manager", "14 · Approval Queue Manager", "C. Campaign Management"),
    ("15_account_health_monitor", "15 · Compliance & Account Health", "C. Campaign Management"),
    ("16_data_collector", "16 · Data Collector", "D. Performance & Optimisation"),
    ("17_lead_quality_tracker", "17 · Lead Quality Tracker", "D. Performance & Optimisation"),
    ("18_creative_analyst", "18 · Creative Analyst", "D. Performance & Optimisation"),
    ("19_optimiser", "19 · Optimiser", "D. Performance & Optimisation"),
    ("20_reporter", "20 · Reporter", "D. Performance & Optimisation"),
]

# Agents page metadata: icon glyph + a one-line description of what the
# role function in app/roles.py actually does (no invented capabilities).
ROLE_DESCRIPTIONS = {
    "01_audience_research": ("&#128101;", "Segments customers and resellers — pain points and interests"),
    "02_competitor_watch": ("&#128269;", "Tracks competitor ads, offers and positioning"),
    "03_trend_analysis": ("&#128200;", "Surfaces market and platform trends to act on"),
    "04_funnel_strategy": ("&#127919;", "Plans the funnel stages for the active business profile"),
    "05_budget_planning": ("&#8377;", "Plans budgets inside the owner's caps"),
    "06_angle_generator": ("&#128161;", "Generates fresh ad angles for each segment"),
    "07_copywriter": ("&#9999;", "Writes ad copy from the chosen angle"),
    "08_visual_poster_brief": ("&#128444;", "Briefs the poster and visual creative"),
    "09_reel_script": ("&#127916;", "Scripts reel and video ads"),
    "10_policy_checker": ("&#128737;", "Checks creative text against Meta advertising policy"),
    "11_structure_planner": ("&#129513;", "Plans campaign structure and naming"),
    "12_targeting_planner": ("&#128205;", "Plans audience targeting for each segment"),
    "13_campaign_builder": ("&#128640;", "Builds campaign drafts — only after approval"),
    "14_approval_queue_manager": ("&#128203;", "Manages the pending approval queue"),
    "15_account_health_monitor": ("&#128154;", "Monitors compliance and account health flags"),
    "16_data_collector": ("&#128229;", "Collects performance data for analysis"),
    "17_lead_quality_tracker": ("&#11088;", "Tracks enquiries, qualified leads, junk and orders"),
    "18_creative_analyst": ("&#128202;", "Analyses which creatives and angles perform"),
    "19_optimiser": ("&#9881;", "Judges winners and losers and proposes changes"),
    "20_reporter": ("&#128221;", "Writes the daily and weekly performance report"),
}

# Agents page department tabs: (query slug, tab label, ROLE_NAMES group).
ROLE_DEPT_TABS = [
    ("all", "All Agents", None),
    ("research", "Research & Strategy", "A. Research & Strategy"),
    ("creative", "Creative Production", "B. Creative Production"),
    ("campaign", "Campaign Management", "C. Campaign Management"),
    ("performance", "Performance & Optimisation", "D. Performance & Optimisation"),
]

SETTING_FIELDS = [
    ("TOTAL_DAILY_BUDGET_CAP", "number", "Maximum spend per day across all campaigns combined. 0/empty = no cap set (the optimiser will not run its safety-stop check)."),
    ("PER_CAMPAIGN_CAP", "number", "Maximum budget for a single campaign. 0/empty = unset."),
    ("LIFETIME_CAP", "number", "Maximum total lifetime spend cap. 0/empty = unset."),
    ("TARGET_COST_PER_QUALIFIED_LEAD", "number", "Target cost for one qualified lead. The optimiser judges winners/losers against this — if unset, no judgement is made."),
    ("MIN_SPEND", "number", "An ad with less spend than this is treated as 'not enough data'."),
    ("MIN_EVENTS", "number", "An ad with fewer enquiries than this will not be judged."),
    ("EVALUATION_WINDOW_DAYS", "number", "How many days of data the judgement is based on."),
    ("CONVERSION_LAG_WINDOW_DAYS", "number", "Days conversions take to be reported — ads newer than this are not judged."),
    ("MAX_BUDGET_CHANGE_PCT", "number", "Maximum % limit for a single budget change (no proposal will exceed this either)."),
    ("MIN_DAYS_BETWEEN_CHANGES", "number", "Minimum days between two budget changes."),
    ("ACCOUNT_CURRENCY", "text", "The ad account's currency (e.g. INR). Used for display/reconciliation only."),
    ("ACCOUNT_TIMEZONE", "text", "The ad account's timezone (e.g. Asia/Kolkata)."),
    ("ATTRIBUTION_WINDOW", "text", "The Insights attribution window in use (will be verified in Step 3 — currently UNVERIFIED)."),
    ("DESTINATION_URL", "text", "Where the ad sends traffic — set by the owner only. Empty = destination gate closed."),
    ("DESTINATION_READY", "checkbox", "Ticking this means: the destination page is ready and traffic can be sent there."),
    ("DRY_RUN", "checkbox", "ON (default) = no real writes at all; everything is simulated on MOCK — even in LIVE mode."),
    ("AUTOMATION_MODE", "select", "OFF = reports only. PROPOSE (default) = everything happens only after approval. AUTO_WITHIN_RULES = only when the owner has written and approved the exact rules (Step 5)."),
    ("AUTO_RULES_APPROVED", "checkbox", "For AUTO_WITHIN_RULES: the owner has read and approved the written rules below. Without this, AUTO mode behaves exactly like PROPOSE."),
    ("AUTO_RULES_TEXT", "text", "The written rules for AUTO_WITHIN_RULES (in the owner's own words — which actions may run automatically within the caps)."),
    ("AUTO_COLLECT", "checkbox", "24x7 worker: collect insights automatically every 6 hours. OFF = manual/CLI collect only."),
    ("AUTO_RESEARCH", "checkbox", "24x7 worker: run the Growth Loop cycle (competitor research + briefs) automatically every week."),
    ("AUTO_CREATIVE_DRAFTS", "checkbox", "24x7 worker: create the loop's creative DRAFTS automatically (nothing goes live — drafts stop at the approval queue)."),
    ("AUTO_REPORTS", "checkbox", "24x7 worker: generate the daily/weekly report automatically."),
    ("AUTO_OPTIMISE_PROPOSALS", "checkbox", "24x7 worker: create optimisation PROPOSALS automatically every day (in PROPOSE mode they are never applied automatically)."),
    ("WORKER_TICK_SECONDS", "number", "How often, in seconds, the worker checks the schedule. Empty = 60."),
    ("QUIET_HOURS", "text", "Quiet hours, e.g. 23-07 — during these hours only collect runs. Empty = no quiet hours."),
    ("TOP_CREATIVE_WINDOW_DAYS", "number", "The Growth Loop's top-creative window: 7 or 10 days. 0/empty = 7."),
    ("GUARDRAIL_LEARNING_MIN_DAYS", "number", "Guardrail: BLOCK edits/changes on a live object newer than this many days. 0 = inactive."),
    ("GUARDRAIL_LEARNING_MIN_CONVERSIONS", "number", "Guardrail: BLOCK judging/editing before this many conversions. 0 = inactive."),
    ("GUARDRAIL_MAX_AD_SETS_PER_CAMPAIGN", "number", "Guardrail: more ad sets than this in one campaign = fragmentation BLOCK. 0 = inactive."),
    ("GUARDRAIL_MIN_AD_SET_BUDGET", "number", "Guardrail: WARN when the per-ad-set budget is below this. 0 = inactive."),
    ("GUARDRAIL_MIN_CREATIVES_PER_ADSET", "number", "Guardrail: WARN when an ad set has fewer creatives than this. 0 = inactive."),
    ("GUARDRAILS_DISABLED", "text", "Guardrail ids that are switched OFF (comma-separated) — toggling from the Guardrails page is preferred."),
    ("LEARNING_EVENT_THRESHOLD", "number", "Guardrail D4/D1: an ad set needs at least this many optimisation events per week before a verdict. 0 = inactive. (Research reference only: ~50 — guidance, not a default.)"),
    ("MIN_EVALUATION_DAYS", "number", "Guardrail D2: at least this many days of data before a verdict. 0 = inactive. (Research reference only: ~7 days.)"),
    ("FREQUENCY_CAP_PROSPECTING", "number", "Guardrail D7: prospecting frequency above this = WARN. 0 = inactive. (Research reference only: ~3.)"),
    ("FREQUENCY_CAP_RETARGETING", "number", "Guardrail D7: retargeting frequency cap. 0 = inactive."),
    ("FATIGUE_CTR_DROP_PCT", "number", "Guardrail D7: CTR drop % after which fatigue is flagged (monitor note). 0 = inactive."),
    ("CREATIVES_PER_AD_SET_MIN", "number", "Guardrail D8: minimum creatives per ad set. 0 = inactive. (Research reference only: 3–5.)"),
    ("CREATIVES_PER_AD_SET_MAX", "number", "Guardrail D8: maximum creatives per ad set. 0 = inactive. (Research reference only: 3–5.)"),
    ("HOOK_RATE_FLOOR_PCT", "number", "Guardrail D9: video hook rate below this = WARN. 0 = inactive. (Research reference only: 20–30% practitioner ranges.)"),
    ("HOOK_MIN_IMPRESSIONS", "number", "Guardrail D9: judge the hook rate only after this many impressions. 0 = inactive."),
    ("AUDIENCE_SIZE_FLOOR", "number", "Guardrail D6: audience size below this = WARN. 0 = inactive."),
    ("AUDIENCE_OVERLAP_MAX_PCT", "number", "Guardrail D5: overlap % between ad sets above this = WARN. 0 = inactive."),
    ("LANDING_PAGE_MAX_LOAD_SEC", "number", "Guardrail D11: landing page mobile load time above this many seconds = WARN. 0 = inactive."),
    ("COMMENT_MODERATION_SLA_HOURS", "number", "Guardrail D12: a negative comment left unaddressed longer than this many hours = WARN. 0 = inactive."),
    ("REJECTION_COUNT_LIMIT", "number", "Guardrail D16: more rejections than this in the rolling window = launch freeze BLOCK. 0 = inactive."),
    ("EMQ_MIN", "number", "Guardrail D14: Event Match Quality below this = WARN. 0 = inactive. (Research reference only: ~8 practitioner figure.)"),
    ("PAUSE_RELEARN_DAYS", "number", "Guardrail D25: re-learning WARN when an ad set paused this many days is resumed. 0 = inactive. (Research reference only: 7 days.)"),
    ("REVIEW_CADENCE_DAYS", "number", "Guardrail D23: self-watch WARN when no review has happened for this many days. 0 = inactive."),
]


def esc(x):
    return html.escape(str(x if x is not None else ""))


def page(title, active, body, flash=None, conn=None, ctx=None):
    nav = "".join('<a href="%s" class="%s">%s</a>' % (href, "on" if href == active else "", label)
                  for href, label in NAV)
    kill = ""
    if conn is not None:
        q = ApprovalQueue()
        q.conn = conn
        if q.kill_switch_active():
            kill = ('<div class="banner bad"><strong>KILL SWITCH ON.</strong> '
                    'Automation is disabled and approvals/execution are blocked. '
                    'This never resumes on its own — the owner releases it '
                    'manually in Settings.</div>')
    flash_html = '<div class="flash">%s</div>' % esc(flash) if flash else ""
    biz_tag = "Business · Meta Ads"
    switcher = ""
    if ctx is not None and ctx.get("profile"):
        profile = ctx["profile"]
        biz_tag = "%s · %s" % (profile["name"], profile.get("industry") or "")
        options = "".join(
            '<option value="%d" %s>%s</option>'
            % (p["id"], "selected" if p["id"] == profile["id"] else "", esc(p["name"]))
            for p in profiles_mod.list_profiles(conn))
        switcher = ('<form method="post" action="/profiles/switch" class="inline">%s'
                    '<select name="profile_id" onchange="this.form.submit()" '
                    'style="width:100%%;margin:0 0 10px;padding:6px 8px">%s</select></form>'
                    % (ctx["csrf_field"], options))
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s · SH Ads Desk</title><style>%s</style></head><body>
<div class="layout">
<aside class="sidebar">
<div class="sb-brand">Software Hub</div>
<div class="sb-ws"><div class="t">SH Ads Workspace</div><div class="s">Pro Plan</div></div>
<nav class="side">%s</nav>
<div class="sb-spacer"></div>
<div class="sb-profile">%s
<div class="sb-user"><div class="sb-avatar">SH</div>
<div><div style="font-weight:700;font-size:13.5px">Software Hub</div>
<div class="small mut">Enterprise</div></div></div>
<form method="post" action="/logout" class="inline"><button class="secondary" type="submit" style="width:100%%">Logout</button></form></div>
</aside>
<div class="shell">
<div class="topbar"><span class="ctx">%s</span><span class="tag">%s</span><span class="tag">DRY_RUN + PROPOSE default</span></div>
<main>%s%s%s</main>
<div class="footer">SH Ads Desk · Built for any industry · Step 1 logic VERIFIED (local tests) · Live Meta path UNTESTED · API %s · Provider API keys live only in the server's data/secrets.env file — the app never displays or logs them</div>
</div></div>
</body></html>""" % (esc(title), CSS, nav, switcher, esc(title), esc(biz_tag),
                     kill, flash_html, body, esc(API_VERSION_LABEL))


def simple_page(title, body):
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s · SH Ads Desk</title><style>%s</style></head><body>
<main style="max-width:430px;margin-top:6vh">%s</main></body></html>""" % (
        esc(title), CSS, body)


def mode_banner(settings):
    mode = os.environ.get("META_MODE", "MOCK").upper()
    if mode == "LIVE":
        return ('<div class="banner warn"><strong>META_MODE=LIVE (UNTESTED).</strong> '
                'The real Meta adapter is code-complete but has NOT been tested '
                'on a real account. DRY_RUN=%s — while DRY_RUN is ON, writes are '
                'simulated on MOCK only.</div>' % esc(settings.get("DRY_RUN")))
    return ('<div class="banner ok"><strong>META_MODE=MOCK.</strong> All data and '
            'all writes are mock. The real Meta connection arrives in Steps 2–4 '
            '(currently UNTESTED).</div>')


# ---------------------------------------------------------------- pages (GET)
def pg_mission(ctx):
    """Mission Control — reel-style agent office, with every status
    assembled from REAL system records (role_runs, approval queue,
    worker heartbeat). Nothing is simulated."""
    from . import mission as mission_mod
    conn, settings = ctx["conn"], ctx["settings"]
    profile = ctx["profile"]
    data = mission_mod.mission_data(conn, settings, profile=profile,
                                    queue=ctx["queue"])
    c, k = data["centre"], data["kpis"]
    cnt = c["counts"]
    chip_colors = {"DOING": "#7c3aed", "DONE": "#059669",
                   "NEXT": "#d97706", "WAITING": "#6b7280"}
    # --- Workflow Status donut (SVG, real DOING/DONE/NEXT/WAITING counts)
    donut_colors = (("DOING", "#7c3aed"), ("DONE", "#10b981"),
                    ("NEXT", "#f59e0b"), ("WAITING", "#c9c4d6"))
    total_agents = sum(cnt[s] for s, _col in donut_colors) or 20
    import math
    circ = 2 * math.pi * 64
    segs, start = [], 0.0
    for status_name, color in donut_colors:
        frac = (cnt[status_name] / total_agents) if total_agents else 0
        seg = frac * circ
        segs.append('<circle cx="90" cy="90" r="64" fill="none" stroke="%s" '
                    'stroke-width="26" stroke-dasharray="%.2f %.2f" '
                    'stroke-dashoffset="%.2f"/>'
                    % (color, seg, circ - seg, -start))
        start += seg
    legend = "".join(
        '<div class="mc-legend-row"><span class="mc-dot" style="background:%s"></span>'
        '%s<span class="mc-legend-n">%d</span></div>'
        % (color, status_name, cnt[status_name])
        for status_name, color in donut_colors)
    donut_html = (
        '<div class="mc-donut-wrap"><svg viewBox="0 0 180 180" class="mc-donut">'
        '<g transform="rotate(-90 90 90)">%s</g>'
        '<text x="90" y="88" text-anchor="middle" class="mc-donut-total">%d</text>'
        '<text x="90" y="110" text-anchor="middle" class="mc-donut-sub">Agents</text>'
        '</svg><div class="mc-legend">%s</div></div>'
        % ("".join(segs), total_agents, legend))
    # --- Task Activity line chart (SVG polyline, role_runs per day, 7 days)
    act = data.get("activity") or []
    max_count = max([p["count"] for p in act] + [1])
    pts, dots, labels = [], [], []
    if act:
        plot_w, plot_h, left, top = 500, 140, 34, 14
        for i, p in enumerate(act):
            x = left + (plot_w * i / (len(act) - 1 if len(act) > 1 else 1))
            y = top + plot_h - (p["count"] / max_count) * plot_h
            pts.append("%.1f,%.1f" % (x, y))
            dots.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#7c3aed"/>' % (x, y))
            labels.append('<text x="%.1f" y="%d" text-anchor="middle" '
                          'class="mc-axis">%s</text>' % (x, top + plot_h + 20,
                                                         esc(p["label"])))
    activity_html = (
        '<svg viewBox="0 0 560 190" class="mc-chart">'
        '<line x1="34" y1="154" x2="534" y2="154" stroke="#e8e8f0"/>'
        '<text x="4" y="18" class="mc-axis">%d</text>'
        '<polyline points="%s" fill="none" stroke="#7c3aed" stroke-width="2.5"/>'
        '%s%s</svg>'
        % (max_count, " ".join(pts), "".join(dots), "".join(labels)))
    # --- Department cards with progress bars
    dept_html = []
    for dept in data["departments"]:
        agents = []
        for a in dept["agents"]:
            num = a["id"].split("_")[0]
            last = ("Last run: %s" % esc(a["last_run"])) if a["last_run"] else "Not run yet"
            pulse = " mc-pulse" if a["status"] == "DOING" else ""
            agents.append(
                '<div class="mc-agent"><div class="mc-num" style="background:%s">%s</div>'
                '<div class="mc-agent-main"><div class="mc-agent-name">%s</div>'
                '<div class="mc-agent-last">%s</div></div>'
                '<span class="mc-chip%s" style="background:%s">%s</span></div>'
                % (dept["color"], num, esc(a["label"]), last, pulse,
                   chip_colors[a["status"]], a["status"]))
        dept_html.append(
            '<div class="card mc-dept"><div class="mc-dept-head">'
            '<span class="mc-dept-badge" style="background:%s">%s</span>'
            '<div><div class="mc-dept-name">%s</div>'
            '<div class="small mut">%d Agents</div></div>'
            '<span class="mc-dept-pct">%d%%</span></div>'
            '<div class="mc-bar"><div class="mc-bar-fill" style="width:%d%%;background:%s"></div></div>'
            '%s</div>'
            % (dept["color"], esc(dept["name"].split(".")[0]),
               esc(dept["name"]), len(dept["agents"]), dept["progress"],
               dept["progress"], dept["color"], "".join(agents)))
    worker_pill = ('<span class="pill ok">WORKER LIVE</span>' if c["worker_live"]
                   else '<span class="pill">WORKER IDLE</span>')
    kill_pill = ('<span class="pill bad">KILL SWITCH ON</span>' if c["kill_switch"]
                 else '<span class="pill ok">SYSTEM ACTIVE</span>')
    body = """
<style>
.mc-head{display:flex;align-items:flex-start;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.mc-head .sub{color:var(--mut);font-size:13.5px}
.mc-head .pills{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap}
.mc-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-bottom:16px}
.mc-kpi{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:0 1px 3px rgba(31,27,80,.05)}
.mc-kpi b{font-size:26px;display:block;letter-spacing:-.5px}
.mc-kpi .lbl{font-weight:600;font-size:14px}
.mc-charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:14px}
.mc-donut-wrap{display:flex;align-items:center;gap:18px;flex-wrap:wrap}
.mc-donut{width:180px;height:180px;flex:none}
.mc-donut-total{font-size:30px;font-weight:800;fill:var(--ink)}
.mc-donut-sub{font-size:12px;fill:var(--mut)}
.mc-legend{flex:1;min-width:130px}
.mc-legend-row{display:flex;align-items:center;gap:8px;padding:4px 0;font-size:14px}
.mc-dot{width:10px;height:10px;border-radius:50%%;flex:none}
.mc-legend-n{margin-left:auto;font-weight:700}
.mc-chart{width:100%%;height:auto}
.mc-axis{font-size:11px;fill:var(--mut)}
.mc-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:14px}
.mc-dept-head{display:flex;align-items:center;gap:11px;margin-bottom:10px}
.mc-dept-badge{color:#fff;font-weight:800;border-radius:10px;width:34px;height:34px;display:flex;align-items:center;justify-content:center;flex:none}
.mc-dept-name{font-weight:700;font-size:15.5px}
.mc-dept-pct{margin-left:auto;font-weight:700;color:var(--mut)}
.mc-bar{background:#f1f0fb;border-radius:20px;height:8px;margin-bottom:10px;overflow:hidden}
.mc-bar-fill{height:100%%;border-radius:20px}
.mc-agent{display:flex;align-items:center;gap:11px;padding:9px 4px;border-bottom:1px solid var(--line)}
.mc-agent:last-child{border-bottom:none}
.mc-num{color:#fff;font-weight:700;border-radius:10px;width:34px;height:34px;display:flex;align-items:center;justify-content:center;font-size:14px;flex:none}
.mc-agent-main{flex:1;min-width:0}
.mc-agent-name{font-weight:600;font-size:14.5px}
.mc-agent-last{color:var(--mut);font-size:12px}
.mc-chip{color:#fff;border-radius:20px;padding:3px 11px;font-size:11.5px;font-weight:700;flex:none}
.mc-pulse{animation:mcpulse 1.2s infinite}
@keyframes mcpulse{0%%{opacity:1}50%%{opacity:.45}100%%{opacity:1}}
</style>
<div class="mc-head"><div>
<h1>&#129302; Mission Control</h1>
<div class="sub">SH ADS DESK — META ADS AGENT &middot; %s &middot; Mode: %s &middot; 20 Agents &middot; 4 Departments</div>
<div class="sub">Every status comes from real records — role runs, the approval queue and the worker heartbeat. This page refreshes itself every 30 seconds.</div>
</div><div class="pills">%s %s</div></div>
<div class="mc-kpis">
<div class="mc-kpi"><b>%d</b><span class="lbl">Pending Approvals</span><div class="small mut">Waiting in the approval queue</div></div>
<div class="mc-kpi"><b>%d</b><span class="lbl">Queue Jobs</span><div class="small mut">Waiting for the 24x7 worker</div></div>
<div class="mc-kpi"><b>%d</b><span class="lbl">Creatives</span><div class="small mut">Saved creative sets and drafts</div></div>
<div class="mc-kpi"><b>%d</b><span class="lbl">Reports</span><div class="small mut">Daily + weekly reports saved</div></div>
</div>
<div class="mc-charts">
<div class="card"><h2>Workflow Status</h2>
<p class="small mut" style="margin-top:-6px">Real-time task distribution across departments</p>
%s</div>
<div class="card"><h2>Task Activity</h2>
<p class="small mut" style="margin-top:-6px">Role runs per day — last 7 days</p>
%s</div>
</div>
<h2 style="margin:4px 0 12px">Departments</h2>
<div class="mc-grid">%s</div>
<script>setTimeout(function(){location.reload()},30000)</script>
""" % (esc(c["profile"]), esc(c["automation_mode"]), worker_pill, kill_pill,
       k["pending_approvals"], k["queue_pending"], k["creatives"],
       k["reports"], donut_html, activity_html, "".join(dept_html))
    return page("Mission Control", "/mission", body, ctx["flash"], conn, ctx)


def _donut_svg(items, centre_top, centre_sub):
    """Donut chart from [(label, value, color)] — real values only.
    Returns SVG + legend HTML with % shares."""
    import math
    total = sum(v for _l, v, _c in items) or 1
    circ = 2 * math.pi * 64
    segs, start = [], 0.0
    for _label, value, color in items:
        seg = (value / total) * circ
        segs.append('<circle cx="90" cy="90" r="64" fill="none" stroke="%s" '
                    'stroke-width="26" stroke-dasharray="%.2f %.2f" '
                    'stroke-dashoffset="%.2f"/>'
                    % (color, seg, circ - seg, -start))
        start += seg
    legend = "".join(
        '<div class="mc-legend-row"><span class="mc-dot" style="background:%s"></span>'
        '%s<span class="mc-legend-n">%s · %.0f%%</span></div>'
        % (color, esc(label), value, 100.0 * value / total)
        for label, value, color in items)
    return ('<div class="mc-donut-wrap"><svg viewBox="0 0 180 180" class="mc-donut">'
            '<g transform="rotate(-90 90 90)">%s</g>'
            '<text x="90" y="88" text-anchor="middle" class="mc-donut-total">%s</text>'
            '<text x="90" y="110" text-anchor="middle" class="mc-donut-sub">%s</text>'
            '</svg><div class="mc-legend">%s</div></div>'
            % ("".join(segs), esc(centre_top), esc(centre_sub), legend))


def pg_today(ctx):
    conn, settings = ctx["conn"], ctx["settings"]
    profile = ctx["profile"]
    pid = profile["id"] if profile else 0
    store.seed_insights(conn=conn, profile_id=pid)
    rows = store.load_insight_rows(conn, profile_id=pid)
    queue = ctx["queue"]
    pending = queue.list_pending(profile_id=pid)
    spend = sum(float(r.get("spend") or 0) for r in rows)
    enq = sum(int(r.get("enquiries") or 0) for r in rows)
    qual = sum(int(r.get("qualified_leads") or 0) for r in rows)
    junk = sum(int(r.get("junk_leads") or 0) for r in rows)
    leads = store.lead_summary(conn)
    biz = esc(profile["name"]) if profile else "Software Hub"
    ind = esc(profile.get("industry") or "") if profile else ""
    status = loop_mod.loop_status(conn, pid)
    ran_keys = {s["key"] for s in status["stages"] if s["last_run"]}
    chips = ""
    for key, label in loop_mod.STAGES:
        short = label.split("·", 1)[-1].strip()
        cls = "done" if key in ran_keys else ("now" if key == status["current_stage"] else "")
        pill = ('<span class="pill ok">done</span>' if key in ran_keys
                else '<span class="pill info">next</span>' if key == status["current_stage"]
                else '<span class="pill dim">queued</span>')
        chips += '<span class="stage %s"><span class="dot"></span>%s %s</span>' % (
            cls, esc(short), pill)
    kill_pill = ('<span class="pill bad">BLOCKED — kill switch ON</span>'
                 if queue.kill_switch_active()
                 else '<span class="pill ok">system clear</span>')
    mode = os.environ.get("META_MODE", "MOCK").upper()
    # --- Analytics components (real rows only; no invented history) ---
    quality_donut = _donut_svg(
        [("Qualified", qual, "#7c3aed"), ("Enquiries", enq, "#10b981"),
         ("Junk", junk, "#f59e0b")],
        str(qual + enq + junk), "Leads")
    by_spend = sorted(rows, key=lambda r: float(r.get("spend") or 0),
                      reverse=True)
    max_spend = max([float(r.get("spend") or 0) for r in by_spend] + [1])
    max_leads = max([int(r.get("qualified_leads") or 0) for r in by_spend] + [1])
    s_pts, l_pts, dots, xlabels = [], [], [], []
    if by_spend:
        plot_w, plot_h, left, top = 500, 130, 34, 14
        n = len(by_spend)
        for i, r in enumerate(by_spend):
            x = left + (plot_w * i / (n - 1 if n > 1 else 1))
            ys = top + plot_h - (float(r.get("spend") or 0) / max_spend) * plot_h
            yl = top + plot_h - (int(r.get("qualified_leads") or 0) / max_leads) * plot_h
            s_pts.append("%.1f,%.1f" % (x, ys))
            l_pts.append("%.1f,%.1f" % (x, yl))
            dots.append('<circle cx="%.1f" cy="%.1f" r="3.5" fill="#7c3aed"/>'
                        '<circle cx="%.1f" cy="%.1f" r="3.5" fill="#10b981"/>'
                        % (x, ys, x, yl))
            xlabels.append('<text x="%.1f" y="%d" text-anchor="middle" '
                           'class="mc-axis">%s</text>'
                           % (x, top + plot_h + 18, esc(r.get("ad_id") or "")))
    spend_leads_chart = (
        '<svg viewBox="0 0 560 180" class="mc-chart">'
        '<line x1="34" y1="144" x2="534" y2="144" stroke="#e8e8f0"/>'
        '<polyline points="%s" fill="none" stroke="#7c3aed" stroke-width="2.5"/>'
        '<polyline points="%s" fill="none" stroke="#10b981" stroke-width="2.5"/>'
        '%s%s</svg>'
        '<div class="small mut"><span style="color:#7c3aed">●</span> Spend '
        '(max %s) &nbsp; <span style="color:#10b981">●</span> Qualified leads '
        '(max %d) — each series scaled to its own maximum; snapshot data, '
        'no daily history yet.</div>'
        % (" ".join(s_pts), " ".join(l_pts), "".join(dots), "".join(xlabels),
           esc(max_spend), max_leads))
    target_cpq = float(settings.get("TARGET_COST_PER_QUALIFIED_LEAD") or 0)
    camps = {}
    for r in rows:
        c = camps.setdefault(r.get("campaign_id") or "—",
                             {"formats": set(), "leads": 0, "cost": 0.0})
        if r.get("format"):
            c["formats"].add(str(r["format"]))
        c["leads"] += int(r.get("qualified_leads") or 0)
        c["cost"] += float(r.get("spend") or 0)
    camp_rows = ""
    for cid, cdata in sorted(camps.items(), key=lambda kv: kv[1]["cost"],
                             reverse=True):
        if target_cpq > 0 and cdata["leads"]:
            cpq = cdata["cost"] / cdata["leads"]
            verdict = ('<span class="pill ok">Winner</span>' if cpq <= target_cpq
                       else '<span class="pill bad">Loser</span>')
        elif target_cpq > 0:
            verdict = '<span class="pill bad">Loser</span>'
        else:
            verdict = '<span class="pill dim">Not judged — set target cost per qualified lead</span>'
        camp_rows += ("<tr><td>%s</td><td>%s</td><td>%d</td><td>%s</td><td>%s</td></tr>"
                      % (esc(cid), esc(", ".join(sorted(cdata["formats"])) or "—"),
                         cdata["leads"], esc(cdata["cost"]), verdict))
    body = """
<style>
.kpi-card{display:flex;gap:13px;align-items:flex-start}
.kpi-ic{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;
justify-content:center;font-size:18px;flex:none;background:var(--violetbg)}
.mc-donut-wrap{display:flex;align-items:center;gap:18px;flex-wrap:wrap}
.mc-donut{width:170px;height:170px;flex:none}
.mc-donut-total{font-size:28px;font-weight:800;fill:var(--ink)}
.mc-donut-sub{font-size:12px;fill:var(--mut)}
.mc-legend{flex:1;min-width:140px}
.mc-legend-row{display:flex;align-items:center;gap:8px;padding:4px 0;font-size:14px}
.mc-dot{width:10px;height:10px;border-radius:50%%;flex:none}
.mc-legend-n{margin-left:auto;font-weight:700}
.mc-chart{width:100%%;height:auto}.mc-axis{font-size:11px;fill:var(--mut)}
.an-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:14px}
</style>
<h1>%s</h1><p class="mut">%s · DRY_RUN + PROPOSE — nothing happens without approval. %s</p>
%s
<div class="grid">
 <div class="card kpi-card"><div class="kpi-ic">₹</div><div><div class="mut small">Spend (MOCK)</div><div class="kpi">%s</div>
 <div class="small mut">Currency: %s</div></div></div>
 <div class="card kpi-card"><div class="kpi-ic">✓</div><div><div class="mut small">Qualified leads</div><div class="kpi">%d</div>
 <div class="small mut">Enquiries %d · Junk %d</div></div></div>
 <div class="card kpi-card"><div class="kpi-ic">⏳</div><div><div class="mut small">Approvals pending</div><div class="kpi">%d</div>
 <div class="small mut"><a href="/approvals">Open the queue →</a></div></div></div>
 <div class="card kpi-card"><div class="kpi-ic">⚙</div><div><div class="mut small">Mode</div><div class="kpi">%s</div>
 <div class="small mut">Live Meta path UNTESTED</div></div></div>
</div>
<div class="an-grid">
<div class="card"><h2>Spend vs Leads</h2>
<p class="small mut" style="margin-top:-6px">Per ad, sorted by spend <span class="pill dim" style="float:right">Snapshot · MOCK data</span></p>
%s</div>
<div class="card"><h2>Lead Quality</h2>
<p class="small mut" style="margin-top:-6px">Qualified vs enquiries vs junk — current data</p>
%s</div>
</div>
<div class="card"><h2>Top Campaigns</h2>
<div class="twrap"><table><tr><th>Campaign</th><th>Channel</th><th>Leads</th><th>Cost</th><th>Status</th></tr>%s</table></div></div>
<div class="card"><h2>Growth Loop</h2>
<div class="stages">%s</div>
<p style="margin-top:14px"><a class="btn bigbtn" href="/loop">Run the loop →</a>
&nbsp; %s</p></div>
<div class="card"><h2>Departments</h2>
<div class="grid">
 <div><strong>Research</strong><div class="small mut">Competitors, angles, trends<br>
 <a href="/roles">Roles</a> · <a href="/trends">Knowledge</a></div></div>
 <div><strong>Creative</strong><div class="small mut">Copy, posters, reels, API generation<br>
 <a href="/creative">Creative Studio</a> · <a href="/providers">API Providers</a></div></div>
 <div><strong>Launch</strong><div class="small mut">Plan → guardrail pre-flight → approval<br>
 <a href="/planner">Planner</a> · <a href="/approvals">Approvals</a></div></div>
 <div><strong>Safety</strong><div class="small mut">Gates, policy, CPC/CPL guardrails<br>
 <a href="/eligibility">Eligibility</a> · <a href="/guardrails">Guardrails</a></div></div>
</div></div>
<details><summary>How it works — all details</summary>
<p class="small">This desk is built for <strong>any industry</strong> — switch the
business from the sidebar profile switcher; every profile
(<a href="/profiles">Business Profiles</a>) keeps its own catalog, competitors,
settings and data separate. The eligibility gate fails closed: until an
offering's permission is confirmed with proof, no ad can be created for it.
Lead log counts: total %d · orders %d · reseller applications %d.
The numbers on this page come from the MOCK demo dataset — real numbers
arrive after Step 3 (read-only API). Meta connection status:
<a href="/connect">Connect wizard</a> · <a href="/reports">Reports</a> ·
<a href="/budget">Budget</a> · <a href="/leads">Leads</a></p>
</details>
""" % (biz, ind, kill_pill, mode_banner(settings), esc(spend),
       esc(settings.get("ACCOUNT_CURRENCY") or "unset"),
       qual, enq, junk, len(pending), esc(mode),
       spend_leads_chart, quality_donut,
       camp_rows or '<tr><td colspan="5" class="mut">No campaign data yet</td></tr>',
       chips, kill_pill,
       sum(leads.values()), int(leads.get("order", 0)),
       int(leads.get("reseller_application", 0)))
    return page("Today", "/", body, ctx["flash"], conn, ctx)


def pg_connect(ctx):
    conn = ctx["conn"]
    checks = [
        ("Facebook Page (created by the owner on Meta)", bool(os.environ.get("META_PAGE_ID")),
         "META_PAGE_ID env"),
        ("Meta Business portfolio + ad account", bool(os.environ.get("META_AD_ACCOUNT_ID")),
         "META_AD_ACCOUNT_ID env"),
        ("Developer app + access token (issued on Meta's own screens)",
         bool(os.environ.get("META_ACCESS_TOKEN")), "META_ACCESS_TOKEN env — never typed inside this app"),
        ("Mode", True, "META_MODE=%s (default MOCK)" % os.environ.get("META_MODE", "MOCK")),
    ]
    rows_html = "".join(
        "<tr><td>%s</td><td>%s</td><td class='small mut'>%s</td></tr>"
        % (esc(name), '<span class="pill ok">Set</span>' if ok else '<span class="pill bad">Missing</span>', esc(hint))
        for name, ok, hint in checks)
    body = """
<h1>Connect Wizard — Meta setup (Step 2 guide)</h1>
<p class="mut">This page only shows what is connected and what is still missing. This app
<strong>never asks for a password</strong> — login always happens on Meta's own screens.
The token lives only in the server's environment (.env); it is never typed inside the app.</p>
%s
<div class="card"><h2>Status</h2><table><tr><th>Item</th><th>Status</th><th>Note</th></tr>%s</table></div>
<div class="card"><h2>Owner's manual steps (on Meta's screens)</h2>
<p class="small mut">The full screen-by-screen guide is in the package: <strong>SETUP_GUIDE.md</strong> —
follow that. Only a summary is below. <strong>Note:</strong> if Meta login itself is
blocked (suspended account), the first route is Meta's appeal/recovery —
never create a new account or Page to dodge a ban (that is against policy).</p>
<ol class="check">
<li>Create a Facebook Page (if you don't have one) — facebook.com/pages/create</li>
<li>On business.facebook.com, create a Business portfolio and add the Page + ad account</li>
<li>Add a payment method in the ad account's Meta billing screen (this app never asks for a card)</li>
<li>Create an app on developers.facebook.com → first only the <strong>"Measure ad performance data"</strong> use case (read-only); "Create &amp; manage ads" only after Step 4 approval</li>
<li>Permissions: read-only (ads_read) first — write (ads_management) only after Step 4 approval</li>
<li>Generate the token and put it in your server's .env as META_ACCESS_TOKEN; the ad account id as META_AD_ACCOUNT_ID</li>
<li>Keep META_MODE on MOCK until Step 3 (read-only comparison) passes</li></ol>
<p class="small mut"><strong>Verified in Step 2 (2026-11-16, by reading the official Authorization page):</strong>
for your <em>own</em> ad account, <code>ads_read</code>/<code>ads_management</code>
<strong>standard access is enough</strong> — advanced access / App Review is needed only when
the app manages <em>other people's</em> accounts. The access tiers' new names (since May 2026):
<strong>Limited</strong> (default, for development, heavily rate-limited) and
<strong>Full</strong> (App Review + 500+ successful calls in the last 15 days + error rate under 15%%).
Full details with URL + date are in the package's <strong>META_ACCESS.md</strong> and
<strong>PRACTICES.md</strong>.
API version pin: %s</p></div>
""" % (mode_banner(ctx["settings"]), rows_html, esc(API_VERSION_LABEL))
    return page("Connect", "/connect", body, ctx["flash"], conn, ctx)


def _parse_ts(ts):
    """Parse a stored timestamp (UTC ISO from common._now); naive values
    are treated as UTC. Returns None when unparseable."""
    from datetime import datetime, timezone
    try:
        parsed = datetime.fromisoformat(str(ts))
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _rel_time(ts, now):
    """Relative label for a stored timestamp: 'Now', '12 min ago',
    '1 hour ago', '3 days ago'; '—' when there is no timestamp."""
    parsed = _parse_ts(ts) if ts else None
    if parsed is None:
        return "—"
    secs = (now - parsed).total_seconds()
    if secs < 60:
        return "Now"
    mins = int(secs // 60)
    if mins < 60:
        return "%d min ago" % mins
    hours = mins // 60
    if hours < 24:
        return "%d hour%s ago" % (hours, "s" if hours != 1 else "")
    days = hours // 24
    return "%d day%s ago" % (days, "s" if days != 1 else "")


def _fmt_date(ts):
    """'16 Nov 2026' for a stored timestamp; '' when there is none."""
    parsed = _parse_ts(ts) if ts else None
    if parsed is None:
        return ""
    return parsed.strftime("%d %b %Y")


def pg_roles(ctx):
    """Agents — the 20 fixed logical roles in the owner's reference
    layout. Every count and status is derived from the real role_runs
    table: a role whose last run is within 5 minutes is Running, a role
    that has run is Completed, a role that never ran is Idle."""
    from datetime import datetime, timedelta, timezone
    conn = ctx["conn"]
    now = datetime.now(timezone.utc)
    runs = conn.execute(
        "SELECT role, status, output, created_at FROM role_runs "
        "ORDER BY id").fetchall()
    last, ran_today, errs = {}, set(), set()
    for r in runs:
        last[r["role"]] = r  # latest wins (ordered by id)
        if str(r["created_at"] or "")[:10] == now.date().isoformat():
            ran_today.add(r["role"])
        if r["status"] == "error":
            errs.add(r["role"])

    def status_of(key):
        run = last.get(key)
        if run is None:
            return "Idle"
        ts = _parse_ts(run["created_at"])
        if ts is not None and now - ts <= timedelta(minutes=5):
            return "Running"
        return "Completed"

    known = [key for key, _label, _group in ROLE_NAMES]
    n_active = sum(1 for k in known if status_of(k) == "Running")
    n_idle = sum(1 for k in known if k not in last)
    n_today = len(ran_today.intersection(known))

    dept = (ctx.get("query") or {}).get("dept", ["all"])[0]
    if dept not in [slug for slug, _l, _g in ROLE_DEPT_TABS]:
        dept = "all"
    want_group = {slug: g for slug, _l, g in ROLE_DEPT_TABS}[dept]

    tabs = []
    for slug, tlabel, tgroup in ROLE_DEPT_TABS:
        n = len(known) if tgroup is None else sum(
            1 for _k, _l, g in ROLE_NAMES if g == tgroup)
        href = "/roles" if slug == "all" else "/roles?dept=%s" % slug
        tabs.append('<a class="ag-tab%s" href="%s">%s (%d)</a>'
                    % (" on" if slug == dept else "", href, esc(tlabel), n))

    dot_colors = {"Completed": "#10b981", "Running": "#7c3aed", "Idle": "#b6b3c7"}
    text_colors = {"Completed": "var(--ok)", "Running": "var(--brand2)",
                   "Idle": "var(--mut)"}
    rows_html = []
    for key, label, group in ROLE_NAMES:
        if want_group is not None and group != want_group:
            continue
        name = label.split(" · ", 1)[1] if " · " in label else label
        icon, desc = ROLE_DESCRIPTIONS.get(key, ("&#8226;", ""))
        dept_name = group.split(". ", 1)[1] if ". " in group else group
        st = status_of(key)
        status_html = ('<span style="color:%s;font-weight:600;white-space:nowrap">'
                       '<span class="ag-dot" style="background:%s"></span>%s</span>'
                       % (text_colors[st], dot_colors[st], st))
        if key in errs:
            status_html += ' <span class="pill bad">Has errors</span>'
        run = last.get(key)
        last_run = _rel_time(run["created_at"], now) if run else "—"
        rows_html.append(
            '<tr><td><div class="ag-agent"><span class="ag-chip">%s</span>'
            '<div><strong>%s</strong><div class="small mut">%s</div></div></div></td>'
            '<td><span class="pill dim">%s</span></td>'
            '<td>%s</td><td style="white-space:nowrap">%s</td>'
            '<td style="white-space:nowrap"><form method="post" action="/roles/run" '
            'class="inline">%s<button type="submit" class="runbtn">&#9654; Run</button>'
            '</form> <span class="mut">&#8942;</span></td></tr>'
            % (icon, esc(name), esc(desc), esc(dept_name), status_html,
               esc(last_run), ctx["csrf_field"]))

    outputs_html = ""
    done = [(key, label) for key, label, _g in ROLE_NAMES if key in last]
    if done:
        blocks = []
        for key, label in done:
            out = str(last[key]["output"] or "")
            if len(out) > 600:
                out = out[:600] + " …"
            blocks.append("<h3>%s</h3><pre>%s</pre>" % (esc(label), esc(out)))
        outputs_html = ('<details><summary>Latest role outputs '
                        '(from role_runs)</summary>%s</details>'
                        % "".join(blocks))

    body = """
<style>
.ag-eyebrow{color:var(--brand);font-weight:700;letter-spacing:2px;font-size:12px}
.ag-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:16px 0 18px}
.ag-stat{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;display:flex;gap:14px;align-items:center;box-shadow:0 1px 3px rgba(31,27,80,.05)}
.ag-ic{width:46px;height:46px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:19px;flex:none}
.ag-stat b{font-size:24px;display:block;line-height:1.15;letter-spacing:-.5px}
.ag-stat .lbl{color:var(--mut);font-size:13px}
.ag-tabs{display:flex;gap:4px;flex-wrap:wrap;border-bottom:1px solid var(--line);margin-bottom:16px}
.ag-tab{padding:9px 14px;font-weight:600;font-size:14px;color:var(--mut);border-bottom:2px solid transparent;margin-bottom:-1px}
.ag-tab:hover{text-decoration:none;color:var(--ink)}
.ag-tab.on{color:var(--brand2);border-bottom-color:var(--brand)}
.ag-agent{display:flex;gap:12px;align-items:center}
.ag-chip{width:38px;height:38px;border-radius:10px;background:var(--violetbg);display:inline-flex;align-items:center;justify-content:center;font-size:17px;flex:none}
.ag-dot{width:9px;height:9px;border-radius:50%%;display:inline-block;margin-right:7px}
button.runbtn{background:#fff;color:var(--ink);border:1px solid var(--line);padding:6px 14px;border-radius:9px;font-size:13.5px;font-weight:600}
button.runbtn:hover{border-color:var(--brand);color:var(--brand2);background:#f5f2ff}
</style>
<div class="ag-eyebrow">&mdash; AI AUTOMATION</div>
<h1>Agents</h1>
<p class="mut" style="margin-top:-4px">20 AI agents across 4 departments, working for your workspace</p>
<div class="ag-stats">
<div class="ag-stat"><span class="ag-ic" style="background:var(--violetbg)">&#129302;</span><div><b>%d</b><span class="lbl">Total Agents</span></div></div>
<div class="ag-stat"><span class="ag-ic" style="background:var(--okbg)">&#9654;</span><div><b>%d</b><span class="lbl">Active</span></div></div>
<div class="ag-stat"><span class="ag-ic" style="background:var(--warnbg)">&#10074;&#10074;</span><div><b>%d</b><span class="lbl">Idle</span></div></div>
<div class="ag-stat"><span class="ag-ic" style="background:var(--violetbg)">&#10003;</span><div><b>%d</b><span class="lbl">Completed (Today)</span></div></div>
</div>
<div class="ag-tabs">%s</div>
<div class="card" style="padding:6px 18px"><div class="twrap"><table>
<tr><th>Agent</th><th>Department</th><th>Status</th><th>Last Run</th><th>Actions</th></tr>
%s
</table></div></div>
<div class="card"><h2>Run roles once (MOCK)</h2>
<p class="small">Every role's output is separate and auditable. The statuses above come from
the real <code>role_runs</code> table — roles also run via the jobs
(<code>python -m app.jobs optimise</code>). There is no always-on agent.</p>
<form method="post" action="/roles/run">%s
<p class="small">Pressing this button — or any row's Run button — runs Roles 1–9, 11, 12,
15–18, 20 once on MOCK data via the existing <code>/roles/run</code> action; outputs are
logged in <code>role_runs</code> and the audit log. Roles 10/13/14/19 run from their own
pages (Creative / Approvals / Optimiser). Nothing is written to Meta.</p>
<button type="submit">Run roles once (MOCK)</button></form></div>
%s
""" % (len(known), n_active, n_idle, n_today, "".join(tabs),
       "".join(rows_html), ctx["csrf_field"], outputs_html)
    return page("Roles", "/roles", body, ctx["flash"], conn, ctx)


ADVANCED_SETTING_KEYS = {
    "GUARDRAIL_LEARNING_MIN_DAYS", "GUARDRAIL_LEARNING_MIN_CONVERSIONS",
    "GUARDRAIL_MAX_AD_SETS_PER_CAMPAIGN", "GUARDRAIL_MIN_AD_SET_BUDGET",
    "GUARDRAIL_MIN_CREATIVES_PER_ADSET", "GUARDRAILS_DISABLED",
    "LEARNING_EVENT_THRESHOLD", "MIN_EVALUATION_DAYS",
    "FREQUENCY_CAP_PROSPECTING", "FREQUENCY_CAP_RETARGETING",
    "FATIGUE_CTR_DROP_PCT", "CREATIVES_PER_AD_SET_MIN",
    "CREATIVES_PER_AD_SET_MAX", "HOOK_RATE_FLOOR_PCT", "HOOK_MIN_IMPRESSIONS",
    "AUDIENCE_SIZE_FLOOR", "AUDIENCE_OVERLAP_MAX_PCT",
    "LANDING_PAGE_MAX_LOAD_SEC", "COMMENT_MODERATION_SLA_HOURS",
    "REJECTION_COUNT_LIMIT", "EMQ_MIN", "PAUSE_RELEARN_DAYS",
    "REVIEW_CADENCE_DAYS", "CONVERSION_LAG_WINDOW_DAYS", "LIFETIME_CAP",
    "AUTO_RULES_APPROVED", "AUTO_RULES_TEXT",
}


_SETTING_LABELS = {
    "TOTAL_DAILY_BUDGET_CAP": "Total Daily Budget Cap",
    "PER_CAMPAIGN_CAP": "Per Campaign Cap",
    "TARGET_COST_PER_QUALIFIED_LEAD": "Target Cost per Qualified Lead",
    "MAX_BUDGET_CHANGE_PCT": "Max Budget Change %",
    "DESTINATION_URL": "Destination URL",
    "DESTINATION_READY": "Mark as Destination Ready",
    "AUTOMATION_MODE": "Automation Mode",
    "QUIET_HOURS": "Quiet Hours",
    "AUTO_COLLECT": "Auto Collect",
    "AUTO_RESEARCH": "Auto Research",
    "AUTO_CREATIVE_DRAFTS": "Auto Creative Drafts",
    "AUTO_REPORTS": "Auto Reports",
    "AUTO_OPTIMISE_PROPOSALS": "Auto Optimise Proposals",
}


def _setting_label(key):
    if key in _SETTING_LABELS:
        return _SETTING_LABELS[key]
    return key.replace("_", " ").title().replace(" Url", " URL").replace(" Pct", " %")


def pg_settings(ctx):
    conn = ctx["conn"]
    settings = load_settings()  # global file; profile overrides win at read time
    kinds = {k: (kind, helptext) for k, kind, helptext in SETTING_FIELDS}

    def field_html(key):
        kind, helptext = kinds[key]
        val = settings.get(key)
        if kind == "checkbox":
            input_html = ('<input type="checkbox" name="%s" %s style="width:auto">'
                          % (key, "checked" if val else ""))
        elif kind == "select":
            opts = "".join('<option %s>%s</option>' % (
                "selected" if val == o else "", o)
                for o in ("OFF", "PROPOSE", "AUTO_WITHIN_RULES"))
            input_html = '<select name="%s">%s</select>' % (key, opts)
        else:
            input_html = '<input name="%s" value="%s">' % (
                key, esc(val if val is not None else ""))
        return ('<div class="fld"><label>%s</label>%s'
                '<p class="small mut" style="margin-top:2px">%s</p></div>'
                % (esc(_setting_label(key)), input_html, esc(helptext)))

    def switch_html(key):
        _kind, helptext = kinds[key]
        return ('<div class="sw-row"><div><div style="font-weight:600">%s</div>'
                '<div class="small mut">%s</div></div>'
                '<label class="switch"><input type="checkbox" name="%s" %s>'
                '<span class="track"></span></label></div>'
                % (esc(_setting_label(key)), esc(helptext), key,
                   "checked" if settings.get(key) else ""))

    caps_keys = ["TOTAL_DAILY_BUDGET_CAP", "PER_CAMPAIGN_CAP",
                 "TARGET_COST_PER_QUALIFIED_LEAD", "MAX_BUDGET_CHANGE_PCT"]
    auto_keys = ["AUTO_COLLECT", "AUTO_RESEARCH", "AUTO_CREATIVE_DRAFTS",
                 "AUTO_REPORTS", "AUTO_OPTIMISE_PROPOSALS"]
    rules_keys = ["AUTO_RULES_APPROVED", "AUTO_RULES_TEXT"]
    placed = set(caps_keys + auto_keys + rules_keys +
                 ["DESTINATION_URL", "DESTINATION_READY", "AUTOMATION_MODE",
                  "QUIET_HOURS"])
    rest_keys = [k for k, _kind, _h in SETTING_FIELDS
                 if k not in placed and k not in ADVANCED_SETTING_KEYS]
    advanced_keys = [k for k, _kind, _h in SETTING_FIELDS
                     if k in ADVANCED_SETTING_KEYS and k not in placed]
    kill_on = ctx["queue"].kill_switch_active()
    from . import autonomy as autonomy_mod
    _asum = autonomy_mod.autonomy_summary(conn, settings)
    _on = [lbl for k, lbl in autonomy_mod.TOGGLES if _asum["toggles"].get(k)]
    worker_html = (
        "Worker heartbeat: <strong>%s</strong> · Queue backend: <strong>%s</strong> "
        "· Pending jobs: <strong>%d</strong> · Quiet hours: <strong>%s</strong><br>"
        "Auto features ON: %s<br><span class='mut'>The worker is a separate 24x7 "
        "service (the 'worker' in docker-compose). It automates housekeeping only — "
        "Meta writes always stay inside AUTOMATION_MODE + the signed rules.</span>"
        % (esc(_asum["worker_heartbeat"] or "No heartbeat yet — the worker is not running"),
           esc(_asum["queue_backend"]), _asum["queue_pending"],
           esc(_asum["quiet_hours"] or "none"),
           esc(", ".join(_on) if _on else "None — all auto features are OFF")))
    body = """
<style>
.set-head{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap}
.set-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:start}
@media(max-width:860px){.set-grid{grid-template-columns:1fr}}
.caps-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px 16px}
@media(max-width:640px){.caps-grid{grid-template-columns:1fr}}
.fld label{margin-top:8px}
.switch{position:relative;display:inline-block;width:46px;height:26px;flex:none}
.switch input{opacity:0;width:0;height:0;position:absolute}
.switch .track{position:absolute;inset:0;background:#d8d8e4;border-radius:999px;transition:.2s;cursor:pointer}
.switch .track:before{content:"";position:absolute;width:20px;height:20px;border-radius:50%%;
background:#fff;top:3px;left:3px;transition:.2s;box-shadow:0 1px 3px rgba(0,0,0,.25)}
.switch input:checked + .track{background:var(--brand)}
.switch input:checked + .track:before{transform:translateX(20px)}
.sw-row{display:flex;align-items:center;justify-content:space-between;gap:12px;
padding:9px 0;border-bottom:1px solid var(--line)}
.sw-row:last-child{border-bottom:none}
.kill-card{background:#fef2f2;border:1px solid #fecaca}
.kill-flex{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
</style>
<form method="post" action="/settings">%s
<div class="set-head"><div>
<h1 style="margin-bottom:2px">Settings</h1>
<p class="mut" style="margin:0">Manage budget caps, automation, and safety controls for your workspace</p>
<p class="small mut">Global settings — defaults are empty/zero, nothing is hardcoded.
Per-business overrides live on <a href="/profiles">Profiles</a>; guardrail toggles on
<a href="/guardrails">Guardrails</a>. Saving writes to this server's local settings file
(with an audit log entry) — it never writes anything to Meta.</p>
</div><button type="submit" class="bigbtn">Save Changes</button></div>
<div class="set-grid">
<div>
<div class="card"><h2>Budget Caps</h2><div class="caps-grid">%s</div></div>
<div class="card"><h2>Destination Gate</h2>%s%s</div>
</div>
<div>
<div class="card"><h2>Automation</h2>%s%s%s
<p class="small mut">AUTO_WITHIN_RULES applies only when the written rules below are
approved. Going LIVE, raising caps and resuming after a safety stop are never automatic.</p></div>
<div class="card"><h2>24x7 Worker Status</h2>
<p class="small">%s</p></div>
</div>
</div>
<div class="card"><h2>Automation Rules (AUTO_WITHIN_RULES)</h2>%s</div>
<div class="card"><h2>Thresholds &amp; Account</h2><div class="caps-grid">%s</div></div>
<div class="card"><details><summary>Advanced — guardrail thresholds (%d fields)</summary>
<div class="caps-grid">%s</div></details></div>
<p><button type="submit" class="bigbtn">Save Changes</button></p>
</form>
<div class="card kill-card"><div class="kill-flex"><div style="flex:1;min-width:260px">
<h2 style="color:var(--bad);margin-top:0">Kill Switch</h2>
<p class="small" style="margin-bottom:6px">Activating the kill switch pauses every managed
campaign, disables all automation and blocks approvals and execution. It
<strong>never resumes on its own</strong> — only the owner can release it, from this card.</p>
<p class="small" style="margin:0">Current status: %s</p></div>
<form method="post" action="/killswitch">%s
<input type="hidden" name="action" value="%s">
<button class="danger" type="submit">%s</button></form></div></div>
""" % (ctx["csrf_field"],
       "".join(field_html(k) for k in caps_keys),
       field_html("DESTINATION_URL"), field_html("DESTINATION_READY"),
       field_html("AUTOMATION_MODE"),
       "".join(switch_html(k) for k in auto_keys),
       field_html("QUIET_HOURS"),
       worker_html,
       "".join(field_html(k) for k in rules_keys),
       "".join(field_html(k) for k in rest_keys),
       len(advanced_keys),
       "".join(field_html(k) for k in advanced_keys),
       '<span class="pill bad">ON — everything is stopped</span>' if kill_on else '<span class="pill ok">OFF</span>',
       ctx["csrf_field"], "off" if kill_on else "on",
       "Release Kill Switch (owner action)" if kill_on else "Activate Kill Switch")
    return page("Settings", "/settings", body, ctx["flash"], conn, ctx)


def pg_eligibility(ctx):
    conn, settings = ctx["conn"], ctx["settings"]
    profile = ctx["profile"]
    pid = profile["id"] if profile else 0
    offerings = profiles_mod.list_offerings(pid, conn)
    perm_label = esc(profile.get("permission_label") or "eligibility permission confirmed") \
        if profile else "eligibility permission confirmed"
    preset = industries_mod.get_preset(profile.get("industry_preset")) if profile else {}
    rows_html = []
    for o in offerings:
        confirmed = o["permission_confirmed"]
        pill = ('<span class="pill ok">CONFIRMED</span>' if confirmed
                else '<span class="pill bad">NOT CONFIRMED — no ad can be created</span>')
        rows_html.append(
            "<tr><td><strong>%s</strong></td><td>%s</td><td>%s</td><td>%s</td>"
            "<td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (esc(o["name"]), esc(o["type"]), esc(o["category"] or "—"),
               esc(o["price"] or "—"), esc(o["supplier"] or "—"), pill,
               esc(o["proof_note"] or "—"), esc(o["terms_checked_date"] or "—")))
    options = "".join('<option value="%d">%s</option>' % (o["id"], esc(o["name"]))
                      for o in offerings)
    dest = policy_checker.check_destination(settings)
    pack = profiles_mod.compliance_patterns_for(profile)
    pack_html = "".join(
        "<li><code>%s</code> — %s</li>" % (esc(p["pattern"]), esc(p["reason"]))
        for p in pack) or "<li class='mut'>This preset has no add-on pack — only the core Meta rules apply.</li>"
    body = """
<h1>Eligibility &amp; Destination Gate — %s</h1>
<p class="mut">Rule: until an offering's <strong>%s is confirmed with a proof note +
terms-checked date</strong>, the system will not create an ad for that offering
(fails closed — the same strictness for every industry).
%s</p>
<div class="card"><h2>Offerings catalog (%d) — %s</h2>
<table><tr><th>Offering</th><th>Type</th><th>Category</th><th>Price</th><th>Supplier/Source</th><th>Permission</th><th>Proof note</th><th>Terms checked</th></tr>%s</table></div>
<div class="card"><h2>Add an offering</h2>
<form method="post" action="/eligibility/add">%s
<label>Name</label><input name="name" required>
<div class="row"><div style="flex:1"><label>Type</label><select name="type"><option>product</option><option>service</option></select></div>
<div style="flex:1"><label>Category</label><input name="category"></div>
<div style="flex:1"><label>Price (optional)</label><input name="price"></div></div>
<label>Supplier / source note</label><input name="supplier">
<label>Destination override (optional — this offering's own landing URL)</label><input name="destination_override">
<p class="small">Adding creates the offering as UNCONFIRMED — an ad can be created
only after its permission is confirmed below.</p>
<button type="submit">Add offering</button></form></div>
<div class="card"><h2>Confirm permission (owner only)</h2>
<form method="post" action="/eligibility/confirm">%s
<label>Offering</label><select name="offering_id">%s</select>
<label>Supplier</label><input name="supplier" placeholder="Supplier name (as in the proof)">
<label>Proof note</label><input name="proof_note" placeholder="Where the proof is — file/agreement reference" required>
<label>Terms checked date</label><input name="terms_checked_date" type="date" required>
<p class="small">Confirming only updates this offering's catalog entry.
If the proof note or date is empty, the confirm is <strong>refused</strong>.
This creates no ad — it only opens the gate.</p>
<button type="submit">Confirm permission</button></form>
<form method="post" action="/eligibility/unconfirm" style="margin-top:10px">%s
<label>Withdraw permission — Offering</label><select name="offering_id">%s</select>
<p class="small">Unconfirming blocks that offering's ads again.</p>
<button class="secondary" type="submit">Unconfirm</button></form>
<form method="post" action="/eligibility/delete" style="margin-top:10px">%s
<label>Remove offering — Offering</label><select name="offering_id">%s</select>
<label><input type="checkbox" name="confirm_delete" style="width:auto"> Yes, delete it permanently</label>
<button class="danger" type="submit">Delete</button></form></div>
<div class="card"><h2>Industry compliance add-on pack — %s</h2>
<p class="small mut">These patterns apply ON TOP of Meta's universal core rules
(the policy checker runs both). A preset is an editable starting point —
this is not legal advice.</p>
<ul class="check">%s</ul></div>
<div class="card"><h2>Destination gate</h2>
<p>Current status: %s</p>
<p class="small mut">DESTINATION_URL and DESTINATION_READY are set from Settings/Profile
overrides — the system never picks a destination itself, and no traffic goes
anywhere until the owner says so. If an offering has its own destination
override, that override applies to that offering's drafts.</p></div>
""" % (esc(profile["name"]) if profile else "—", perm_label,
       esc(preset.get("permission_note", "")),
       len(offerings), esc(profile["name"]) if profile else "—",
       "".join(rows_html) or '<tr><td colspan="8" class="mut">The catalog is empty — add the first offering</td></tr>',
       ctx["csrf_field"], ctx["csrf_field"], options, ctx["csrf_field"], options,
       ctx["csrf_field"], options,
       esc(profile.get("industry") or "") if profile else "", pack_html,
       '<span class="pill ok">OPEN</span>' if dest["allowed"]
       else '<span class="pill bad">CLOSED</span> — ' + esc("; ".join(dest["reasons"])))
    return page("Eligibility", "/eligibility", body, ctx["flash"], conn, ctx)


def pg_creative(ctx):
    conn = ctx["conn"]
    products = ctx["eligibility"]
    options = "".join('<option>%s</option>' % esc(p.get("product")) for p in products)
    segments = "".join('<option>%s</option>' % s for s in
                       ("students", "freelancers", "creators", "bot owners", "agencies"))
    saved = store.list_creatives(conn, profile_id=ctx["profile"]["id"] if ctx["profile"] else None)
    saved_html = ""
    for c in saved:
        pill = ('<span class="pill ok">Policy PASS</span>' if c["policy_allowed"]
                else '<span class="pill bad">Policy BLOCKED</span>')
        saved_html += ('<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                       % (c["id"], esc(c["product"]), esc(c["kind"]), pill))
    assets = store.list_assets(conn, limit=20)
    asset_html = ""
    for a in assets:
        view = ""
        if (a["source"] or "").startswith("api"):
            if "." in a["filename"] and " " not in a["filename"]:
                view = ' <a href="/generated/%s" target="_blank" rel="noopener">view</a>' % esc(a["filename"])
            if a["remote_url"]:
                view += ' · <a href="%s" target="_blank" rel="noopener">provider link</a>' % esc(a["remote_url"])
        asset_html += ('<tr><td>%s%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                       % (esc(a["filename"]), view, esc(a["kind"]),
                          esc(a["source"] or "manual upload (owner)"),
                          '<span class="pill ok">Visual check PASS</span>'
                          if a["visual_check"] == "PASS"
                          else '<span class="pill warn">Visual check PENDING</span>'))
    # --- API generation section ---
    api_status = {cap: providers.connection_status(cap) for cap in providers.CAPABILITIES}

    def api_pill(cap):
        s = api_status[cap]
        if s["configured"]:
            return '<span class="pill ok">Connected — %s (%s)</span>' % (
                esc(s["provider_name"]), esc(s["model"] or "model unset"))
        return ('<span class="pill bad">API not connected</span> '
                '<span class="small">— connect it from the <a href="/providers">API Providers page</a></span>')

    jobs = store.list_video_jobs(conn)
    job_html = ""
    for j in jobs[-10:]:
        job_html += ('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
                     '<td><form method="post" action="/creative/api_video_check" class="inline">%s'
                     '<input type="hidden" name="job_id" value="%s">'
                     '<button class="secondary" type="submit">Check status</button></form></td></tr>'
                     % (esc(j.get("job_id")), esc(j.get("provider")), esc(j.get("status")),
                        esc((j.get("prompt") or "")[:60]), ctx["csrf_field"],
                        esc(j.get("job_id"))))
    api_section = """
<div class="card"><h2>Generate with API (the owner's connected APIs)</h2>
<p class="small mut">These actions only generate — nothing is written to Meta.
Generated copy passes the policy check first; generated files are saved as assets
with visual check PENDING. Cost everywhere stays <strong>unknown — provider billing</strong>.
The adapters are UNTESTED on real accounts.</p>
<h3>Ad copy — Text API: %s</h3>
<form method="post" action="/creative/api_copy">%s
<label>Product</label><select name="product">%s</select>
<label>Segment</label><select name="segment">%s</select>
<label>Extra instruction (optional)</label><input name="instruction" placeholder="E.g.: write from the hostel-student angle">
<p class="small">If the API is not connected, template drafts are created and clearly labelled.</p>
<button type="submit">Generate copy (API/templates)</button></form>
<h3>Poster image — Image API: %s</h3>
<form method="post" action="/creative/api_image">%s
<label>Image prompt</label><textarea name="prompt" rows="2" placeholder="Prompt for the poster — clean, with no brand logos or claims" required></textarea>
<button type="submit">Create poster image</button></form>
<h3>Carousel — Image API (one slide = one line = one image)</h3>
<form method="post" action="/creative/api_carousel">%s
<label>Slide briefs (each line is one slide's prompt)</label>
<textarea name="slides" rows="4" placeholder="Slide 1 prompt&#10;Slide 2 prompt&#10;Slide 3 prompt" required></textarea>
<button type="submit">Create carousel images</button></form>
<h3>Reel video — Video API: %s</h3>
<form method="post" action="/creative/api_video">%s
<label>Video prompt</label><textarea name="prompt" rows="2" placeholder="Prompt for the reel" required></textarea>
<label>Image URL (optional — for image-to-video)</label><input name="image_url">
<div class="row"><div style="flex:1"><label>Duration (optional)</label><input name="duration" placeholder="5"></div>
<div style="flex:1"><label>Aspect ratio (optional)</label><input name="aspect" placeholder="9:16"></div></div>
<p class="small">Submitting sends the video job to the provider. Poll its status from the
table below with "Check status" — when done, the file arrives here as an asset.</p>
<button type="submit">Submit reel video</button></form>
%s
</div>
""" % (api_pill("text"), ctx["csrf_field"], options, segments,
       api_pill("image"), ctx["csrf_field"], ctx["csrf_field"],
       api_pill("video"), ctx["csrf_field"],
       ('<h3>Video jobs</h3><table><tr><th>Job ID</th><th>Provider</th><th>Status</th>'
        '<th>Prompt</th><th>Action</th></tr>%s</table>' % job_html) if job_html else "")
    # --- Creative Studio design: header, inspiration, insights, cards ---
    pid = ctx["profile"]["id"] if ctx["profile"] else 0
    window = int(ctx["settings"].get("TOP_CREATIVE_WINDOW_DAYS") or 7)
    brief = loop_mod.inspiration_brief(pid, window, conn=conn, profile=ctx["profile"])
    if brief:
        pattern_box = ('<div class="pattern-box"><strong>Winning Pattern</strong><br>'
                       '<strong>Theme:</strong> %s<br><strong>Hook:</strong> %s<br>'
                       '<strong>Format:</strong> %s<br><strong>CTA style:</strong> %s<br>'
                       '<span class="small mut">Source: %s</span></div>'
                       '<p class="small" style="color:var(--ok);font-weight:600">'
                       '✓ Pattern copied, creative original</p>'
                       % (esc(brief.get("theme", "")), esc(brief.get("hook", "")),
                          esc(brief.get("format", "")), esc(brief.get("cta_style", "")),
                          esc(brief.get("source", ""))))
    else:
        pattern_box = ('<div class="pattern-box"><strong>Winning Pattern</strong><br>'
                       '<span class="mut">No inspiration brief yet — record a top '
                       'creative in the Growth Loop and the brief appears here '
                       'automatically.</span></div>')
    n_sets = len(saved)
    n_pass = sum(1 for c in saved if c["policy_allowed"])
    n_blocked = n_sets - n_pass
    insights_html = (
        '<div class="ins-line"><span>Creative sets</span><strong>%d</strong></div>'
        '<div class="ins-line"><span>Policy PASS</span><strong>%d</strong></div>'
        '<div class="ins-line"><span>Policy BLOCKED</span><strong>%d</strong></div>'
        '<div class="ins-line"><span>Poster briefs</span><strong>%d</strong></div>'
        '<div class="ins-line"><span>Reel scripts</span><strong>%d</strong></div>'
        '<div class="ins-line"><span>Assets registered</span><strong>%d</strong></div>'
        % (n_sets, n_pass, n_blocked, n_sets, n_sets, len(assets)))
    meta_mode = os.environ.get("META_MODE", "MOCK").upper()
    connected = meta_mode == "LIVE" and bool(os.environ.get("META_ACCESS_TOKEN"))
    status_pill = ('<span class="pill ok">Connected</span>' if connected
                   else '<span class="pill dim">Mock Mode</span>')

    def policy_pill(c):
        if c["policy_allowed"]:
            return '<span class="pill ok">Policy Check: PASS</span>'
        try:
            reasons = json.loads(c["policy_reasons"] or "[]")
        except ValueError:
            reasons = []
        return ('<span class="pill bad">Policy Check: BLOCKED%s</span>'
                % ((" — " + esc(reasons[0])) if reasons else ""))

    def card_actions(c, fmt):
        return (
            '<div class="cc-actions">'
            '<form method="post" action="/planner/plan" class="inline">%s'
            '<input type="hidden" name="product" value="%s">'
            '<input type="hidden" name="segment" value="%s">'
            '<input type="hidden" name="audience_type" value="customers">'
            '<input type="hidden" name="format" value="%s">'
            '<button type="submit" class="approve-outline">Approve</button></form>'
            '<form method="post" action="/creative/generate" class="inline">%s'
            '<input type="hidden" name="product" value="%s">'
            '<input type="hidden" name="segment" value="%s">'
            '<button type="submit" class="secondary">Regenerate</button></form></div>'
            % (ctx["csrf_field"], esc(c["product"]), esc(c["segment"]), fmt,
               ctx["csrf_field"], esc(c["product"]), esc(c["segment"])))

    cards_html = ""
    for c in saved[:4]:
        try:
            content = json.loads(c["content"] or "{}")
        except ValueError:
            content = {}
        copy_d = content.get("copy") or {}
        brief_d = content.get("poster_brief") or {}
        script_d = content.get("reel_script") or {}
        headline = copy_d.get("headline") or content.get("angle") or c["product"]
        pill = policy_pill(c)
        # Poster card
        cards_html += (
            '<div class="card cc"><div class="cc-visual"><span>%s</span></div>'
            '<h3>Poster — %s</h3>%s'
            '<p class="small mut">Format: Poster brief (text)</p>'
            '<p class="small">%s</p>%s</div>'
            % (esc(headline), esc(c["product"]), pill,
               esc((brief_d.get("brief") or "")[:220]), card_actions(c, "IMAGE")))
        # Reel card
        lines = script_d.get("script") or []
        hook = lines[0].split("hook:", 1)[-1].strip() if lines else ""
        body_lines = lines[1:-1] if len(lines) > 2 else lines[1:]
        cta_line = lines[-1] if len(lines) > 1 else ""
        dur = script_d.get("duration_sec")
        dur_badge = ('<span class="cc-dur">%ss</span>' % esc(dur)) if dur else ""
        cards_html += (
            '<div class="card cc"><div class="cc-visual"><span class="cc-play">▶</span>'
            '<span>%s</span>%s</div>'
            '<h3>Reel — %s</h3>%s'
            '<p class="small mut">Format: Reel script (text)</p>'
            '<p class="small"><strong>Hook:</strong> %s<br><strong>Body:</strong> %s<br>'
            '<strong>CTA:</strong> %s</p>%s</div>'
            % (esc(headline), dur_badge, esc(c["product"]), pill,
               esc(hook), esc(" ".join(body_lines)[:180]), esc(cta_line),
               card_actions(c, "REEL")))
        # Ad copy card
        cards_html += (
            '<div class="card cc"><div class="cc-visual"><span>%s</span></div>'
            '<h3>Ad Copy — %s</h3>%s'
            '<p class="small mut">Format: Text</p>'
            '<p class="small">%s</p>'
            '<p class="small mut">CTA: %s</p>%s</div>'
            % (esc(headline), esc(c["product"]), pill,
               esc((copy_d.get("primary_text") or "")[:220]),
               esc(copy_d.get("cta") or "—"), card_actions(c, "IMAGE")))
    if not cards_html:
        cards_html = ('<div class="card"><p class="mut">No creative sets yet — '
                      'use "+ Generate New Set" above to create the first one.</p></div>')
    body = """
<style>
.cs-head{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap}
.cs-pills{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.outline-pill{border:1px solid var(--line);border-radius:999px;padding:6px 13px;
font-size:13px;font-weight:600;background:#fff}
.gen-form{display:flex;gap:8px;align-items:flex-end;flex-wrap:wrap}
.gen-form select{width:auto}
.cs-grid{display:grid;grid-template-columns:330px 1fr;gap:14px;align-items:start}
@media(max-width:960px){.cs-grid{grid-template-columns:1fr}}
.pattern-box{background:var(--violetbg);border-radius:12px;padding:13px 15px;font-size:14px}
.ins-line{display:flex;justify-content:space-between;padding:7px 0;
border-bottom:1px solid var(--line);font-size:14px}
.ins-line:last-child{border-bottom:none}
.cc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.cc-visual{background:linear-gradient(135deg,#7c3aed,#a78bfa);color:#fff;border-radius:12px;
padding:20px 16px;min-height:96px;display:flex;align-items:center;gap:10px;
font-weight:700;font-size:16.5px;position:relative;margin-bottom:10px}
.cc-play{background:rgba(255,255,255,.25);border-radius:50%%;width:34px;height:34px;
display:inline-flex;align-items:center;justify-content:center;flex:none}
.cc-dur{position:absolute;right:10px;bottom:10px;background:rgba(0,0,0,.45);
border-radius:7px;padding:2px 8px;font-size:12px}
.cc-actions{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
.approve-outline{background:#fff;color:var(--ok);border:1px solid var(--ok)}
</style>
<div class="cs-head"><div>
<h1 style="margin-bottom:2px">Creative Studio</h1>
<p class="mut" style="margin:0">Review, approve and generate ad creatives powered by SH Ads Desk</p>
<p class="small mut">Creatives here are TEXT — angles, copy, poster briefs and reel
scripts. Real image/video files come from the "Generate with API" section below
(only with the owner's own connected API) or the owner's uploads. Every asset
needs the visual check before it can enter the approval queue.</p>
</div>
<div>
<div class="cs-pills"><span class="outline-pill">SH Ads Desk · Meta Ads</span>%s</div>
<form method="post" action="/creative/generate" class="gen-form" style="margin-top:10px">%s
<select name="product">%s</select>
<select name="segment">%s</select>
<button type="submit" class="bigbtn">+ Generate New Set</button></form>
<p class="small mut">Generating runs Roles 6–9; the copy passes Role 10 (policy checker).
If a gate is closed, the set is marked BLOCKED.</p>
</div></div>
<div class="cs-grid">
<div>
<div class="card"><h2 style="margin-top:0">Inspiration Brief</h2>
%s
<p style="margin-bottom:0"><a class="btn secondary" href="/loop">View Full Brief →</a></p></div>
<div class="card"><h2 style="margin-top:0">Insights</h2>%s
<p class="small mut">Counts from real records only — this system does not invent
creative performance metrics.</p></div>
</div>
<div class="cc-grid">%s</div>
</div>
<div class="card"><h2>Policy checker (instant test)</h2>
<form method="post" action="/creative/policycheck">%s
<label>Ad text</label><textarea name="text" rows="3" placeholder="Write your ad line here — banned claims are caught instantly"></textarea>
<p class="small">Checking only scans — nothing is saved or created.</p>
<button class="secondary" type="submit">Check claims</button></form></div>
%s
<div class="card"><h2>Assets (generated + manual upload)</h2>
<form method="post" action="/creative/upload">%s
<label>File name (keep the file with you — only a registry entry is created here)</label>
<input name="filename" placeholder="poster-v1.png" required>
<label>Kind</label><select name="kind"><option>image</option><option>video</option></select>
<p class="small">Registering adds the asset with visual check PENDING.
It passes only when every checklist item below is ticked — without that, the
asset cannot enter the approval queue.</p>
<button class="secondary" type="submit">Register asset</button></form>
<table><tr><th>File</th><th>Kind</th><th>Source</th><th>Visual check</th></tr>%s</table>
<form method="post" action="/creative/visualcheck" style="margin-top:12px">%s
<label>Asset file name (to mark PASS)</label><input name="filename" required>
<label><input type="checkbox" name="c1" style="width:auto"> The text is readable</label><br>
<label><input type="checkbox" name="c2" style="width:auto"> Product names/logos are correct</label><br>
<label><input type="checkbox" name="c3" style="width:auto"> There is no misleading claim</label><br>
<label><input type="checkbox" name="c4" style="width:auto"> There is no unauthorized brand mark</label>
<p class="small">Marking PASS records the asset's visual check as PASS (with an audit entry).
If even one item is unticked, it is refused.</p>
<button type="submit">Mark visual check PASS</button></form></div>
""" % (status_pill, ctx["csrf_field"], options, segments,
       pattern_box, insights_html, cards_html,
       ctx["csrf_field"],
       api_section,
       ctx["csrf_field"], asset_html or '<tr><td colspan="4" class="mut">No assets registered yet</td></tr>',
       ctx["csrf_field"])
    return page("Creative Studio", "/creative", body, ctx["flash"], conn, ctx)


PROVIDER_FIELD_LABELS = {
    "text": [("chat_path", "Chat/messages path")],
    "image": [("image_path", "Image generation path"),
              ("prompt_field", "Prompt field name"),
              ("model_field", "Model field name"),
              ("size_field", "Size field name"), ("size", "Size"),
              ("response_url_path", "Image URL path in the response"),
              ("response_b64_path", "b64 image path in the response")],
    "video": [("submit_path", "Submit path"),
              ("poll_path", "Status/poll path ({id} = job id)"),
              ("prompt_field", "Prompt field name"),
              ("model_field", "Model field name"),
              ("image_field", "Image URL field name"),
              ("duration_field", "Duration field name"),
              ("aspect_field", "Aspect ratio field name"),
              ("job_id_path", "Job ID path in the response"),
              ("status_path", "Status path in the response"),
              ("done_values", "Done status values (comma-separated)"),
              ("fail_values", "Fail status values (comma-separated)"),
              ("result_url_path", "Result video URL path in the response"),
              ("poll_interval_sec", "Poll interval (seconds)"),
              ("max_wait_sec", "Max wait (seconds)")],
}

PROVIDER_TITLES = {
    "text": ("Text / LLM", "For ad copy — OpenAI (ChatGPT models), Anthropic Claude, or any OpenAI-compatible API."),
    "image": ("Image generation", "For poster and carousel images — an OpenAI-compatible image API or a custom-mapped API."),
    "video": ("Video generation", "For reel video — Higgsfield, Kling-style async APIs (submit + poll)."),
}


def _provider_card(ctx, cap):
    conn = ctx["conn"]
    cfg = providers.get_config(cap)
    status = providers.connection_status(cap)
    preset = cfg["preset"]
    preset_meta = providers.PRESETS[cap][preset]
    preset_opts = "".join(
        '<option value="%s" %s>%s</option>'
        % (k, "selected" if k == preset else "", esc(v["label"]))
        for k, v in providers.PRESETS[cap].items())
    key_pill = ('<span class="pill ok">Key is set (%s)</span>' % esc(status["key_source"])
                if status["key_set"] else '<span class="pill bad">Key is not set</span>')
    conn_pill = ('<span class="pill ok">CONNECTED</span>' if status["configured"]
                 else '<span class="pill warn">Not connected</span>')
    last_test = conn.execute(
        "SELECT value FROM kv WHERE key = ?", ("provider_test_" + cap,)).fetchone()
    test_html = ""
    if last_test:
        try:
            t = json.loads(last_test["value"])
            test_html = ('<p class="small">Last test: %s — %s</p>'
                         % ('<span class="pill ok">Connected (HTTP %s)</span>' % esc(t.get("status"))
                            if t.get("ok") else '<span class="pill bad">Failed</span>',
                            esc(t.get("detail", ""))))
        except ValueError:
            test_html = ""
    cap_fields = "".join(
        '<label>%s</label><input name="%s" value="%s">'
        % (esc(label), name, esc(cfg.get(name) if cfg.get(name) is not None else ""))
        for name, label in PROVIDER_FIELD_LABELS[cap])
    auth_opts = "".join(
        '<option value="%s" %s>%s</option>'
        % (v, "selected" if cfg.get("auth_style") == v else "", label)
        for v, label in (("bearer", "Bearer (Authorization: Bearer KEY)"),
                         ("x-api-key", "x-api-key header"),
                         ("custom", "Custom header + prefix (e.g. Higgsfield: Authorization + 'Key ')")))
    fmt_opts = "".join(
        '<option value="%s" %s>%s</option>'
        % (v, "selected" if cfg.get("payload_format") == v else "", v)
        for v in ("openai", "anthropic"))
    remove_html = ""
    if status["key_source"] == "file":
        remove_html = ("""<form method="post" action="/providers/removekey" class="inline">%s
<input type="hidden" name="capability" value="%s">
<button class="secondary" type="submit">Remove key</button></form>"""
                       % (ctx["csrf_field"], cap))
    elif status["key_source"] == "env":
        remove_html = ('<p class="small mut">The key comes from the environment variable %s — '
                       'to remove it, remove it from the server environment.</p>'
                       % esc(providers.ENV_KEY_NAMES[cap]))
    return """
<div class="card"><h2>%s</h2>
<p class="small mut">%s</p>
<p>%s %s</p>
<p class="small">Preset: <strong>%s</strong> · Base URL: <code>%s</code> · Model: <code>%s</code></p>
<p class="small mut">Base URL source: %s</p>
%s
<form method="post" action="/providers/preset">%s
<input type="hidden" name="capability" value="%s">
<label>Change preset (the preset's pre-filled defaults will apply — base URL, model and paths reset; the key stays)</label>
<select name="preset">%s</select>
<button class="secondary" type="submit">Apply preset</button></form>
<form method="post" action="/providers/save">%s
<input type="hidden" name="capability" value="%s">
<input type="hidden" name="preset" value="%s">
<label>Provider name (for your own identification)</label>
<input name="provider_name" value="%s">
<label>Model</label>
<input name="model" value="%s">
<label>API key %s</label>
<input type="password" name="api_key" autocomplete="off" placeholder="%s">
<details><summary><strong>Advanced (optional)</strong> — base URL override, auth and paths. Known presets have all of this pre-filled; change it only if the provider's docs say otherwise.</summary>
<label>Base URL %s</label>
<input name="base_url" value="%s">
<label>Auth style</label><select name="auth_style">%s</select>
<label>Auth header name</label><input name="auth_header" value="%s">
<label>Auth value prefix (e.g. 'Key ' or 'Bearer ')</label><input name="auth_prefix" value="%s">
<label>Extra headers (JSON object, optional)</label>
<textarea name="extra_headers" rows="2">%s</textarea>
<label>Test connection path (GET — a harmless models/list-type endpoint)</label>
<input name="test_path" value="%s">
<label>Payload format</label><select name="payload_format">%s</select>
%s
</details>
<p class="small">Saving saves only the settings above. The key changes only when a new key
is typed in the key field — left empty, the old key stays.
The key goes into the server's <code>data/secrets.env</code> file (never into
settings/DB/logs) and is never shown here again.</p>
<button type="submit">Save connection</button></form>
<div class="row" style="margin-top:10px">
<form method="post" action="/providers/test" class="inline">%s
<input type="hidden" name="capability" value="%s">
<button class="secondary" type="submit">Test connection</button></form>
%s</div>
<p class="small mut">Test connection makes only one harmless GET (models/list type) —
no generation happens and nothing is charged. Green means the endpoint responded;
it is not a guarantee that generation will work. These adapters are
<strong>UNTESTED</strong> on real provider accounts.</p>
</div>
""" % (esc(PROVIDER_TITLES[cap][0]), esc(PROVIDER_TITLES[cap][1]),
       conn_pill, key_pill, esc(preset_meta["label"]), esc(cfg.get("base_url") or "—"),
       esc(cfg.get("model") or "—"), esc(preset_meta["base_url_source"]), test_html,
       ctx["csrf_field"], cap, preset_opts, ctx["csrf_field"], cap, preset,
       esc(cfg.get("provider_name") or ""), esc(cfg.get("model") or ""),
       "(set via env var %s)" % providers.ENV_KEY_NAMES[cap] if status["key_source"] == "env"
       else "(will be stored in the server's secrets file)",
       "Key is set — type a new key only to change it, otherwise leave it empty"
       if status["key_set"] else "Paste your API key here",
       "— mandatory for the Custom preset" if preset == "custom" else "(optional override)",
       esc(cfg.get("base_url") or ""), auth_opts, esc(cfg.get("auth_header") or ""),
       esc(cfg.get("auth_prefix") or ""), esc(cfg.get("extra_headers") or ""),
       esc(cfg.get("test_path") or ""), fmt_opts, cap_fields,
       ctx["csrf_field"], cap, remove_html)


CLAUDE_SUBSCRIPTION_NOTE = (
    "Have a Claude Pro or Max plan? Subscriptions work only inside "
    "Claude's own apps — Anthropic does not allow connecting them to "
    "external software. An API key is the only supported way here.")


def _ichips(labels):
    return '<div class="ichips">%s</div>' % "".join(
        '<span class="ichip">%s</span>' % esc(x) for x in labels)


def _provider_last_test(conn, cap):
    """Last saved test-connection result line for a capability (same kv
    record the capability cards below use)."""
    row = conn.execute(
        "SELECT value FROM kv WHERE key = ?", ("provider_test_" + cap,)).fetchone()
    if not row:
        return ""
    try:
        t = json.loads(row["value"])
    except ValueError:
        return ""
    return ('<p class="small">Last test: %s — %s</p>'
            % ('<span class="pill ok">Connected (HTTP %s)</span>' % esc(t.get("status"))
               if t.get("ok") else '<span class="pill bad">Failed</span>',
               esc(t.get("detail", ""))))


def _integration_meta_card(ctx):
    live = os.environ.get("META_MODE", "MOCK").upper() == "LIVE"
    token = bool(os.environ.get("META_ACCESS_TOKEN"))
    if live and token:
        pill = '<span class="pill ok">Connected</span>'
    elif live:
        pill = '<span class="pill bad">Not Connected</span>'
    else:
        pill = '<span class="pill dim">Mock Mode</span>'
    return """
<div class="icard">
<div class="ihead2"><div class="ititle"><span class="iicon">&#8734;</span>Meta Ads</div>%s</div>
<p class="small mut">Run and optimise campaigns across Facebook &amp; Instagram.</p>
%s
<div style="margin-top:auto"><a class="btn ibtn" href="/connect">Connect</a>
<p class="small mut" style="margin:8px 0 0">Opens the Connect wizard. The access token
itself is set in the server's .env as META_ACCESS_TOKEN — it is never typed
inside this app.</p></div></div>
""" % (pill, _ichips(["Campaigns", "Audience Sync", "Ad Insights"]))


def _integration_library_card(ctx):
    return """
<div class="icard">
<div class="ihead2"><div class="ititle"><span class="iicon">&#128269;</span>Meta Ad Library</div><span class="pill info">Public Search</span></div>
<p class="small mut">Search and browse public ad library listings.</p>
%s
<div style="margin-top:auto"><a class="btn secondary ibtn" href="/loop">Open</a>
<p class="small mut" style="margin:8px 0 0">Opens the Growth Loop page, where the
Competitor Research Board holds the ready-made Ad Library search links.</p></div></div>
""" % _ichips(["Search Ads", "View Creatives", "Competitor Insights"])


def _integration_brand_card(ctx, cap, brand_preset, name, icon, desc, chips,
                            note=None):
    """One provider brand card (OpenAI / Claude / Higgsfield / Kling).
    Key management is the EXISTING per-capability machinery: the Save Key
    form posts to /providers/save with this brand's preset, carrying the
    current field values as hidden inputs so nothing else is reset.
    Test/Remove act on the capability, so they are shown only when this
    brand is the capability's active preset. No key value is ever
    rendered — only set/not-set state."""
    conn = ctx["conn"]
    cfg = providers.get_config(cap)
    status = providers.connection_status(cap)
    active = cfg["preset"] == brand_preset
    cap_word = {"text": "Text", "image": "Image", "video": "Video"}[cap]
    if not status["key_set"]:
        pill = '<span class="pill dim">Not Connected</span>'
    elif active:
        pill = '<span class="pill ok">Connected</span>'
    else:
        pill = '<span class="pill warn">Key is set</span>'
    src = cfg if active else providers.preset_defaults(cap, brand_preset)
    hidden = "".join(
        '<input type="hidden" name="%s" value="%s">'
        % (k, esc(src.get(k) if src.get(k) is not None else ""))
        for k in PROVIDER_FORM_FIELDS[cap])
    placeholder = ("Key is set — type a new key only to change it"
                   if status["key_set"] else "Paste your API key here")
    if active:
        state_html = ('<p class="small">Active %s provider · Preset: <strong>%s</strong>'
                      ' · Model: <code>%s</code></p>'
                      % (cap_word, esc(providers.PRESETS[cap][brand_preset]["label"]),
                         esc(cfg.get("model") or "—")))
    else:
        state_html = ('<p class="small mut">Not the active %s provider right now. '
                      'Saving a key here makes %s the active %s provider — its '
                      'preset defaults apply and the %s settings card below then '
                      'holds the live settings.</p>'
                      % (cap_word, esc(name), cap_word, cap_word))
    manage_html = ""
    if active:
        remove_html = ""
        if status["key_source"] == "file":
            remove_html = ("""<form method="post" action="/providers/removekey" class="inline">%s
<input type="hidden" name="capability" value="%s">
<button class="secondary" type="submit">Remove key</button></form>"""
                           % (ctx["csrf_field"], cap))
        elif status["key_source"] == "env":
            remove_html = ('<p class="small mut">The key comes from the environment '
                           'variable %s — to remove it, remove it from the server '
                           'environment.</p>' % esc(providers.ENV_KEY_NAMES[cap]))
        manage_html = """
<div class="row" style="margin-top:10px">
<form method="post" action="/providers/test" class="inline">%s
<input type="hidden" name="capability" value="%s">
<button class="secondary" type="submit">Test connection</button></form>
%s</div>
%s""" % (ctx["csrf_field"], cap, remove_html, _provider_last_test(conn, cap))
    note_html = ('<p class="small mut">%s</p>' % esc(note)) if note else ""
    return """
<div class="icard">
<div class="ihead2"><div class="ititle"><span class="iicon">%s</span>%s</div>%s</div>
<p class="small mut">%s</p>
%s
%s
<form method="post" action="/providers/save">%s
<input type="hidden" name="capability" value="%s">
<input type="hidden" name="preset" value="%s">
%s
<div class="keyrow"><input type="password" name="api_key" autocomplete="off" placeholder="%s">
<button type="submit">Save Key</button></div></form>
<p class="small mut">The key is stored only in the server's <code>data/secrets.env</code>
file — it is never shown here again.</p>
%s%s
</div>
""" % (icon, esc(name), pill, esc(desc), _ichips(chips), state_html,
       ctx["csrf_field"], cap, brand_preset, hidden, esc(placeholder),
       note_html, manage_html)


def pg_providers(ctx):
    conn = ctx["conn"]
    queue = ApprovalQueue()
    queue.conn = conn
    sys_pill = ('<span class="pill bad">Paused</span>' if queue.kill_switch_active()
                else '<span class="pill ok">All Systems Operational</span>')
    grid = "".join([
        _integration_meta_card(ctx),
        _integration_library_card(ctx),
        _integration_brand_card(
            ctx, "text", "openai_compatible", "OpenAI", "&#9883;",
            "Use GPT models for AI agents and copy generation.",
            ["GPT-4o", "Text Generation", "Code Generation"]),
        _integration_brand_card(
            ctx, "text", "anthropic", "Anthropic Claude", "&#10035;",
            "Claude for reasoning, drafting, and analysis.",
            ["Claude 3.5", "Long Context", "Smart Analysis"],
            note=CLAUDE_SUBSCRIPTION_NOTE),
        _integration_brand_card(
            ctx, "video", "higgsfield_style", "Higgsfield", "&#127916;",
            "Generate video content with Higgsfield models.",
            ["Video Generation", "Templates", "AI Motion"]),
        _integration_brand_card(
            ctx, "video", "kling_style", "Kling AI", "&#127909;",
            "Produce video clips using Kling AI generation.",
            ["Video Generation", "Templates", "High Quality"]),
    ])
    cards = "".join(_provider_card(ctx, cap) for cap in providers.CAPABILITIES)
    body = """
<div class="ihead"><div><h1>Integrations</h1>
<p class="mut" style="margin:0">Connect your ad accounts and AI providers</p></div>
<div>%s</div></div>
<div class="banner warn"><strong>UNTESTED:</strong> these adapters have not been tested on
any real provider account (this build had no real key). Test the first real generation
carefully, with a small prompt. Generation cost goes to the provider's billing — the
app always shows cost as "unknown — provider billing" and never estimates it.</div>
<div class="igrid">%s</div>
<h2>Provider settings — presets, models and advanced options</h2>
<p class="mut">This is where you connect your generation APIs: OpenAI/Claude for text,
an image API for images, a Higgsfield/Kling-style API for video. Known presets have the
<strong>base URL and default model pre-filled — you only paste the API key</strong>.
Creative Studio's "Generate with API" buttons then create copy, posters, carousels
and reels from these APIs. The system never selects a vendor itself and never keeps
a key — the key lives only in this server's <code>data/secrets.env</code>.</p>
%s
<div class="card"><h2>Environment variables (the other way)</h2>
<p class="small">Instead of the UI, you can keep the key in the server environment —
an env key always wins: <code>SH_ADS_TEXT_API_KEY</code>, <code>SH_ADS_IMAGE_API_KEY</code>,
<code>SH_ADS_VIDEO_API_KEY</code>. Keep a backup of <code>data/secrets.env</code> in a
safe place — never put it in git/commits/chat.</p></div>
""" % (sys_pill, grid, cards)
    return page("Integrations", "/providers", body, ctx["flash"], ctx["conn"], ctx)


def pg_planner(ctx):
    products = ctx["eligibility"]
    options = "".join('<option>%s</option>' % esc(p.get("product")) for p in products)
    body = """
<h1>Campaign Planner</h1>
<p class="mut">Creating a plan is only data — nothing is written to Meta. The plan goes
to the approval queue; even after approval, execution creates only PAUSED
objects (and on MOCK while DRY_RUN is ON). Customer and reseller campaigns
always stay separate.</p>
<div class="card"><form method="post" action="/planner/plan">%s
<label>Product</label><select name="product">%s</select>
<label>Segment</label><select name="segment">
<option>students</option><option>freelancers</option><option>creators</option>
<option>bot owners</option><option>agencies</option></select>
<label>Audience type</label><select name="audience_type">
<option>customers</option><option>resellers</option></select>
<label>Format</label><select name="format"><option>REEL</option><option>IMAGE</option><option>CAROUSEL</option></select>
<label>Daily budget (campaign level — optional, within the caps)</label>
<input name="daily_budget" placeholder="Leave empty to keep the budget out of the plan">
<p class="small">Planning builds the structure plan (named AUD_ANGLE_FORMAT_DATE_VERSION)
and sends a CAMPAIGN_DRAFT to the approval queue. The plan's copy passes the
policy check — if a gate is closed, the draft stays BLOCKED and will not execute.</p>
<button type="submit">Create plan + send for approval</button></form></div>
""" % (ctx["csrf_field"], options)
    return page("Planner", "/planner", body, ctx["flash"], ctx["conn"], ctx)


def pg_campaigns(ctx):
    conn, settings = ctx["conn"], ctx["settings"]
    profile = ctx["profile"]
    pid = profile["id"] if profile else 0
    store.seed_insights(conn=conn, profile_id=pid)
    rows = store.load_insight_rows(conn, profile_id=pid)
    cur = settings.get("ACCOUNT_CURRENCY") or "INR"
    sym = "₹" if cur == "INR" else (cur + " ")
    kill_on = ctx["queue"].kill_switch_active()
    from . import optimiser as optimiser_mod
    try:
        per_ad = optimiser_mod.analyse(rows, settings).get("per_ad", {})
    except Exception:
        per_ad = {}

    def verdict_for(ad_ids):
        vs = [str(per_ad.get(a, {}).get("verdict") or "") for a in ad_ids]
        if any(v == "winner" for v in vs):
            return "Winner"
        if any(v.startswith("loser") for v in vs):
            return "Loser"
        if any(v.startswith("not enough data") or v == "fatigued creative"
               for v in vs):
            return "Learning"
        return ""

    camps = {}
    for r in rows:
        cid = r.get("campaign_id") or "—"
        c = camps.setdefault(cid, {"ads": [], "formats": set(), "spend": 0.0,
                                   "enq": 0, "qual": 0, "budgets": {}})
        c["ads"].append(r.get("ad_id"))
        if r.get("format"):
            c["formats"].add(str(r["format"]))
        c["spend"] += float(r.get("spend") or 0)
        c["enq"] += int(r.get("enquiries") or 0)
        c["qual"] += int(r.get("qualified_leads") or 0)
        if r.get("budget_object_id"):
            c["budgets"][r["budget_object_id"]] = float(r.get("current_budget") or 0)
    paused_ids = set()
    try:
        for w in conn.execute("SELECT object_ids FROM meta_writes").fetchall():
            try:
                paused_ids.update(str(i) for i in json.loads(w["object_ids"] or "[]"))
            except ValueError:
                pass
    except Exception:
        paused_ids = set()

    def camp_status(cid):
        return "Paused" if (kill_on or cid in paused_ids) else "Active"

    total_spend = sum(c["spend"] for c in camps.values())
    total_enq = sum(c["enq"] for c in camps.values())
    total_qual = sum(c["qual"] for c in camps.values())
    avg_cpl = (total_spend / total_qual) if total_qual else None
    n_active = sum(1 for cid in camps if camp_status(cid) == "Active")
    n_paused = len(camps) - n_active
    latest_row = conn.execute(
        "SELECT MAX(created_at) AS t FROM insight_rows WHERE profile_id IN (?, 0)",
        (pid,)).fetchone()
    latest_date = (latest_row["t"] or "")[:10] if latest_row else ""
    status_filter = (ctx.get("query") or {}).get("status", ["all"])[0]
    if status_filter not in ("all", "active", "paused"):
        status_filter = "all"
    fmt_icon = {"reel": "▶", "image": "▣", "carousel": "▦", "video": "▶"}
    shown = 0
    table_rows = ""
    for cid, c in sorted(camps.items(), key=lambda kv: kv[1]["spend"],
                         reverse=True):
        st = camp_status(cid)
        if status_filter != "all" and st.lower() != status_filter:
            continue
        shown += 1
        fmt = sorted(c["formats"])[0] if c["formats"] else ""
        icon = fmt_icon.get(fmt, "•")
        st_pill = ('<span class="pill ok">Active</span>' if st == "Active"
                   else '<span class="pill dim">Paused</span>')
        budget = sum(c["budgets"].values())
        cpl = ("%s%s" % (sym, esc(round(c["spend"] / c["qual"], 2)))) if c["qual"] else "—"
        verdict = verdict_for(c["ads"])
        v_pill = {"Winner": '<span class="pill ok">Winner</span>',
                  "Learning": '<span class="pill warn">Learning</span>',
                  "Loser": '<span class="pill bad">Loser</span>'}.get(verdict, "—")
        table_rows += ("<tr><td><span class='camp-ic'>%s</span> <strong>%s</strong>"
                       "<div class='small mut' style='margin-left:30px'>Meta · %s</div></td>"
                       "<td>%s</td><td>%s</td><td>%s</td><td>%d</td><td>%s</td>"
                       "<td>%s</td><td class='mut'>⋯</td></tr>"
                       % (icon, esc(cid), esc(fmt or "—"), st_pill,
                          ("%s%s/day" % (sym, esc(budget))) if budget else "—",
                          "%s%s" % (sym, esc(c["spend"])), c["enq"], cpl, v_pill))
    # --- New Campaign Draft card data (real gate state) ---
    products = ctx["eligibility"]
    options = "".join('<option>%s</option>' % esc(p.get("product")) for p in products)
    dest = policy_checker.check_destination(settings)
    offerings = profiles_mod.list_offerings(pid, conn)
    any_confirmed = any(o["permission_confirmed"] for o in offerings)
    blockers = []
    if not dest["allowed"]:
        blockers.extend(dest["reasons"])
    if not any_confirmed:
        blockers.append("No offering has confirmed permission yet — drafts stay BLOCKED")
    gate_box = ('<div class="gate-box ok">Ready to submit for review</div>'
                if not blockers else
                '<div class="gate-box bad">Not ready yet:<br>%s</div>'
                % "<br>".join("• " + esc(b) for b in blockers))
    body = """
<style>
.kpi-ic{width:40px;height:40px;border-radius:12px;display:inline-flex;align-items:center;
justify-content:center;font-size:18px;flex:none;background:var(--violetbg)}
.camp-head{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap}
.camp-title{display:flex;gap:13px;align-items:center}
.camp-ic{width:24px;height:24px;border-radius:7px;background:var(--violetbg);
display:inline-flex;align-items:center;justify-content:center;font-size:13px}
.camp-grid{display:grid;grid-template-columns:1.7fr 1fr;gap:14px;align-items:start}
@media(max-width:960px){.camp-grid{grid-template-columns:1fr}}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%%;margin-right:5px}
.gate-box{border-radius:12px;padding:12px 14px;font-size:13.5px;margin:12px 0}
.gate-box.ok{background:var(--violetbg);color:var(--brand2);font-weight:600}
.gate-box.bad{background:#fef2f2;color:#991b1b;border:1px solid #fecaca}
.filter-form select{width:auto;display:inline-block;padding:7px 10px}
</style>
<div class="camp-head"><div class="camp-title">
<span class="kpi-ic" style="width:46px;height:46px;font-size:21px">📣</span>
<div><h1 style="margin:0">Campaigns</h1>
<p class="mut" style="margin:2px 0 0">Manage and monitor your ad campaigns across Meta platforms</p></div>
</div><a class="btn bigbtn" href="#new-draft">+ New Campaign</a></div>
<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(230px,1fr))">
<div class="card"><div class="mut small">Total Campaigns</div><div class="kpi">%d</div>
<div class="small"><span class="dot" style="background:var(--ok)"></span>%d Active
&nbsp;<span class="dot" style="background:#c9c4d6"></span>%d Paused</div></div>
<div class="card"><div class="mut small">Total Spend</div><div class="kpi">%s%s</div>
<div class="small mut">Snapshot · latest insights %s (MOCK data)</div></div>
<div class="card"><div class="mut small">Total Enquiries</div><div class="kpi">%d</div>
<div class="small mut">Avg. CPL %s</div></div>
</div>
<div class="camp-grid">
<div class="card"><div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
<h2 style="margin:0">All Campaigns</h2>
<form method="get" action="/campaigns" class="filter-form">
<label style="display:inline;margin:0">Filter:</label>
<select name="status" onchange="this.form.submit()">
<option value="all" %s>All Status</option>
<option value="active" %s>Active</option>
<option value="paused" %s>Paused</option>
</select> <span class="pill dim">Snapshot data</span></form></div>
<div class="twrap"><table><tr><th>Campaign Name</th><th>Status</th><th>Budget</th>
<th>Spend</th><th>Enquiries</th><th>Cost per Lead</th><th>Verdict</th><th></th></tr>%s</table></div>
<p class="small mut">Showing %d of %d campaigns</p></div>
<div class="card" id="new-draft"><h2 style="margin-top:0">New Campaign Draft</h2>
<form method="post" action="/planner/plan">%s
<label>Product</label><select name="product">%s</select>
<div class="sw-row"><span class="small mut">Objective</span><strong>Outcome Leads</strong></div>
<p class="small mut" style="margin-top:-4px">The planner's default objective (UNTESTED default — the owner confirms the objective in Step 2).</p>
<label>Audience</label><select name="audience_type">
<option>customers</option><option>resellers</option></select>
<label>Segment</label><select name="segment">
<option>students</option><option>freelancers</option><option>creators</option>
<option>bot owners</option><option>agencies</option></select>
<label>Format</label><select name="format"><option>REEL</option><option>IMAGE</option><option>CAROUSEL</option></select>
<label>Daily budget (optional, within the caps)</label><input name="daily_budget">
%s
<button type="submit" class="bigbtn" style="width:100%%">Send to Approval Queue</button>
<p class="small mut" style="text-align:center">Draft will be sent for approval for compliance review.</p>
</form></div>
</div>
""" % (len(camps), n_active, n_paused, sym, esc(total_spend),
       esc(latest_date or "—"), total_enq,
       ("%s%s" % (sym, esc(round(avg_cpl, 2)))) if avg_cpl is not None else "—",
       "selected" if status_filter == "all" else "",
       "selected" if status_filter == "active" else "",
       "selected" if status_filter == "paused" else "",
       table_rows or '<tr><td colspan="8" class="mut">No campaigns match this filter</td></tr>',
       shown, len(camps),
       ctx["csrf_field"], options, gate_box)
    return page("Campaigns", "/campaigns", body, ctx["flash"], conn, ctx)


_PROPOSAL_CHIPS = {
    "PROPOSE_BUDGET_INCREASE": ("Budget Increase", "#fff7ed", "#c2410c", "Role 19 · Optimiser"),
    "PROPOSE_PAUSE": ("Pause", "#fdf2f8", "#be123c", "Role 19 · Optimiser"),
    "CAMPAIGN_DRAFT": ("New Campaign Draft", "#eff6ff", "#1d4ed8", "Role 13 · Campaign Builder"),
    "PROPOSE_CREATIVE_REFRESH": ("Creative Refresh", "#f5f3ff", "#6d28d9", "Role 19 · Optimiser"),
    "SAFETY_STOP": ("Safety Stop", "#fef2f2", "#b91c1c", "Role 19 · Optimiser"),
}


def pg_approvals(ctx):
    conn = ctx["conn"]
    queue = ctx["queue"]
    settings = ctx["settings"]
    pid = ctx["profile"]["id"] if ctx["profile"] else None
    pending = queue.list_pending(profile_id=pid)
    all_items = conn.execute(
        "SELECT * FROM proposals WHERE profile_id IN (?, 0) "
        "ORDER BY id DESC LIMIT 50", (pid or 0,)).fetchall()
    created = {r["id"]: r["created_at"] for r in all_items}
    cards = []
    for item in pending:
        payload = item["payload"] or {}
        chip_label, chip_bg, chip_fg, role = _PROPOSAL_CHIPS.get(
            item["kind"], (item["kind"].replace("_", " ").title(),
                           "#f5f3ff", "#6d28d9", "System"))
        title = payload.get("what") or chip_label
        lines = ""
        if payload.get("why"):
            lines += '<p class="small" style="margin:4px 0">%s</p>' % esc(payload["why"])
        if payload.get("budget_effect"):
            lines += ('<p class="small mut" style="margin:2px 0">Budget effect: %s</p>'
                      % esc(payload["budget_effect"]))
        cards.append("""
<div class="card prop-card">
<div class="prop-top"><span class="type-chip" style="background:%s;color:%s">%s</span>
<span class="small mut">#%d</span></div>
<h3 style="margin:8px 0 2px">%s</h3>
%s
<p class="small mut">Approving marks this item APPROVED — nothing more. Only pressing
"Execute" afterwards creates PAUSED objects (MOCK, or LIVE after Step 4).
Activation is never automatic.</p>
<div class="prop-actions">
<form method="post" action="/approvals/approve" class="inline">%s<input type="hidden" name="id" value="%d"><button type="submit" class="approve-btn">Approve</button></form>
<form method="post" action="/approvals/reject" class="inline">%s<input type="hidden" name="id" value="%d"><button type="submit" class="reject-btn">Reject</button></form>
<span class="prop-meta">Proposed %s • by %s</span>
</div>
<details style="margin-top:10px"><summary>Payload &amp; edit</summary>
<pre>%s</pre>
<form method="post" action="/approvals/edit">%s
<label>Edit payload (JSON)</label><textarea name="payload" rows="4">%s</textarea>
<p class="small">Saving only changes the draft — nothing is executed.</p>
<button class="secondary" type="submit">Save edit</button>
<input type="hidden" name="id" value="%d"></form></details></div>
""" % (chip_bg, chip_fg, esc(chip_label), item["id"], esc(title), lines,
       ctx["csrf_field"], item["id"], ctx["csrf_field"], item["id"],
       esc(created.get(item["id"], "")), esc(role),
       esc(json.dumps(payload, ensure_ascii=False, indent=1)[:3000]),
       ctx["csrf_field"], esc(json.dumps(payload, ensure_ascii=False)), item["id"]))
    history = "".join(
        "<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (r["id"], esc(r["kind"]), esc(r["status"]), esc(r["created_at"]),
           '<form method="post" action="/approvals/execute" class="inline">%s'
           '<input type="hidden" name="id" value="%d"><button type="submit">Execute (PAUSED only)</button></form>'
           % (ctx["csrf_field"], r["id"]) if r["status"] == "APPROVED" else "")
        for r in all_items)
    mode_setting = str(settings.get("AUTOMATION_MODE") or "PROPOSE").upper()
    if mode_setting == "OFF":
        banner_text = ("Automation Off: the system only reports — no changes go live "
                       "without your approval.")
    elif mode_setting == "AUTO_WITHIN_RULES":
        banner_text = ("Auto Within Rules: only the capped actions in your signed rules "
                       "run automatically — everything else needs your approval.")
    else:
        banner_text = "Propose Mode: No changes go live without your approval."
    kill_on = queue.kill_switch_active()
    last_collect_row = conn.execute(
        "SELECT MAX(created_at) AS t FROM role_runs WHERE role = '16_data_collector'"
    ).fetchone()
    last_collect = (last_collect_row["t"] or "")[:16].replace("T", " ") \
        if last_collect_row else ""
    meta_mode = os.environ.get("META_MODE", "MOCK").upper()
    mode_text = ("Mock mode — not connected to Meta Ads" if meta_mode != "LIVE"
                 else "Live mode (path UNTESTED)")
    status_pill = ('<span class="pill bad">Paused</span>' if kill_on
                   else '<span class="pill ok">System Operational</span>')
    body = """
<style>
.appr-grid{display:grid;grid-template-columns:1fr 330px;gap:14px;align-items:start}
@media(max-width:960px){.appr-grid{grid-template-columns:1fr}}
.mode-banner{background:var(--violetbg);border:1px solid #ddd6fe;border-radius:12px;
padding:11px 15px;font-weight:600;color:var(--brand2);margin-bottom:14px}
.type-chip{padding:4px 11px;border-radius:999px;font-size:12px;font-weight:700}
.prop-top{display:flex;justify-content:space-between;align-items:center}
.prop-actions{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-top:10px}
.approve-btn{background:var(--ok);border-color:var(--ok);color:#fff}
.reject-btn{background:#fff;color:var(--bad);border:1px solid var(--bad)}
.prop-meta{margin-left:auto;font-size:12.5px;color:var(--mut)}
.ks-head{background:#dc2626;color:#fff;border-radius:12px 12px 0 0;
padding:11px 15px;font-weight:700;margin:-17px -19px 13px}
.ks-toggle{width:58px;height:32px;border-radius:999px;background:#d8d8e4;
position:relative;border:none;padding:0;cursor:pointer;flex:none}
.ks-toggle:before{content:"";position:absolute;width:26px;height:26px;border-radius:50%%;
background:#fff;top:3px;left:3px;transition:.2s;box-shadow:0 1px 3px rgba(0,0,0,.25)}
.ks-toggle.on{background:#dc2626}
.ks-toggle.on:before{transform:translateX(26px)}
.ks-enable{background:#fff;color:var(--bad);border:1px solid var(--bad);width:100%%}
.status-bar{display:flex;gap:14px;align-items:center;flex-wrap:wrap}
</style>
<h1 style="margin-bottom:2px">Approval Queue — %d Pending</h1>
<p class="mut" style="margin-top:0">Review and approve pending proposals before they go live</p>
<div class="mode-banner">%s</div>
<div class="appr-grid">
<div>
%s
<div class="card"><h2>History</h2>
<div class="twrap"><table><tr><th>#</th><th>Kind</th><th>Status</th><th>Created</th><th>Action</th></tr>%s</table></div>
<p class="small mut">Execute proceeds only when the kill switch is OFF and the status is
APPROVED; for a CAMPAIGN_DRAFT all gates (eligibility, claims, destination) are checked
again — a failure blocks it. The result lands in meta_writes + the audit log.</p></div>
</div>
<div class="card" style="overflow:hidden">
<div class="ks-head">⏻ Kill Switch</div>
<form method="post" action="/killswitch">%s
<input type="hidden" name="action" value="%s">
<div style="display:flex;gap:12px;align-items:center;margin-bottom:10px">
<button type="submit" class="ks-toggle %s" aria-label="Toggle kill switch"></button>
<strong>%s</strong></div>
<p class="small">%s</p>
<p class="small mut">🛡 When enabled, it will instantly pause all live changes and block new approvals for safety.</p>
<button type="submit" class="%s">%s</button></form>
</div>
</div>
<div class="card status-bar"><strong>SH Ads Desk</strong>
<span class="mut">%s</span>
<span class="mut">Last collect: %s</span>
<span style="margin-left:auto">%s</span></div>
""" % (len(pending), esc(banner_text),
       "".join(cards) or '<div class="card">No pending items.</div>', history,
       ctx["csrf_field"], "off" if kill_on else "on", "on" if kill_on else "",
       "Kill switch is ON" if kill_on else "Kill switch is OFF",
       "The emergency stop is engaged — approvals and execution are blocked. Release it here when it is safe to continue."
       if kill_on else
       "Emergency stop is disabled — all proposals remain actionable.",
       "danger" if kill_on else "ks-enable",
       "Release Kill Switch" if kill_on else "Enable Kill Switch",
       esc(mode_text), esc(last_collect or "not collected yet"), status_pill)
    return page("Approvals", "/approvals", body, ctx["flash"], conn, ctx)


def pg_budget(ctx):
    conn, settings = ctx["conn"], ctx["settings"]
    pid = ctx["profile"]["id"] if ctx["profile"] else None
    store.seed_insights(profile_id=pid, conn=conn)
    rows = store.load_insight_rows(conn, profile_id=pid)
    total = sum(float(r.get("spend") or 0) for r in rows)
    cap = float(settings.get("TOTAL_DAILY_BUDGET_CAP") or 0)
    per_rows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (esc(r.get("budget_object_id")), esc(r.get("budget_owner")),
           esc(r.get("current_budget")), esc(r.get("spend")), esc(r.get("ad_id")))
        for r in rows)
    body = """
<h1>Budget View</h1>
%s
<div class="grid">
<div class="card"><div class="mut small">TOTAL_DAILY_BUDGET_CAP (setting)</div>
<div class="kpi">%s</div><div class="small mut">0/empty = cap unset</div></div>
<div class="card"><div class="mut small">Reported spend (MOCK dataset)</div>
<div class="kpi">%s</div><div class="small mut">%s</div></div>
<div class="card"><div class="mut small">PER_CAMPAIGN_CAP / LIFETIME_CAP</div>
<div class="kpi">%s / %s</div><div class="small mut">Changed from Settings</div></div>
</div>
<div class="banner warn"><strong>Reporting delay note:</strong> Meta's reported spend
lags — caps are best-effort and overspend can happen. That is why Meta's own
native limits (account spend limit, campaign/ad-set caps) must also be set (it is
in the Step 2/4 checklist). On a breach the system proposes a safety stop and
never auto-resumes.</div>
<div class="card"><h2>Which object holds the budget</h2>
<p class="small mut">Budgets always sit at campaign or ad-set level — never per-ad.
When the optimiser creates a proposal, it detects the real owner.</p>
<table><tr><th>Budget object</th><th>Owner level</th><th>Current budget</th><th>Spend</th><th>Ad</th></tr>%s</table></div>
<div class="card"><h2>Change the demo dataset (MOCK)</h2>
<form method="post" action="/budget/dataset">%s
<label>Scenario</label><select name="dataset">
<option>thin_data</option><option>one_big_winner</option><option>all_losers</option>
<option>cheap_junk_leads</option><option>lagged_conversions</option>
<option>spend_breach</option><option>fatigue</option></select>
<p class="small">Changing the dataset changes the demo numbers on Budget/Reports/Optimiser.
This is MOCK data only — real data arrives after Step 3.</p>
<button class="secondary" type="submit">Change dataset</button></form>
<form method="post" action="/budget/optimise" style="margin-top:10px">%s
<p class="small">Running the optimiser makes Role 19 create proposals from the current
rows and put them in the approval queue (PROPOSE — nothing is applied). If a spend
breach is found, a safety stop + the kill switch engage.</p>
<button type="submit">Run optimiser — create proposals</button></form></div>
""" % (mode_banner(settings), esc(cap if cap else "unset"), esc(total),
       ('<span class="pill bad">CAP BREACH (MOCK)</span>' if cap and total > cap
        else '<span class="pill ok">Within cap / cap unset</span>'),
       esc(settings.get("PER_CAMPAIGN_CAP") or "unset"),
       esc(settings.get("LIFETIME_CAP") or "unset"), per_rows,
       ctx["csrf_field"], ctx["csrf_field"])
    return page("Budget", "/budget", body, ctx["flash"], conn, ctx)


def pg_leads(ctx):
    conn = ctx["conn"]
    summary = store.lead_summary(conn)
    rows = conn.execute("SELECT * FROM lead_log ORDER BY id DESC LIMIT 30").fetchall()
    hist = "".join("<tr><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>"
                   % (esc(r["ad_ref"]), esc(r["status"]), r["count"], esc(r["created_at"]))
                   for r in rows)
    body = """
<h1>Lead Quality Log</h1>
<p class="mut">Only <strong>counts and statuses</strong> are stored here — never a name,
phone, email or chat. The main metric is cost per QUALIFIED lead; cost per
enquiry is always called provisional.</p>
<div class="grid">%s</div>
<div class="card"><h2>Add an entry</h2>
<form method="post" action="/leads/add">%s
<label>Ad reference (ad id / name)</label><input name="ad_ref" required>
<label>Status</label><select name="status">
<option>enquiry</option><option>real_conversation</option>
<option>reseller_application</option><option>order</option><option>junk</option></select>
<label>Count</label><input name="count" type="number" value="1" min="1">
<p class="small">Adding only adds this count to the lead log (with an audit entry).
Never write personal data — keep ad_ref to the ad's identity only.</p>
<button type="submit">Add lead count</button></form></div>
<div class="card"><h2>Recent entries</h2>
<table><tr><th>Ad ref</th><th>Status</th><th>Count</th><th>When</th></tr>%s</table></div>
""" % ("".join('<div class="card"><div class="mut small">%s</div><div class="kpi">%d</div></div>'
               % (esc(k), v) for k, v in summary.items()),
       ctx["csrf_field"], hist or '<tr><td colspan="4" class="mut">No entries yet</td></tr>')
    return page("Leads", "/leads", body, ctx["flash"], conn, ctx)


def pg_reports(ctx):
    conn = ctx["conn"]
    settings = ctx["settings"]
    profile = ctx["profile"]
    pid = profile["id"] if profile else 0
    kind = (ctx.get("query") or {}).get("kind", ["daily"])[0]
    if kind not in ("daily", "weekly"):
        kind = "daily"
    saved = store.list_reports(conn)
    saved_kind = [r for r in saved if r["kind"] == kind]
    latest = saved_kind[0] if saved_kind else (saved[0] if saved else None)
    hist = "".join("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                   % (r["id"], esc(r["kind"]), esc(r["language"]), esc(r["created_at"]))
                   for r in saved)
    # --- Presentation data: the same real rows the reports are built from ---
    store.seed_insights(conn=conn, profile_id=pid)
    rows = store.load_insight_rows(conn, profile_id=pid)
    queue = ctx["queue"]
    pending = queue.list_pending(profile_id=pid)
    cur = settings.get("ACCOUNT_CURRENCY") or "INR"
    sym = "₹" if cur == "INR" else (cur + " ")
    t_spend = sum(float(r.get("spend") or 0) for r in rows)
    t_enq = sum(int(r.get("enquiries") or 0) for r in rows)
    t_qual = sum(int(r.get("qualified_leads") or 0) for r in rows)
    t_cpq = (t_spend / t_qual) if t_qual else None
    camps = {}
    for r in rows:
        c = camps.setdefault(r.get("campaign_id") or "—",
                             {"leads": 0, "cost": 0.0})
        c["leads"] += int(r.get("qualified_leads") or 0)
        c["cost"] += float(r.get("spend") or 0)
    for c in camps.values():
        c["cpq"] = (c["cost"] / c["leads"]) if c["leads"] else None
    with_leads = {k: v for k, v in camps.items() if v["leads"]}
    ranked = sorted(with_leads.items(), key=lambda kv: kv[1]["cpq"])
    top3 = ranked[:3]
    bottom3 = list(reversed(ranked[-3:])) if ranked else []
    no_lead = sorted(((k, v) for k, v in camps.items() if not v["leads"]),
                     key=lambda kv: kv[1]["cost"], reverse=True)
    bottom3 = (bottom3 + no_lead)[:3]
    bottom_ids = {k for k, _v in bottom3}
    # Insights bullets — only from real data that exists.
    bullets = []
    if top3:
        k0, v0 = top3[0]
        bullets.append(("#10b981", "Top performing campaign: <strong>%s</strong> — "
                        "%d qualified leads at %s%s / CPL"
                        % (esc(k0), v0["leads"], sym, esc(round(v0["cpq"], 2)))))
    fatigue = next((p for p in pending if p["kind"] == "PROPOSE_CREATIVE_REFRESH"), None)
    first_prop = pending[0] if pending else None
    if first_prop is not None and first_prop is not fatigue:
        bullets.append(("#f59e0b", "Key issue: %s"
                        % esc((first_prop["payload"] or {}).get("what")
                              or first_prop["kind"])))
    if fatigue is not None:
        bullets.append(("#3b82f6", "Creative fatigue: %s"
                        % esc((fatigue["payload"] or {}).get("what")
                              or "A creative refresh is proposed")))
    bullets_html = "".join(
        '<div class="ins-row"><span class="mc-dot" style="background:%s"></span>'
        '<span>%s</span></div>' % (color, text) for color, text in bullets)

    def camp_list(items, color):
        out = []
        for i, (cid, cdata) in enumerate(items, 1):
            detail = ("%d leads · %s%s / CPL" % (cdata["leads"], sym,
                        esc(round(cdata["cpq"], 2)))) if cdata["leads"] else \
                     ("0 leads · %s%s spent" % (sym, esc(cdata["cost"])))
            out.append('<div class="tc-row"><span class="tc-num" '
                       'style="background:%s">%d</span><div><strong>%s</strong>'
                       '<div class="small mut">%s</div></div></div>'
                       % (color, i, esc(cid), detail))
        return "".join(out) or '<p class="mut small">No campaign data yet</p>'

    max_cost = max([c["cost"] for c in camps.values()] + [1])
    perf_rows = ""
    for cid, cdata in sorted(camps.items(), key=lambda kv: kv[1]["cost"],
                             reverse=True):
        pct = max(4, int(100 * cdata["cost"] / max_cost))
        bar = ("linear-gradient(90deg,#fca5a5,#fecaca)" if cid in bottom_ids
               else "linear-gradient(90deg,#7c3aed,#a78bfa)")
        perf_rows += ('<div class="perf-row"><div class="perf-name">%s</div>'
                      '<div class="perf-bar" style="width:%d%%;background:%s">'
                      '<span>%s%s</span></div>'
                      '<span class="pill info">%d Leads</span></div>'
                      % (esc(cid), pct, bar, sym, esc(cdata["cost"]),
                         cdata["leads"]))
    rec = None
    if pending:
        p0 = pending[0]
        rec = (p0["payload"] or {}).get("what") or p0["kind"]
        rec_why = (p0["payload"] or {}).get("why") or ""
    date_label = ("Latest %s report: %s" % (kind, latest["created_at"])) if latest \
        else "No report generated yet"
    export_link = ('<a class="btn" href="/reports?kind=%s">Export (view latest)</a>'
                   % kind) if latest else ""
    body = """
<style>
.rep-head{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap}
.toggle-pills{display:flex;gap:8px}
.toggle-pills a{padding:7px 16px;border-radius:999px;border:1px solid var(--line);
background:#fff;color:var(--mut);font-weight:600;font-size:13.5px}
.toggle-pills a.on{background:var(--brand);color:#fff;border-color:var(--brand)}
.toggle-pills a:hover{text-decoration:none}
.rep-grid{display:grid;grid-template-columns:1.6fr 1fr;gap:14px;align-items:start}
@media(max-width:960px){.rep-grid{grid-template-columns:1fr}}
.ins-row{display:flex;gap:10px;align-items:flex-start;padding:7px 0;font-size:14px}
.ins-row .mc-dot{margin-top:6px}
.tc-row{display:flex;gap:11px;align-items:center;padding:7px 0}
.tc-num{width:26px;height:26px;border-radius:50%%;color:#fff;font-weight:700;
display:flex;align-items:center;justify-content:center;flex:none;font-size:13px}
.tc-cols{display:grid;grid-template-columns:1fr 1fr;gap:8px 22px}
@media(max-width:640px){.tc-cols{grid-template-columns:1fr}}
.perf-row{display:flex;align-items:center;gap:10px;padding:7px 0}
.perf-name{width:130px;flex:none;font-size:13px;font-weight:600;
overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.perf-bar{height:26px;border-radius:8px;color:#fff;font-size:12.5px;font-weight:700;
display:flex;align-items:center;padding:0 10px;min-width:64px}
.rec-box{background:var(--violetbg);border-radius:12px;padding:13px 15px;font-size:14px}
</style>
<div class="rep-head"><div>
<h1 style="margin-bottom:2px">Reports</h1>
<p class="mut" style="margin:0">Performance summary and key insights</p>
<p class="small mut">Report language follows the LANGUAGES setting (English by default).
Numbers below come from the current data (MOCK dataset until Step 3).</p>
</div>
<div style="text-align:right">
<div class="toggle-pills">
<a href="/reports?kind=daily" class="%s">Daily Report</a>
<a href="/reports?kind=weekly" class="%s">Weekly Report</a>
</div>
<p class="small mut" style="margin:8px 0 6px">%s</p>%s
</div></div>
<div class="row" style="margin-bottom:6px">
<form method="post" action="/reports/generate" class="inline">%s
<input type="hidden" name="kind" value="daily"><button type="submit">Generate daily report</button></form>
<form method="post" action="/reports/generate" class="inline">%s
<input type="hidden" name="kind" value="weekly"><button class="secondary" type="submit">Generate weekly report</button></form>
</div>
<div class="grid">
 <div class="card"><div class="mut small">Total Spend</div><div class="kpi">%s%s</div></div>
 <div class="card"><div class="mut small">Enquiries</div><div class="kpi">%d</div></div>
 <div class="card"><div class="mut small">Qualified Leads</div><div class="kpi">%d</div></div>
 <div class="card"><div class="mut small">Cost per Qualified Lead</div><div class="kpi">%s</div></div>
</div>
<div class="rep-grid">
<div class="card"><h2>%s Insights</h2>
%s
<div class="tc-cols" style="margin-top:12px">
<div><h3 style="margin-top:0">Top 3 Campaigns</h3>%s</div>
<div><h3 style="margin-top:0">Bottom 3 Campaigns</h3>%s</div>
</div>
<details style="margin-top:12px"><summary>Full report text</summary>
%s</details>
</div>
<div>
<div class="card"><h2>Campaign Performance</h2>
<p class="small mut" style="margin-top:-6px">Spend vs Leads — latest report data</p>
%s</div>
<div class="rec-box"><strong>💡 Recommendation</strong><br>%s</div>
</div>
</div>
<div class="card"><h2>Saved reports</h2>
<table><tr><th>#</th><th>Kind</th><th>Language</th><th>When</th></tr>%s</table></div>
""" % ("on" if kind == "daily" else "", "on" if kind == "weekly" else "",
       esc(date_label), export_link,
       ctx["csrf_field"], ctx["csrf_field"],
       sym, esc(t_spend), t_enq, t_qual,
       ("%s%s" % (sym, esc(round(t_cpq, 2)))) if t_cpq is not None else "n/a",
       "Daily" if kind == "daily" else "Weekly",
       bullets_html or '<p class="mut small">No insights yet — run the optimiser or generate a report.</p>',
       camp_list(top3, "#10b981"), camp_list(bottom3, "#dc2626"),
       ('<pre>%s</pre>' % esc(latest["body"])) if latest else
       '<p class="mut small">No report saved yet</p>',
       perf_rows or '<p class="mut small">No campaign data yet</p>',
       (esc(rec) + (('<br><span class="small mut">%s</span>' % esc(rec_why)) if rec_why else ""))
       if rec else "No pending recommendations right now — proposals appear here after an optimisation run.",
       hist or '<tr><td colspan="4" class="mut">No reports saved yet</td></tr>')
    return page("Reports", "/reports", body, ctx["flash"], conn, ctx)


def pg_trends(ctx):
    from . import policies_register
    items = ""
    for t in trends_mod.TREND_ITEMS:
        pill = ('<span class="pill ok">VERIFIED</span>' if t["verified"]
                else '<span class="pill warn">UNVERIFIED</span>')
        items += ('<tr><td><a href="%s" target="_blank" rel="noopener">%s</a></td>'
                  '<td>%s</td><td>%s</td><td class="small">%s</td></tr>'
                  % (esc(t["url"]), esc(t["title"]), esc(t["date"]), pill, esc(t["note"])))
    review = trends_mod.knowledge_review()
    reg = ""
    for k in trends_mod.KNOWLEDGE_REGISTER:
        pill = ('<span class="pill ok">VERIFIED</span>' if k["verified"]
                else '<span class="pill warn">UNVERIFIED</span>')
        reg += ('<tr><td>%s</td><td>%s<div class="small mut">%s</div></td>'
                '<td class="small"><a href="%s" target="_blank" rel="noopener">source</a></td>'
                '<td>%s</td><td>%s</td><td class="small">%s</td></tr>'
                % (esc(k["id"]), esc(k["title"]), esc(k["area"]), esc(k["url"]),
                   esc(k["date_read"]), pill, esc(k["note"])))
    pol = ""
    for p in policies_register.POLICIES:
        status = p["status"]
        pill_cls = "bad" if status == "CONTESTED" else ("ok" if status == "OFFICIAL" else "warn")
        pol += ('<tr><td>%s</td><td>%s<div class="small mut">%s</div></td>'
                '<td>%s</td><td><span class="pill %s">%s</span></td>'
                '<td class="small"><a href="%s" target="_blank" rel="noopener">source</a>'
                ' · checked %s</td></tr>'
                % (esc(p["id"]), esc(p["title"]), esc(p["rule"][:400]),
                   esc(p["category"]), pill_cls, esc(status),
                   esc(p["source_url"]), esc(p["date_checked"])))
    pol_status = policies_register.register_status()
    body = """
<h1>Knowledge — Meta register, Policies register, Trend watch</h1>
<p class="mut">Every entry carries its source URL and date. UNVERIFIED means the
official page itself could not be fetched in this environment (403) — secondary
sources quoted Meta verbatim; do not quote externally without re-verifying in a
normal browser. The register never changes strategy on its own —
changes always happen via a proposal + the owner's decision.</p>
<div class="card"><h2>Meta Knowledge register — 2026 features/changes</h2>
<p class="small mut">%s</p>
<table><tr><th>ID</th><th>Feature / change</th><th>Source</th><th>Read</th><th>Status</th><th>Note</th></tr>%s</table></div>
<div class="card"><h2>Policies register — Meta Advertising Policies digest</h2>
<p class="small mut">%s The personal attributes rule enforces the UNION of both
official lists (the Transparency Center and Help Center lists do not match).
The 2026 Ad Terms (PR9) are DISPUTED — one tracker says the update was paused
on 5 Nov 2026 without a new date. This digest is not legal advice.</p>
<table><tr><th>ID</th><th>Rule</th><th>Category</th><th>Status</th><th>Source</th></tr>%s</table></div>
<div class="card"><h2>Trend watch — official sources</h2>
<table><tr><th>Item</th><th>Date</th><th>Status</th><th>Note</th></tr>%s</table></div>
<div class="card"><h2>PRACTICES note</h2>
<p class="small">Official guidance on objectives, structure, targeting/broad, placements,
the learning phase, budget changes and attribution is in PRACTICES.md (with the
repo) — verified against official docs in Step 2; the API is pinned at %s.
Even so, no number is used as a default — thresholds are owner settings.</p></div>
""" % (esc(review["note"]), reg, esc(pol_status["note"]), pol, items,
       esc(API_VERSION_LABEL))
    return page("Knowledge", "/trends", body, ctx["flash"], ctx["conn"], ctx)


def pg_audit(ctx):
    conn = ctx["conn"]
    audits = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 60").fetchall()
    errs = conn.execute("SELECT * FROM errors ORDER BY id DESC LIMIT 30").fetchall()
    writes = conn.execute("SELECT * FROM meta_writes ORDER BY id DESC LIMIT 30").fetchall()
    a_html = "".join("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                     % (r["id"], esc(r["event"]), esc(r["detail"]), esc(r["created_at"]))
                     for r in audits)
    e_html = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                     % (esc(r["source"]), esc(r["message"]), esc(r["created_at"]))
                     for r in errs)
    w_html = "".join("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                     % (r["id"], esc(r["mode"]), esc(r["status"]), esc(r["created_at"]))
                     for r in writes)
    body = """
<h1>Errors &amp; Audit Log</h1>
<p class="mut">Every proposal, approval and write is recorded here — secrets and
personal data are redacted before they reach the logs (email/phone/token patterns).</p>
<div class="card"><h2>Meta writes</h2>
<table><tr><th>#</th><th>Mode</th><th>Status</th><th>When</th></tr>%s</table>
<p class="small mut">Rollback: rolling back any write happens only after reading the
fresh state, showing the diff and taking the owner's separate approval — via the
CLI/library (<code>app.rollback</code>), never automatically. Rollback does not
refund spend.</p></div>
<div class="card"><h2>Errors</h2>
<table><tr><th>Source</th><th>Message (redacted)</th><th>When</th></tr>%s</table></div>
<div class="card"><h2>Audit log (latest 60)</h2>
<table><tr><th>#</th><th>Event</th><th>Detail (redacted)</th><th>When</th></tr>%s</table></div>
""" % (w_html or '<tr><td colspan="4" class="mut">No writes yet</td></tr>',
       e_html or '<tr><td colspan="3" class="mut">No errors recorded</td></tr>',
       a_html)
    return page("Errors & Audit", "/audit", body, ctx["flash"], conn, ctx)


# ---------------------------------------------------------------- POST actions
def _redirect(handler, path, msg=None):
    if msg:
        path = path + "?msg=" + urllib.parse.quote(msg)
    handler.send_response(303)
    handler.send_header("Location", path)
    handler.end_headers()


def post_login(ctx, form):
    if auth.check_login(form.get("password", ""), ctx["conn"]):
        token, _csrf = auth.create_session(ctx["conn"])
        audit(ctx["conn"], "owner_login", "Owner logged in (password not logged).")
        ctx["set_cookie"] = token
        return "/"
    log_error(ctx["conn"], "auth", "Login failed — wrong password (value not logged).")
    return "/login?msg=" + urllib.parse.quote("Wrong password — please try again.")


def post_setup(ctx, form):
    conn = ctx["conn"]
    if auth.owner_exists(conn):
        return "/login?msg=" + urllib.parse.quote("The owner is already set — setup is closed.")
    try:
        auth.create_owner(form.get("password", ""), conn)
    except ValueError as e:
        return "/setup?msg=" + urllib.parse.quote(str(e))
    token, _csrf = auth.create_session(conn)
    ctx["set_cookie"] = token
    return "/?msg=" + urllib.parse.quote("Owner is set. The dashboard is ready.")


def post_settings(ctx, form):
    # Settings page edits the GLOBAL settings file. Per-profile overrides
    # live on the profile (Profiles page) and win at read time — they are
    # never baked into the global file by a save here.
    settings = load_settings()
    for key, kind, _h in SETTING_FIELDS:
        if kind == "checkbox":
            settings[key] = key in form
        elif kind == "number":
            raw = (form.get(key) or "").strip()
            try:
                settings[key] = float(raw) if raw else 0
                if settings[key] == int(settings[key]):
                    settings[key] = int(settings[key])
            except ValueError:
                settings[key] = 0
        elif key == "AUTOMATION_MODE":
            val = form.get(key, "PROPOSE")
            settings[key] = val if val in ("OFF", "PROPOSE", "AUTO_WITHIN_RULES") else "PROPOSE"
        else:
            settings[key] = (form.get(key) or "").strip()
    save_settings(settings)
    audit(ctx["conn"], "settings_saved", "Settings updated by owner (values not logged).")
    return "Settings saved."


def post_killswitch(ctx, form):
    queue = ctx["queue"]
    if form.get("action") == "on":
        from .mock_meta import MockMetaClient
        queue.engage_kill_switch("owner pressed kill switch in UI", mock_client=MockMetaClient())
        return "Kill switch ON — automation stopped, execution blocked. It will never auto-resume."
    queue.conn.execute("INSERT OR REPLACE INTO kv (key, value) VALUES ('kill_switch', '0')")
    queue.conn.commit()
    audit(ctx["conn"], "kill_switch_released", "Owner released the kill switch manually.")
    return "Kill switch OFF — released by the owner. AUTOMATION_MODE stays whatever Settings says."


def _offering_name(ctx, offering_id):
    for o in profiles_mod.list_offerings(ctx["profile"]["id"], ctx["conn"]):
        if o["id"] == offering_id:
            return o["name"]
    return "#%s" % offering_id


def post_eligibility_confirm(ctx, form):
    if not ctx["profile"]:
        return "Refused: there is no active profile."
    offering_id = int(form.get("offering_id", "0") or 0)
    proof = (form.get("proof_note") or "").strip()
    tdate = (form.get("terms_checked_date") or "").strip()
    if not proof or not tdate:
        return "Refused: both a proof note and a terms-checked date are required — without them it cannot be confirmed."
    profiles_mod.update_offering(offering_id, {
        "supplier": (form.get("supplier") or "").strip(),
        "proof_note": proof, "terms_checked_date": tdate,
        "permission_confirmed": True}, ctx["conn"])
    audit(ctx["conn"], "eligibility_confirmed",
          "offering_id=%s profile=%s (proof recorded)"
          % (offering_id, ctx["profile"]["slug"]))
    return "Permission confirmed for %s (with proof + date)." % _offering_name(ctx, offering_id)


def post_eligibility_unconfirm(ctx, form):
    offering_id = int(form.get("offering_id", "0") or 0)
    profiles_mod.update_offering(offering_id, {"permission_confirmed": False},
                                 ctx["conn"])
    audit(ctx["conn"], "eligibility_unconfirmed", "offering_id=%s" % offering_id)
    return "%s is unconfirmed — its ads are blocked again." % _offering_name(ctx, offering_id)


def post_eligibility_add(ctx, form):
    if not ctx["profile"]:
        return "Refused: there is no active profile."
    try:
        oid = profiles_mod.add_offering(ctx["profile"]["id"], {
            "name": form.get("name", ""), "type": form.get("type", "product"),
            "category": form.get("category", ""), "price": form.get("price", ""),
            "supplier": form.get("supplier", ""),
            "destination_override": form.get("destination_override", ""),
        }, ctx["conn"])
    except ValueError as e:
        return "Refused: %s" % e
    audit(ctx["conn"], "offering_added", "offering_id=%s profile=%s"
          % (oid, ctx["profile"]["slug"]))
    return "Offering added (UNCONFIRMED — confirm its permission first)."


def post_eligibility_delete(ctx, form):
    if not form.get("confirm_delete"):
        return "Refused: tick the confirm checkbox to delete."
    offering_id = int(form.get("offering_id", "0") or 0)
    name = _offering_name(ctx, offering_id)
    profiles_mod.delete_offering(offering_id, ctx["conn"])
    audit(ctx["conn"], "offering_deleted", "offering_id=%s" % offering_id)
    return "%s was removed from the catalog." % name


def post_creative_generate(ctx, form):
    conn = ctx["conn"]
    result = creative_mod.generate_creative_set(
        form.get("product", ""), form.get("segment", "students"),
        settings=ctx["settings"], eligibility=ctx["eligibility"],
        extra_patterns=ctx["extra_patterns"], profile=ctx["profile"])
    cid = store.save_creative(result["product"], result["segment"], "creative_set",
                              result, result["policy"], conn,
                              profile_id=ctx["profile"]["id"] if ctx["profile"] else 0)
    from .common import log_role_run
    log_role_run(conn, "06_angle_generator", "done", {"angles_for": result["segment"]})
    log_role_run(conn, "07_copywriter", "done", result["copy"])
    log_role_run(conn, "10_policy_checker", "done", result["policy"])
    if result["policy"]["allowed"]:
        return "Creative set #%d saved and policy PASS. You can send it for approval from the Planner." % cid
    return ("Creative set #%d saved but policy BLOCKED: %s"
            % (cid, "; ".join(result["policy"]["reasons"])))


def post_policycheck(ctx, form):
    result = policy_checker.check_claims(form.get("text", ""))
    if result["allowed"]:
        return "Policy check: no banned claim found. (Only claims were scanned — eligibility/destination are separate gates.)"
    return "Policy check BLOCKED: " + "; ".join(result["reasons"])


def post_upload(ctx, form):
    conn = ctx["conn"]
    adapter = creative_mod.ManualUploadAdapter()
    info = adapter.describe_upload(form.get("filename", ""), form.get("kind", "image"))
    conn.execute(
        "INSERT INTO assets (filename, kind, checklist, visual_check, created_at) "
        "VALUES (?, ?, ?, 'PENDING', datetime('now'))",
        (info["filename"], info["kind"], json.dumps(info["checklist"])))
    conn.commit()
    audit(conn, "asset_registered", "file=%s kind=%s (manual upload, visual check PENDING)"
          % (info["filename"], info["kind"]))
    return "Asset registered — visual check is PENDING; until then it cannot enter the approval queue."


def post_visualcheck(ctx, form):
    conn = ctx["conn"]
    if not all(form.get(k) for k in ("c1", "c2", "c3", "c4")):
        return "Refused: all 4 visual checklist items must be ticked."
    cur = conn.execute(
        "UPDATE assets SET visual_check = 'PASS' WHERE filename = ?",
        (form.get("filename", ""),))
    conn.commit()
    if cur.rowcount == 0:
        return "No asset is registered under this name — register it first."
    audit(conn, "asset_visual_check_pass", "file=%s" % form.get("filename", ""))
    return "Visual check marked PASS."


PROVIDER_FORM_FIELDS = {
    "text": ("provider_name", "model", "base_url", "auth_style", "auth_header",
             "auth_prefix", "extra_headers", "test_path", "payload_format",
             "chat_path"),
    "image": ("provider_name", "model", "base_url", "auth_style", "auth_header",
              "auth_prefix", "extra_headers", "test_path", "payload_format",
              "image_path", "prompt_field", "model_field", "size_field", "size",
              "response_url_path", "response_b64_path"),
    "video": ("provider_name", "model", "base_url", "auth_style", "auth_header",
              "auth_prefix", "extra_headers", "test_path", "payload_format",
              "submit_path", "poll_path", "prompt_field", "model_field",
              "image_field", "duration_field", "aspect_field", "job_id_path",
              "status_path", "done_values", "fail_values", "result_url_path",
              "poll_interval_sec", "max_wait_sec"),
}


def post_providers_save(ctx, form):
    cap = form.get("capability", "")
    if cap not in providers.CAPABILITIES:
        return "Refused: unknown capability."
    fields = {"preset": form.get("preset") or providers.DEFAULT_PRESET[cap]}
    for key in PROVIDER_FORM_FIELDS[cap]:
        fields[key] = form.get(key, "")
    try:
        cfg = providers.save_connection(cap, fields, api_key=form.get("api_key", ""))
    except ValueError as e:
        return "Refused: %s" % e
    audit(ctx["conn"], "provider_saved",
          "capability=%s preset=%s provider=%s base=%s model=%s (key value never logged)"
          % (cap, cfg["preset"], cfg.get("provider_name") or "-", cfg.get("base_url"),
             cfg.get("model")))
    status = providers.connection_status(cap)
    return ("%s connection saved. Key: %s. Base URL: %s · Model: %s"
            % (cap, "is set" if status["key_set"] else "is NOT set",
               cfg.get("base_url") or "—", cfg.get("model") or "—"))


def post_providers_preset(ctx, form):
    cap = form.get("capability", "")
    if cap not in providers.CAPABILITIES:
        return "Refused: unknown capability."
    try:
        cfg = providers.apply_preset(cap, form.get("preset", ""))
    except ValueError as e:
        return "Refused: %s" % e
    audit(ctx["conn"], "provider_preset_applied",
          "capability=%s preset=%s" % (cap, cfg["preset"]))
    return ("%s: preset '%s' applied — base URL %s, model %s pre-filled. "
            "Now just paste the API key and save."
            % (cap, cfg["preset"], cfg.get("base_url") or "—", cfg.get("model") or "—"))


def post_providers_test(ctx, form):
    cap = form.get("capability", "")
    if cap not in providers.CAPABILITIES:
        return "Refused: unknown capability."
    result = providers.test_connection(cap)
    ctx["conn"].execute(
        "INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
        ("provider_test_" + cap, json.dumps(result)))
    ctx["conn"].commit()
    audit(ctx["conn"], "provider_test",
          "capability=%s ok=%s status=%s" % (cap, result["ok"], result["status"]))
    return "Test connection (%s): %s" % (cap, result["detail"])


def post_providers_removekey(ctx, form):
    cap = form.get("capability", "")
    if cap not in providers.CAPABILITIES:
        return "Refused: unknown capability."
    providers.remove_api_key(cap)
    audit(ctx["conn"], "provider_key_removed", "capability=%s" % cap)
    return "The %s API key was removed from the secrets file." % cap


def post_api_copy(ctx, form):
    conn = ctx["conn"]
    try:
        result = creative_mod.generate_copy_with_api(
            form.get("product", ""), form.get("segment", "students"),
            settings=ctx["settings"], instruction=form.get("instruction", ""),
            eligibility=ctx["eligibility"],
            extra_patterns=ctx["extra_patterns"], profile=ctx["profile"])
    except providers.ProviderError as e:
        log_error(conn, "providers:text", str(e))
        return "Text API error: %s" % e
    kind = "api_copy" if result.get("source") == "api" else "creative_set"
    cid = store.save_creative(result["product"], result["segment"], kind,
                              result, result["policy"], conn,
                              profile_id=ctx["profile"]["id"] if ctx["profile"] else 0)
    audit(conn, "creative_generated",
          "id=%s source=%s provider=%s model=%s request=%s cost=%s"
          % (cid, result.get("source"), result.get("provider", "-"),
             result.get("model", "-"), result.get("request_id", "-"),
             providers.COST_NOTE))
    if result.get("source") != "api":
        return ("Creative set #%d created from TEMPLATES — %s. Policy: %s"
                % (cid, result["label"],
                   "PASS" if result["policy"]["allowed"]
                   else "BLOCKED — " + "; ".join(result["policy"]["reasons"])))
    if result["policy"]["allowed"]:
        return ("API copy #%d created (%s, %s) and policy PASS. Cost: %s"
                % (cid, result.get("provider"), result.get("model"), providers.COST_NOTE))
    return ("API copy #%d created but policy BLOCKED: %s"
            % (cid, "; ".join(result["policy"]["reasons"])))


def _register_generated(ctx, meta, kind, prompt, source):
    store.register_asset(meta["filename"], kind, source=source,
                         provider=meta["provider"], model=meta["model"],
                         prompt=prompt, cost_note=providers.COST_NOTE,
                         remote_url=meta.get("remote_url"), conn=ctx["conn"])
    audit(ctx["conn"], "asset_generated",
          "file=%s kind=%s provider=%s model=%s request=%s cost=%s (visual check PENDING)"
          % (meta["filename"], kind, meta["provider"], meta["model"],
             meta["request_id"], providers.COST_NOTE))
    return ("Asset %s created (%s, %s) — visual check is PENDING; it will not enter "
            "the approval queue until the checklist PASSes. Cost: %s"
            % (meta["filename"], meta["provider"], meta["model"], providers.COST_NOTE))


def post_api_image(ctx, form):
    prompt = (form.get("prompt") or "").strip()
    if not prompt:
        return "Refused: the image prompt is empty."
    if not providers.is_configured("image"):
        return "API not connected — connect the Image API from the API Providers page first."
    try:
        meta = creative_mod.generate_poster_image(prompt)
    except providers.ProviderError as e:
        log_error(ctx["conn"], "providers:image", str(e))
        return "Image API error: %s" % e
    return _register_generated(ctx, meta, "image", prompt, "api-image")


def post_api_carousel(ctx, form):
    slides = [s.strip() for s in (form.get("slides") or "").splitlines() if s.strip()]
    if not slides:
        return "Refused: write at least one slide brief."
    if not providers.is_configured("image"):
        return "API not connected — connect the Image API from the API Providers page first."
    try:
        metas = creative_mod.generate_carousel_images(slides)
    except providers.ProviderError as e:
        log_error(ctx["conn"], "providers:image", str(e))
        return "Image API error: %s" % e
    msgs = []
    for i, meta in enumerate(metas, 1):
        msgs.append(_register_generated(ctx, meta, "image", slides[i - 1],
                                        "api-carousel slide %d" % i))
    return "%d carousel slides created. " % len(metas) + " | ".join(msgs)


def post_api_video(ctx, form):
    prompt = (form.get("prompt") or "").strip()
    if not prompt:
        return "Refused: the video prompt is empty."
    if not providers.is_configured("video"):
        return "API not connected — connect the Video API from the API Providers page first."
    try:
        out = creative_mod.submit_reel_video(
            prompt, image_url=(form.get("image_url") or "").strip() or None,
            duration=(form.get("duration") or "").strip() or None,
            aspect=(form.get("aspect") or "").strip() or None)
    except providers.ProviderError as e:
        log_error(ctx["conn"], "providers:video", str(e))
        return "Video API error: %s" % e
    from .common import _now
    store.add_video_job({
        "job_id": out["job_id"], "provider": out["provider"],
        "model": out["model"], "prompt": prompt, "status": "submitted",
        "created_at": _now(), "request_id": out["request_id"],
    }, ctx["conn"])
    return ("Video job submitted — job id %s (%s, %s). Poll it from the Video jobs "
            "table below with 'Check status'. Cost: %s"
            % (out["job_id"], out["provider"], out["model"], providers.COST_NOTE))


def post_api_video_check(ctx, form):
    conn = ctx["conn"]
    job_id = form.get("job_id", "")
    job = next((j for j in store.list_video_jobs(conn)
                if str(j.get("job_id")) == str(job_id)), None)
    if job is None:
        return "There is no video job record with this id."
    if job.get("status") == "done":
        return "This job is already done — the asset is registered."
    try:
        out = creative_mod.poll_reel_video(job_id)
    except providers.ProviderError as e:
        log_error(conn, "providers:video", str(e))
        return "Video API error: %s" % e
    if out["state"] == "pending":
        store.update_video_job(job_id, {"status": "pending: %s" % out["raw_status"]}, conn)
        return "Job %s is still processing (status: %s). Check again in a little while." \
            % (job_id, out["raw_status"])
    if out["state"] == "failed":
        store.update_video_job(job_id, {"status": "failed"}, conn)
        audit(conn, "video_job_failed", "job=%s" % job_id)
        return "Job %s FAILED at the provider. Change the prompt and try again." % job_id
    # done
    meta = {"filename": None, "provider": job.get("provider"),
            "model": job.get("model"), "request_id": out["request_id"],
            "remote_url": out["result_url"]}
    if out["result_url"]:
        try:
            filename, _ext = providers.fetch_result_file(out["result_url"])
            meta["filename"] = filename
        except providers.ProviderError:
            meta["filename"] = "(remote only) %s" % job_id
    else:
        meta["filename"] = "(no result url) %s" % job_id
    store.update_video_job(job_id, {"status": "done"}, conn)
    return _register_generated(ctx, meta, "video", job.get("prompt", ""), "api-video")


def post_planner_plan(ctx, form):
    conn = ctx["conn"]
    product = form.get("product", "")
    segment = form.get("segment", "students")
    profile = ctx["profile"]
    pid = profile["id"] if profile else 0
    plan = planner_mod.plan_structure(
        product, segment, form.get("audience_type", "customers"),
        form.get("format", "REEL"), 1, form.get("daily_budget", ""),
        profile=profile)
    creative = creative_mod.generate_creative_set(
        product, segment, settings=ctx["settings"],
        eligibility=ctx["eligibility"], extra_patterns=ctx["extra_patterns"],
        profile=profile)
    draft = {
        "kind": "CAMPAIGN_DRAFT",
        "product": product,
        "profile_id": pid,
        "business": profile["name"] if profile else "",
        "campaign_name": plan["campaign_name"],
        "adset_name": plan["ad_sets"][0]["name"],
        "ad_name": plan["ad_sets"][0]["ads"][0]["ad_name"],
        "creative_text": creative["copy"]["hinglish"]["headline"] + " "
                         + creative["copy"]["hinglish"]["text"],
        "daily_budget": form.get("daily_budget", ""),
        "plan": plan,
        "policy_preview": creative["policy"],
        "cost_effect": "When created, the objects stay PAUSED — spend starts only "
                       "when activation gets a SEPARATE approval (this build has "
                       "no automatic path to activation).",
    }
    # Guardrail pre-flight: BLOCK = queue me entry NAHI; WARN = warnings
    # draft ke saath attach hokar jaate hain (draft par visible).
    offering = next((o for o in profiles_mod.list_offerings(pid, conn)
                     if o["name"] == product), None) if pid else None
    dest_url = (offering or {}).get("destination_override") \
        or ctx["settings"].get("DESTINATION_URL", "")
    preflight = guardrails_mod.run_preflight({
        "kind": "draft", "product": product,
        "text": draft["creative_text"],
        "settings": ctx["settings"], "eligibility": ctx["eligibility"],
        "extra_patterns": ctx["extra_patterns"], "plan": plan,
        "daily_budget": form.get("daily_budget", ""),
        "format": form.get("format", "REEL"),
        "profile": profile,
        "objective": plan.get("objective", ""),
        "destination_url": dest_url,
        "destination_ready": bool(dest_url) and (
            bool((offering or {}).get("destination_override"))
            or ctx["settings"].get("DESTINATION_READY") is True),
        "kill_switch": ctx["queue"].kill_switch_active(),
    }, conn=conn)
    if not preflight["allowed"]:
        reasons = "; ".join(b["reason"] for b in preflight["blocks"])
        from .common import log_role_run
        log_role_run(conn, "guardrail_preflight", "blocked", preflight)
        return ("⛔ Guardrail pre-flight STOPPED the draft — it did NOT go to the "
                "approval queue. Reason: %s" % reasons)
    if preflight["warnings"]:
        draft["guardrail_warnings"] = [
            {"id": w["id"], "name": w["name"], "reason": w["reason"]}
            for w in preflight["warnings"]]
    item_id = ctx["queue"].add_item("CAMPAIGN_DRAFT", draft, profile_id=pid)
    from .common import log_role_run
    log_role_run(conn, "11_structure_planner", "done", plan)
    warn_note = ""
    if preflight["warnings"]:
        warn_note = " Guardrail warnings attached: %s" % "; ".join(
            w["name"] for w in preflight["warnings"])
    return ("Plan created and CAMPAIGN_DRAFT #%d went to the approval queue. "
            "Policy preview: %s.%s" % (item_id, "PASS" if creative["policy"]["allowed"]
                                    else "BLOCKED — " + "; ".join(creative["policy"]["reasons"]),
                                    warn_note))


def post_approval_action(ctx, form, action):
    queue = ctx["queue"]
    item_id = int(form.get("id", "0"))
    if action == "approve":
        if queue.kill_switch_active():
            return "The kill switch is ON — approvals are blocked."
        queue.approve(item_id)
        return "Item #%d APPROVED. Execute is a separate step (from the History table) — activation is never automatic." % item_id
    if action == "reject":
        queue.reject(item_id)
        return "Item #%d REJECTED." % item_id
    if action == "edit":
        try:
            payload = json.loads(form.get("payload", "{}"))
        except ValueError:
            return "Edit refused: the payload is not valid JSON."
        queue.edit_item(item_id, payload)
        return "Item #%d draft edit saved." % item_id
    if action == "execute":
        result = execute_approved_item(item_id, ctx["settings"], conn=ctx["conn"], queue=queue)
        if result.get("ok"):
            return "Executed (%s): %s" % (result.get("mode"), result.get("note"))
        return "Execute BLOCKED: %s %s" % (result.get("blocked", ""),
                                           "; ".join(result.get("reasons", [])))
    return "Unknown action."


def post_budget_dataset(ctx, form):
    n = store.replace_insights(form.get("dataset", "one_big_winner"), ctx["conn"])
    return "MOCK dataset changed — %d rows are now active." % n


def post_budget_optimise(ctx, form):
    from . import jobs
    rc = jobs.cmd_optimise(None)
    return "Optimiser ran (rc=%s). See the proposals in the approval queue." % rc


def post_leads_add(ctx, form):
    try:
        store.add_lead(form.get("ad_ref", ""), form.get("status", "enquiry"),
                       int(form.get("count", "1")), ctx["conn"])
    except ValueError as e:
        return "Refused: %s" % e
    return "Lead count added (count/status only — no personal data was stored)."


def post_reports_generate(ctx, form):
    from . import jobs
    kind = form.get("kind", "daily")
    jobs._report(None, kind)
    return "%s report generated and saved." % kind.capitalize()


def post_roles_run(ctx, form):
    conn = ctx["conn"]
    from .common import log_role_run
    settings = ctx["settings"]
    profile = ctx["profile"]
    pid = profile["id"] if profile else None
    rows = store.load_insight_rows(conn, profile_id=pid) \
        or store.seed_insights(profile_id=pid, conn=conn) \
        and store.load_insight_rows(conn, profile_id=pid)
    ran = []

    def run(result):
        log_role_run(conn, result["role"], "done", result["output"])
        ran.append(result["role"])

    run(roles.role_01_audience_research(profile=profile))
    run(roles.role_02_competitor_watch(
        profile["slug"] if profile else "software-hub", conn=conn, profile_id=pid))
    run(roles.role_03_trend_analysis())
    run(roles.role_04_funnel_strategy(profile=profile))
    run(roles.role_05_budget_planning(settings))
    angles = roles.role_06_angle_generator("students", profile=profile)["output"]["angles"]
    run(roles.role_06_angle_generator("students", profile=profile))
    run(roles.role_07_copywriter(angles[0], profile=profile))
    run(roles.role_08_visual_poster_brief(angles[0], profile=profile))
    run(roles.role_09_reel_script(angles[0]))
    run(roles.role_11_structure_planner())
    run(roles.role_12_targeting_planner())
    run(roles.role_15_account_health_monitor())
    run(roles.role_16_data_collector())
    run(roles.role_17_lead_quality_tracker(rows))
    run(roles.role_18_creative_analyst(rows))
    run(roles.role_20_reporter(rows, [], (settings.get("LANGUAGES") or ["English"])[0],
                               business_name=profile["name"] if profile else None,
                               industry=profile["industry"] if profile else None))
    audit(conn, "roles_manual_run", "roles=%s" % ",".join(ran))
    return "%d roles ran on MOCK data — outputs are logged in role_runs." % len(ran)


# ------------------------------------------------------- Business Profiles
_PROFILE_FIELDS = ("name", "industry", "description", "website",
                   "target_type", "target_text", "geography", "languages",
                   "currency", "sales_model")
_OVERRIDE_FIELDS = ("TOTAL_DAILY_BUDGET_CAP", "PER_CAMPAIGN_CAP",
                    "TARGET_COST_PER_QUALIFIED_LEAD", "MAX_BUDGET_CHANGE_PCT",
                    "DESTINATION_URL", "TOP_CREATIVE_WINDOW_DAYS")


def pg_profiles(ctx):
    conn = ctx["conn"]
    profiles = profiles_mod.list_profiles(conn)
    active = ctx["profile"]
    rows = ""
    for p in profiles:
        n_off = len(profiles_mod.list_offerings(p["id"], conn))
        is_active = active and p["id"] == active["id"]
        rows += ("<tr><td>%s <strong>%s</strong></td><td>%s</td><td>%s</td>"
                 "<td>%s</td><td>%d</td><td class='small'>"
                 "<form method='post' action='/profiles/switch' class='inline'>%s"
                 "<input type='hidden' name='profile_id' value='%d'>"
                 "<button class='secondary' type='submit'>Make active</button></form> "
                 "<form method='post' action='/profiles/duplicate' class='inline'>%s"
                 "<input type='hidden' name='profile_id' value='%d'>"
                 "<button class='secondary' type='submit'>Duplicate</button></form> "
                 "<form method='post' action='/profiles/delete' class='inline'>%s"
                 "<input type='hidden' name='profile_id' value='%d'>"
                 "<label class='small'><input type='checkbox' name='confirm_delete' value='yes'> confirm</label> "
                 "<button class='danger' type='submit'>Delete</button></form>"
                 "</td></tr>"
                 % ("★" if is_active else "", esc(p["name"]), esc(p["industry"]),
                    esc(industries_mod.get_preset(p["industry_preset"])["label"]),
                    esc(p["sales_model"]), n_off,
                    ctx["csrf_field"], p["id"], ctx["csrf_field"], p["id"],
                    ctx["csrf_field"], p["id"]))
    preset_options = "".join(
        "<option value='%s'>%s</option>" % (k, esc(industries_mod.get_preset(k)["label"]))
        for k in industries_mod.PRESET_ORDER)
    model_options = "".join("<option>%s</option>" % m for m in industries_mod.SALES_MODELS)
    target_options = "".join("<option>%s</option>" % t for t in industries_mod.TARGET_TYPES)
    proof = ""
    sh = next((p for p in profiles if p["slug"] == "software-hub"), None)
    if sh:
        mp = profiles_mod.migration_proof(conn, sh["id"])
        proof = ("<div class='card'><h2>Software Hub migration proof</h2>"
                 "<p class='small'>PRODUCT_ELIGIBILITY.yaml to DB catalog: "
                 "source %d · stored %d · names match: %s · all flags "
                 "unconfirmed: %s · <strong>lossless: %s</strong>%s</p></div>"
                 % (mp["source_count"], mp["stored_count"], mp["names_match"],
                    mp["all_unconfirmed"], mp["lossless"],
                    (" · mismatches: " + esc("; ".join(mp["mismatches"]))) if mp["mismatches"] else ""))
    edit = ""
    if active:
        ov = active.get("settings_overrides") or {}
        ov_inputs = "".join(
            "<label>%s (profile override)</label><input name='ov_%s' value='%s'>"
            % (k, k, esc(ov.get(k, ""))) for k in _OVERRIDE_FIELDS)
        edit = """<div class="card"><h2>Edit the active profile — %s</h2>
<form method="post" action="/profiles/update">%s
<input type="hidden" name="profile_id" value="%d">
<label>Business name</label><input name="name" value="%s">
<label>Industry (text)</label><input name="industry" value="%s">
<label>Description</label><textarea name="description" rows="2">%s</textarea>
<label>Website / destination</label><input name="website" value="%s">
<label>Target type</label><select name="target_type">%s</select>
<label>Target customers (text)</label><input name="target_text" value="%s">
<label>Geography</label><input name="geography" value="%s">
<label>Languages</label><input name="languages" value="%s">
<label>Currency</label><input name="currency" value="%s">
<label>Sales model</label><select name="sales_model">%s</select>
%s
<label><input type="checkbox" name="ov_DESTINATION_READY" value="1" %s> DESTINATION_READY (override) — the landing page is live and ready</label>
<label>Automation mode (override)</label><select name="ov_AUTOMATION_MODE">
<option value="">(use the global setting)</option>
<option %s>PROPOSE</option><option %s>AUTO_WITHIN_RULES</option></select>
<p class="small mut">Leave an override empty to use the global setting. The per-profile
catalog is on the Eligibility page, and the compliance pack shows there too.</p>
<button type="submit">Save profile</button></form></div>""" % (
            esc(active["name"]), ctx["csrf_field"], active["id"],
            esc(active["name"]), esc(active["industry"]),
            esc(active["description"]), esc(active["website"]),
            "".join("<option %s>%s</option>" % ("selected" if t == active["target_type"] else "", t)
                    for t in industries_mod.TARGET_TYPES),
            esc(active["target_text"]), esc(active["geography"]),
            esc(active["languages"]), esc(active["currency"]),
            "".join("<option %s>%s</option>" % ("selected" if m == active["sales_model"] else "", m)
                    for m in industries_mod.SALES_MODELS),
            ov_inputs,
            "checked" if ov.get("DESTINATION_READY") is True else "",
            "selected" if ov.get("AUTOMATION_MODE") == "PROPOSE" else "",
            "selected" if ov.get("AUTOMATION_MODE") == "AUTO_WITHIN_RULES" else "")
    body = """<h1>Business Profiles</h1>
<p class="mut">Every business has its own profile — its own catalog, competitors and
settings. You can also switch from the sidebar. Presets are editable starting
points, not legal advice.</p>
<div class="card"><table><tr><th></th><th>Business</th><th>Industry</th><th>Preset</th>
<th>Sales model</th><th>Offerings</th><th>Actions</th></tr>%s</table></div>
%s
<div class="card"><h2>Create a new profile</h2>
<form method="post" action="/profiles/create">%s
<label>Business name</label><input name="name" required>
<label>Industry preset (seeds funnel/KPI defaults + the compliance pack)</label>
<select name="industry_preset">%s</select>
<label>Industry (free text — if different from the preset label)</label><input name="industry">
<label>Description</label><textarea name="description" rows="2"></textarea>
<label>Website / destination URL</label><input name="website" placeholder="https://">
<label>Target type</label><select name="target_type">%s</select>
<label>Target customers (text)</label><input name="target_text">
<label>Geography</label><input name="geography">
<label>Languages</label><input name="languages">
<label>Currency</label><input name="currency" placeholder="INR">
<label>Sales model</label><select name="sales_model">%s</select>
<button type="submit">Create profile</button></form></div>
%s""" % (rows, proof, ctx["csrf_field"], preset_options, target_options,
         model_options, edit)
    return page("Profiles", "/profiles", body, ctx["flash"], conn, ctx)


def post_profiles_switch(ctx, form):
    profile = profiles_mod.set_active_profile(int(form.get("profile_id") or 0),
                                              ctx["conn"])
    return "Active profile is now: %s (%s)" % (profile["name"], profile["industry"])


def post_profiles_create(ctx, form):
    data = {k: form.get(k, "") for k in _PROFILE_FIELDS}
    data["industry_preset"] = form.get("industry_preset", "generic")
    profile = profiles_mod.create_profile(data, ctx["conn"])
    return ("Profile '%s' created (preset: %s). Add the catalog on the Eligibility "
            "page — a new offering always stays UNCONFIRMED."
            % (profile["name"], profile["industry_preset"]))


def post_profiles_update(ctx, form):
    conn = ctx["conn"]
    pid = int(form.get("profile_id") or 0)
    data = {k: form.get(k, "") for k in _PROFILE_FIELDS if k in form}
    overrides = {}
    for key in _OVERRIDE_FIELDS:
        val = (form.get("ov_" + key) or "").strip()
        if val:
            try:
                overrides[key] = float(val) if val.replace(".", "", 1).isdigit() else val
            except ValueError:
                overrides[key] = val
    overrides["DESTINATION_READY"] = form.get("ov_DESTINATION_READY") == "1"
    mode = form.get("ov_AUTOMATION_MODE") or ""
    if mode:
        overrides["AUTOMATION_MODE"] = mode
    data["settings_overrides"] = overrides
    profile = profiles_mod.update_profile(pid, data, conn)
    return "Profile '%s' updated (overrides apply to this profile only)." % profile["name"]


def post_profiles_duplicate(ctx, form):
    clone = profiles_mod.duplicate_profile(int(form.get("profile_id") or 0),
                                           ctx["conn"])
    return "Duplicate profile created: %s (catalog + competitors copied)." % clone["name"]


def post_profiles_delete(ctx, form):
    if form.get("confirm_delete") != "yes":
        return "NOT deleted — ticking the confirm checkbox is required."
    profiles_mod.delete_profile(int(form.get("profile_id") or 0), ctx["conn"])
    return "Profile deleted. Its catalog/competitor rows are gone too."


# ------------------------------------------------------------ Growth Loop
# Growth Loop stage cards: (stage key, short label, icon) in loop order.
GL_STAGE_CARDS = [
    ("competitor_discovery", "Competitor Discovery", "&#128269;"),
    ("competitor_ads_research", "Best Ads Research", "&#129513;"),
    ("top_creative_inspiration", "Inspiration Brief", "&#128196;"),
    ("creative_production", "Creative Production", "&#128444;"),
    ("optimisation_plan", "Optimisation Plan", "&#128640;"),
    ("go_live", "Go Live (Approval)", "&#9654;"),
    ("monitoring", "Winners vs Losers", "&#128200;"),
    ("refresh", "Refresh Creatives", "&#128260;"),
]


def pg_loop(ctx):
    from datetime import datetime, timezone
    conn = ctx["conn"]
    profile = ctx["profile"]
    pid = profile["id"] if profile else 0
    now = datetime.now(timezone.utc)
    status = loop_mod.loop_status(conn, pid)
    window = 10 if str(ctx["settings"].get("TOP_CREATIVE_WINDOW_DAYS")) == "10" else 7
    brief = loop_mod.inspiration_brief(pid, window, conn=conn, profile=profile)
    comps = profiles_mod.list_competitors(pid, conn) if pid else []
    board = loop_mod.competitor_research_board(pid, conn=conn, profile=profile)
    tops = loop_mod.list_top_creatives(pid, conn=conn)

    # ---- header pill: latest loop-run date (real loop_runs data only)
    last_run_at = status["history"][0]["at"] if status["history"] else None
    pill_html = ("<span class='pill info'>&#128197; Last run &middot; %s</span>"
                 % esc(_fmt_date(last_run_at))) if last_run_at else ""

    # ---- stage cards: done / current / pending from real loop_runs.
    # A stage with a recorded run is done (green); the first stage
    # without one is current (violet); the rest are pending (grey).
    # When every stage has run, all cards stay green and stage 1 is
    # outlined as the restart point of the next cycle.
    by_key = {s["key"]: s for s in status["stages"]}
    keys = [k for k, _label, _icon in GL_STAGE_CARDS]
    done_map = {k: bool(by_key.get(k, {}).get("last_run")) for k in keys}
    all_done = all(done_map.values())
    current_key = (status["current_stage"]
                   if status["current_stage"] in keys else keys[0])
    cards = []
    for idx, (key, label, icon) in enumerate(GL_STAGE_CARDS):
        if done_map[key]:
            cls = "gl-stage done" + (" next" if all_done and key == keys[0] else "")
            badge = "<span class='gl-check'>&#10003;</span>"
            sub = "Last run %s" % _fmt_date(by_key[key]["last_run"])
        elif key == current_key:
            cls = "gl-stage now"
            badge = ""
            sub = "Current stage"
        else:
            cls = "gl-stage"
            badge = ""
            sub = "Not run yet"
        cards.append("<div class='%s'><span class='ic'>%s</span>%s"
                     "<div class='lb'>%d. %s</div><div class='sub'>%s</div></div>"
                     % (cls, icon, badge, idx + 1, esc(label), esc(sub)))
        if idx < len(GL_STAGE_CARDS) - 1:
            cards.append("<div class='gl-arrow'>&#8594;</div>")
    stages_html = "".join(cards)

    stage_rows = ""
    for s in status["stages"]:
        stage_rows += ("<tr><td>%s</td><td>%s</td><td>%s</td>"
                       "<td class='small'>%s</td></tr>"
                       % (esc(s["label"]),
                          "✅ done" if s["last_run"] else "⏳ pending",
                          esc(s["last_run"] or "—"), esc(s["detail"] or "")))
    hist = "".join("<tr><td>%s</td><td>%s</td><td class='small'>%s</td></tr>"
                   % (esc(h["at"]), esc(h["stage"]), esc(h["detail"]))
                   for h in status["history"][:15])

    if brief:
        brief_html = ("<p><strong>Theme:</strong> %s<br><strong>Hook:</strong> %s<br>"
                      "<strong>Format:</strong> %s<br><strong>CTA style:</strong> %s<br>"
                      "<span class='small mut'>Source: %s · %s · %s</span></p>"
                      "<div class='banner warn'>%s</div>"
                      % (esc(brief["theme"]), esc(brief["hook"]), esc(brief["format"]),
                         esc(brief["cta_style"]), esc(brief["source"]),
                         esc(brief["source_date"]), esc(brief["score_note"]),
                         esc(brief["rule"])))
    else:
        brief_html = ("<p class='mut'>No inspiration source yet — record a "
                      "top creative below, or let the mock insights arrive first.</p>")

    comp_rows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td class='small'>%s</td>"
        "<td><form method='post' action='/loop/competitor_delete' class='inline'>%s"
        "<input type='hidden' name='competitor_id' value='%d'>"
        "<button class='danger' type='submit'>Delete</button></form></td></tr>"
        % (esc(c["name"]), esc(c["handle"]), esc(c["niche"]), esc(c["source"]),
           ctx["csrf_field"], c["id"]) for c in comps)

    # ---- Competitor Research Board table. Active Ads / Longest
    # Running / Winning Signal come ONLY from the owner's recorded
    # findings (see growth_loop.competitor_research_board) — the Ad
    # Library publishes no numbers, so anything unrecorded stays "—".
    chip_classes = ["ok", "info", "warn"]
    board_rows = []
    for i, c in enumerate(board["competitors"]):
        n = c.get("findings_count") or 0
        active = str(n) if n else "—"
        days = c.get("longest_running_days")
        longest = ("%d days" % days) if days is not None else "—"
        sig = c.get("winning_signal") or ""
        sig_html = ("<span class='pill %s'>%s</span>"
                    % (chip_classes[i % len(chip_classes)], esc(sig))) if sig else "—"
        board_rows.append(
            "<tr><td><strong>%s</strong></td>"
            "<td><a href='%s' target='_blank' rel='noopener'>Open in Ad Library &#8599;</a>"
            "<br><a class='small' href='%s' target='_blank' rel='noopener'>Active ads only</a></td>"
            "<td>%s</td><td>%s</td><td>%s</td></tr>"
            % (esc(c["name"]), esc(c["search_url"]), esc(c["active_url"]),
               active, longest, sig_html))
    if not board_rows:
        board_rows.append(
            "<tr><td colspan='5' class='mut'>No competitors yet — add them "
            "in the Competitors section below.</td></tr>")
    board_table = "".join(board_rows)
    board_kw = "".join(
        "<li>%s — <a href='%s' target='_blank' rel='noopener'>Ad Library search</a>"
        " · <a href='%s' target='_blank' rel='noopener'>active only</a></li>"
        % (esc(k["keyword"]), esc(k["search_url"]), esc(k["active_url"]))
        for k in board["product_keywords"])
    if board["industry_keyword"]:
        board_kw += ("<li>%s (industry) — <a href='%s' target='_blank' "
                     "rel='noopener'>Ad Library search</a></li>"
                     % (esc(board["industry_keyword"]["keyword"]),
                        esc(board["industry_keyword"]["search_url"])))
    board_open_url = "%s?country=%s" % (loop_mod.AD_LIBRARY_BASE, board["country"])

    # ---- Research Checklist: a step is ticked only when the real
    # record behind it exists (competitors / a recorded finding / an
    # inspiration brief / a creative set / proposals).
    creatives_exist = bool(store.list_creatives(conn, profile_id=pid)) if pid else False
    props_exist = False
    for s in status["stages"]:
        if s["key"] == "optimisation_plan" and s.get("detail"):
            try:
                d = json.loads(s["detail"])
            except (ValueError, TypeError):
                d = {}
            if isinstance(d, dict) and d.get("proposals"):
                props_exist = True
    queue = ctx.get("queue")
    if (not props_exist and queue is not None
            and getattr(queue, "conn", None) is not None):
        try:
            props_exist = bool(queue.list_pending(profile_id=pid))
        except Exception:
            props_exist = False
    checks = [bool(comps), bool(tops), brief is not None,
              creatives_exist, props_exist]
    checklist_html = ""
    for i, step in enumerate(board["checklist"]):
        on = checks[i] if i < len(checks) else False
        checklist_html += ("<div class='gl-check-item'>"
                           "<span class='gl-tick%s'>&#10003;</span>"
                           "<span class='small'>%s</span></div>"
                           % ("" if on else " off", esc(step)))
    updated_html = ("<p class='small mut' style='margin-top:10px'>Last updated %s</p>"
                    % esc(_rel_time(last_run_at, now))) if last_run_at else ""

    top_rows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s days</td><td class='small'>%s · %s</td></tr>"
        % (esc(t["theme"]), esc(t["hook"]), esc(t["format"]), t["window_days"],
           esc(t["source"]), esc(t["source_date"])) for t in tops)
    strat = strategy_library
    css = """
<style>
.gl-stages{display:flex;gap:6px;align-items:stretch;overflow-x:auto;padding:4px 0 8px}
.gl-stage{flex:1;min-width:118px;background:#f4f4f8;border:1px solid var(--line);border-radius:12px;padding:12px 10px;position:relative}
.gl-stage.done{background:var(--okbg);border-color:#a9dcc2}
.gl-stage.now{background:var(--violetbg);border-color:var(--brand);box-shadow:0 0 0 1px var(--brand)}
.gl-stage.next{border-color:var(--brand);box-shadow:0 0 0 1px var(--brand)}
.gl-stage .ic{font-size:19px}
.gl-stage .lb{font-weight:700;font-size:13px;line-height:1.35;margin-top:6px}
.gl-stage .sub{font-size:11.5px;color:var(--mut);margin-top:3px}
.gl-check{position:absolute;top:8px;right:8px;width:19px;height:19px;border-radius:50%;background:#10b981;color:#fff;font-size:12px;display:flex;align-items:center;justify-content:center}
.gl-arrow{align-self:center;color:var(--mut);font-weight:700;flex:none}
.gl-cols{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:18px;align-items:start}
@media(max-width:1000px){.gl-cols{grid-template-columns:1fr}}
.gl-open{display:inline-block;border:1.5px solid var(--brand);color:var(--brand2);border-radius:10px;padding:7px 14px;font-weight:600;font-size:13.5px;white-space:nowrap}
.gl-open:hover{background:var(--violetbg);text-decoration:none}
.gl-check-item{display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-bottom:1px solid var(--line)}
.gl-check-item:last-child{border-bottom:0}
.gl-tick{width:21px;height:21px;border-radius:50%;background:#10b981;color:#fff;font-size:12px;display:flex;align-items:center;justify-content:center;flex:none;margin-top:1px}
.gl-tick.off{background:#fff;border:2px solid #cfcbe0;color:transparent}
</style>
"""
    head = """
<div class="ihead"><div><h1>Growth Loop</h1>
<p class="mut" style="margin-top:-4px">Competitor research to winning creatives, on repeat</p></div>
<div>%s</div></div>
<div class="gl-stages">%s</div>
<form method="post" action="/loop/run" style="margin:2px 0 18px">%s
<button type="submit">Run one full cycle (mock data)</button>
<span class="small mut" style="margin-left:10px">Current stage: %s &middot; Profile: %s</span></form>
<details><summary>How the loop runs</summary>
<p class="small">Competitor discovery → research of their best ads → inspiration
from the last 7/10 days' top creatives → new creatives → optimise →
approval-gated live → winners scale / losers pause → a fresh brief on fatigue.
Scheduler: <code>python -m app.jobs loop</code>. The research stage creates
task entries based on the public Meta Ad Library — a live pull is not wired
yet and no metric is invented; but on the Research Board below, 1-click
Ad Library links for every competitor/product are ready.</p></details>
""" % (pill_html, stages_html, ctx["csrf_field"],
       esc(status["current_stage"]),
       esc(profile["name"] if profile else "—"))
    board_card = """
<div class="card"><div class="ihead"><div><h2 style="margin-bottom:2px">Competitor Research Board</h2>
<p class="small mut" style="margin:0">Top competitors tracked for creative trend analysis (country: %s)</p></div>
<a class="gl-open" href="%s" target="_blank" rel="noopener">Open Ad Library &#8599;</a></div>
<div class="twrap"><table><tr><th>Competitor</th><th>Ad Library</th><th>Active Ads</th><th>Longest Running</th><th>Winning Signal</th></tr>%s</table></div>
<p class="small mut">Active Ads counts only the winning ads you recorded as findings for that
competitor (Record top creative, below); Longest Running is counted from a finding's recorded
Source date. The Ad Library itself publishes no numbers.</p>
<h3>Search by product keywords</h3><ul class="small">%s</ul>
<div class="banner warn">%s</div>
<p class="small mut">%s</p></div>
""" % (esc(board["country"]), esc(board_open_url), board_table, board_kw,
       esc(board["winner_signal_rule"]), esc(board["honest_note"]))
    checklist_card = """
<div class="card"><h2>Research Checklist</h2>%s%s</div>
""" % (checklist_html, updated_html)
    rest = """
<div class="card"><h2>Inspiration brief (window: %d days)</h2>%s</div>
<div class="card"><h2>Competitors (for %s)</h2>
<table><tr><th>Name</th><th>Handle</th><th>Niche</th><th>Source</th><th></th></tr>%s</table>
<form method="post" action="/loop/competitor_add">%s
<div class="row"><div><label>Name</label><input name="name" required></div>
<div><label>Handle</label><input name="handle"></div>
<div><label>URL</label><input name="url"></div>
<div><label>Niche</label><input name="niche"></div></div>
<button type="submit">Add competitor</button></form></div>
<div class="card"><h2>Top creatives (last 7/10 days — from research)</h2>
<table><tr><th>Theme</th><th>Hook</th><th>Format</th><th>Window</th><th>Source</th></tr>%s</table>
<form method="post" action="/loop/topcreative_add">%s
<div class="row"><div><label>Theme</label><input name="theme" required></div>
<div><label>Hook</label><input name="hook"></div>
<div><label>Format</label><input name="format"></div>
<div><label>CTA style</label><input name="cta_style"></div></div>
<div class="row"><div><label>Source (Ad Library URL/note)</label><input name="source"></div>
<div><label>Source date</label><input name="source_date" placeholder="YYYY-MM-DD"></div>
<div><label>Window (days)</label><select name="window_days"><option>7</option><option>10</option></select></div>
<div><label>Score note</label><input name="score_note"></div></div>
<button type="submit">Record top creative</button></form>
<p class="small mut">This is inspiration only — copying someone else's ad verbatim or
reusing their assets is forbidden.</p></div>
<div class="card"><h2>Loop stages &amp; history</h2>
<details><summary>Stage details</summary>
<table><tr><th>Stage</th><th>Status</th><th>Last run</th><th>Detail</th></tr>%s</table></details>
<table><tr><th>When</th><th>Stage</th><th>Detail</th></tr>%s</table>
<p class="small mut">Strategy Library: %d active entries · %d DO-NOT-APPLY ·
format taxonomy %d formats (Damini S22). The knowledge register is on the Trends page.</p></div>
""" % (window, brief_html,
       esc(profile["name"] if profile else "—"), comp_rows, ctx["csrf_field"],
       top_rows, ctx["csrf_field"], stage_rows, hist,
       len(strat.active_entries()), len(strat.do_not_apply_entries()),
       len(strat.FORMAT_TAXONOMY))
    body = (css + head + "<div class='gl-cols'>" + board_card + checklist_card
            + "</div>" + rest)
    return page("Growth Loop", "/loop", body, ctx["flash"], conn, ctx)


def post_loop_run(ctx, form):
    summary = loop_mod.run_cycle(conn=ctx["conn"], settings=ctx["settings"],
                                 profile=ctx["profile"], queue=ctx["queue"])
    if not summary.get("ok", True):
        return "Loop cycle BLOCKED: %s" % summary.get("blocked", "")
    refresh = (summary.get("stages") or {}).get("refresh") or {}
    return ("Loop cycle complete (%s) — proposals in queue: %d · "
            "auto-applied (AUTO_WITHIN_RULES): %d · fresh brief created: %s"
            % (summary.get("profile", ""), summary.get("proposals_added", 0),
               summary.get("auto_applied", 0),
               "yes" if refresh.get("new_brief") else "no"))


def post_loop_competitor_add(ctx, form):
    pid = ctx["profile"]["id"] if ctx["profile"] else 0
    profiles_mod.add_competitor(pid, {
        "name": form.get("name", ""), "handle": form.get("handle", ""),
        "url": form.get("url", ""), "niche": form.get("niche", ""),
        "source": "owner-added (UI)",
    }, ctx["conn"])
    return "Competitor added — it is included in the loop's discovery stage."


def post_loop_competitor_delete(ctx, form):
    profiles_mod.delete_competitor(int(form.get("competitor_id") or 0), ctx["conn"])
    return "Competitor deleted."


def post_loop_topcreative_add(ctx, form):
    pid = ctx["profile"]["id"] if ctx["profile"] else 0
    loop_mod.add_top_creative(pid, {
        "theme": form.get("theme", ""), "hook": form.get("hook", ""),
        "format": form.get("format", ""), "cta_style": form.get("cta_style", ""),
        "source": form.get("source", ""), "source_date": form.get("source_date", ""),
        "window_days": form.get("window_days", "7"),
        "score_note": form.get("score_note", ""),
    }, conn=ctx["conn"])
    return "Top creative recorded — the inspiration brief will now be built from it."


# ------------------------------------------------------------- Guardrails
def pg_guardrails(ctx):
    conn = ctx["conn"]
    status_rows = guardrails_mod.registry_status(ctx["settings"], conn)
    rows = ""
    for g in status_rows:
        pill = "bad" if g["severity"] == "BLOCK" else "warn"
        first_key = (g["setting_key"] or "").split(" / ")[0].strip()
        value = ctx["settings"].get(first_key) if first_key else None
        if not g["enabled"]:
            state = "<span class='pill bad'>OFF (owner)</span>"
        elif first_key and value in (None, "", 0, 0.0):
            state = "<span class='pill warn'>setting unset — inactive</span>"
        else:
            state = "<span class='pill ok'>active</span>"
        rows += ("<tr><td><strong>%s</strong><div class='small mut'>%s</div></td>"
                 "<td><span class='pill %s'>%s</span></td><td class='small'>%s</td>"
                 "<td class='small'>%s</td><td>%s</td>"
                 "<td><form method='post' action='/guardrails/toggle' class='inline'>%s"
                 "<input type='hidden' name='guardrail_id' value='%s'>"
                 "<input type='hidden' name='action' value='%s'>"
                 "<button class='secondary' type='submit'>%s</button></form></td></tr>"
                 % (esc(g["id"]), esc(g["name"]), pill, g["severity"],
                    esc(g["setting_key"] or "— (always active)"),
                    esc(str(value) if value not in (None, "") else "—"),
                    state, ctx["csrf_field"], esc(g["id"]),
                    "on" if not g["enabled"] else "off",
                    "Turn ON" if not g["enabled"] else "Turn OFF"))
    checklist = "".join(
        "<li>%s<div class='small mut'>Guardrails: %s</div></li>" % (esc(item), esc(", ".join(ids)))
        for item, ids in guardrails_mod.PREFLIGHT_CHECKLIST)
    body = """<h1>Guardrails</h1>
<p class="mut">Mistakes that raise CPC/CPL — system-enforced. BLOCK = the draft
does not enter the queue; WARN = a warning is attached.</p>
<details><summary>Full details</summary>
<p class="small">Every draft/plan passes these checks before the approval queue.
The optimiser never proposes a BLOCK action either. Thresholds are owner
settings — empty/0 = that guardrail is inactive (research numbers are only
labelled references in Settings, never defaults). Catalogue: winner-patterns
research §D (D1–D26) + the system's built-in gates. Guardrails can stop
mistakes — no system can guarantee CPC/CPL; the auction/market matters too.</p></details>
<div class="card"><h2>Pre-flight checklist (every draft, before the queue)</h2>
<ol>%s</ol></div>
<div class="card"><table><tr><th>Guardrail</th><th>Severity</th><th>Setting</th>
<th>Value</th><th>Status</th><th>Toggle</th></tr>%s</table>
<p class="small mut">The toggle is saved in GUARDRAILS_DISABLED (a global setting) —
it cannot be toggled via profile overrides. Turning one OFF is the owner's
decision; it is recorded in the audit log.</p></div>
""" % (checklist, rows)
    return page("Guardrails", "/guardrails", body, ctx["flash"], conn, ctx)


def post_guardrails_toggle(ctx, form):
    conn = ctx["conn"]
    gid = (form.get("guardrail_id") or "").strip()
    action = form.get("action") or ""
    if not gid:
        return "Guardrail id is missing."
    global_settings = load_settings()
    disabled = set(guardrails_mod.disabled_ids(global_settings))
    if action == "off":
        disabled.add(gid)
    else:
        disabled.discard(gid)
    global_settings["GUARDRAILS_DISABLED"] = sorted(disabled)
    save_settings(global_settings)
    audit(conn, "guardrail_toggled", "id=%s action=%s" % (gid, action))
    return "Guardrail %s is now %s." % (gid, "OFF" if action == "off" else "ON")


POST_ROUTES = {
    "/settings": (post_settings, "/settings"),
    "/killswitch": (post_killswitch, "/settings"),
    "/eligibility/confirm": (post_eligibility_confirm, "/eligibility"),
    "/eligibility/unconfirm": (post_eligibility_unconfirm, "/eligibility"),
    "/eligibility/add": (post_eligibility_add, "/eligibility"),
    "/eligibility/delete": (post_eligibility_delete, "/eligibility"),
    "/creative/generate": (post_creative_generate, "/creative"),
    "/creative/policycheck": (post_policycheck, "/creative"),
    "/creative/upload": (post_upload, "/creative"),
    "/creative/visualcheck": (post_visualcheck, "/creative"),
    "/providers/save": (post_providers_save, "/providers"),
    "/providers/preset": (post_providers_preset, "/providers"),
    "/providers/test": (post_providers_test, "/providers"),
    "/providers/removekey": (post_providers_removekey, "/providers"),
    "/creative/api_copy": (post_api_copy, "/creative"),
    "/creative/api_image": (post_api_image, "/creative"),
    "/creative/api_carousel": (post_api_carousel, "/creative"),
    "/creative/api_video": (post_api_video, "/creative"),
    "/creative/api_video_check": (post_api_video_check, "/creative"),
    "/planner/plan": (post_planner_plan, "/approvals"),
    "/profiles/switch": (post_profiles_switch, "/profiles"),
    "/profiles/create": (post_profiles_create, "/profiles"),
    "/profiles/update": (post_profiles_update, "/profiles"),
    "/profiles/duplicate": (post_profiles_duplicate, "/profiles"),
    "/profiles/delete": (post_profiles_delete, "/profiles"),
    "/loop/run": (post_loop_run, "/loop"),
    "/loop/competitor_add": (post_loop_competitor_add, "/loop"),
    "/loop/competitor_delete": (post_loop_competitor_delete, "/loop"),
    "/loop/topcreative_add": (post_loop_topcreative_add, "/loop"),
    "/guardrails/toggle": (post_guardrails_toggle, "/guardrails"),
    "/leads/add": (post_leads_add, "/leads"),
    "/reports/generate": (post_reports_generate, "/reports"),
    "/roles/run": (post_roles_run, "/roles"),
    "/budget/dataset": (post_budget_dataset, "/budget"),
    "/budget/optimise": (post_budget_optimise, "/approvals"),
}

GET_ROUTES = {
    "/": pg_today, "/mission": pg_mission, "/connect": pg_connect, "/roles": pg_roles,
    "/settings": pg_settings, "/eligibility": pg_eligibility,
    "/creative": pg_creative, "/providers": pg_providers,
    "/planner": pg_planner, "/campaigns": pg_campaigns,
    "/profiles": pg_profiles, "/loop": pg_loop,
    "/guardrails": pg_guardrails,
    "/approvals": pg_approvals, "/budget": pg_budget, "/leads": pg_leads,
    "/reports": pg_reports, "/trends": pg_trends, "/audit": pg_audit,
}


def login_page(msg=""):
    body = """<div class="card"><h1>SH Ads Desk — Owner Login</h1>
<p class="mut">Single-owner app. The password is the one the owner set at setup/env —
a password never appears in chat or code.</p>
%s<form method="post" action="/login">
<label>Password</label><input type="password" name="password" required>
<button type="submit" style="width:100%%">Login</button></form>
<p class="small mut" style="margin-top:12px">First time? If the owner is not set yet, go to
<a href="/setup">first-run setup</a>.</p></div>""" % (
        ('<div class="flash">%s</div>' % esc(msg)) if msg else "")
    return simple_page("Login", body)


def setup_page(msg=""):
    body = """<div class="card"><h1>First-run Setup</h1>
<p class="mut">Set the owner password (at least 10 characters). This happens only once —
it stays in the local database as a hash; the password itself is never stored.
After this, setup closes permanently.</p>
%s<form method="post" action="/setup">
<label>New owner password</label><input type="password" name="password" required>
<button type="submit" style="width:100%%">Set owner</button></form></div>""" % (
        ('<div class="flash">%s</div>' % esc(msg)) if msg else "")
    return simple_page("Setup", body)


class Handler(BaseHTTPRequestHandler):
    server_version = "SHAdsDesk/1.0"

    def log_message(self, fmt, *args):  # keep stdout clean; audit log is the record
        pass

    def _send_html(self, body, status=200, set_cookie=None, clear_cookie=False):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        if set_cookie:
            c = http_cookies.SimpleCookie()
            c["shads_session"] = set_cookie
            c["shads_session"]["httponly"] = True
            c["shads_session"]["samesite"] = "Lax"
            c["shads_session"]["path"] = "/"
            if os.environ.get("COOKIE_SECURE") == "1":
                c["shads_session"]["secure"] = True
            self.send_header("Set-Cookie", c.output(header="").strip())
        if clear_cookie:
            self.send_header("Set-Cookie", "shads_session=; Max-Age=0; Path=/")
        self.end_headers()
        self.wfile.write(data)

    def _send_generated(self, name):
        # Only files the app itself saved under data/generated/; basename
        # only, so no path traversal out of that folder is possible.
        safe = os.path.basename(name)
        full = os.path.join(providers.generated_dir(), safe)
        if not safe or not os.path.isfile(full):
            return self._send_html(simple_page("404", "<div class='card'><h1>404</h1>"
                                               "<p>File not found.</p></div>"), status=404)
        ext = safe.rsplit(".", 1)[-1].lower() if "." in safe else ""
        ctype = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                 "webp": "image/webp", "gif": "image/gif", "mp4": "video/mp4",
                 "mov": "video/quicktime", "webm": "video/webm"}.get(
                     ext, "application/octet-stream")
        with open(full, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _session(self, conn):
        raw = self.headers.get("Cookie", "")
        c = http_cookies.SimpleCookie(raw)
        morsel = c.get("shads_session")
        if morsel is None:
            return None
        return auth.get_session(morsel.value, conn)

    def _ctx(self, conn, session, flash=""):
        profile = profiles_mod.get_active_profile(conn)
        settings = profiles_mod.effective_settings(load_settings(), profile)
        eligibility = (profiles_mod.offerings_as_eligibility(profile["id"], conn)
                       if profile else load_eligibility())
        return {
            "conn": conn,
            "settings": settings,
            "profile": profile,
            "eligibility": eligibility,
            "extra_patterns": profiles_mod.compliance_patterns_for(profile),
            "queue": ApprovalQueue(),
            "csrf_field": '<input type="hidden" name="csrf" value="%s">' % esc(session["csrf"]),
            "flash": flash,
        }

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = urllib.parse.parse_qs(parsed.query)
        msg = (query.get("msg") or [""])[0]
        conn = get_db()
        if path == "/login":
            if not auth.owner_exists(conn):
                return _redirect(self, "/setup")
            return self._send_html(login_page(msg))
        if path == "/setup":
            if auth.owner_exists(conn):
                return _redirect(self, "/login")
            return self._send_html(setup_page(msg))
        session = self._session(conn)
        if session is None:
            return _redirect(self, "/login")
        if path.startswith("/generated/"):
            return self._send_generated(path[len("/generated/"):])
        handler = GET_ROUTES.get(path)
        if handler is None:
            return self._send_html(simple_page("404", "<div class='card'><h1>404</h1>"
                                               "<p>Page not found.</p></div>"), status=404)
        ctx = self._ctx(conn, session, flash=msg)
        ctx["query"] = query
        ctx["queue"].conn = conn
        try:
            return self._send_html(handler(ctx))
        except Exception as e:  # record redacted, show plain message
            log_error(conn, "web:" + path, str(e))
            return self._send_html(simple_page(
                "Error", "<div class='card'><h1>Something went wrong</h1><p>%s</p>"
                         "<p class='small mut'>Details are logged on the Errors &amp; Audit page (redacted).</p></div>"
                % esc(redact(str(e)))), status=500)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        form = {k: v[0] for k, v in urllib.parse.parse_qs(raw).items()}
        conn = get_db()

        if path == "/setup":
            ctx = {"conn": conn, "set_cookie": None}
            dest = post_setup(ctx, form)
            return self._finish_post(dest, ctx)
        if path == "/login":
            ctx = {"conn": conn, "set_cookie": None}
            dest = post_login(ctx, form)
            return self._finish_post(dest, ctx)
        if path == "/logout":
            session = self._session(conn)
            if session is not None:
                auth.destroy_session(session["token"], conn)
            self.send_response(303)
            self.send_header("Location", "/login")
            self.send_header("Set-Cookie", "shads_session=; Max-Age=0; Path=/")
            self.end_headers()
            return

        session = self._session(conn)
        if session is None:
            return _redirect(self, "/login")
        if not session["csrf"] or form.get("csrf") != session["csrf"]:
            return self._send_html(simple_page(
                "Blocked", "<div class='card'><h1>CSRF check failed</h1>"
                           "<p>Reopen the form and try again.</p></div>"), status=403)
        ctx = self._ctx(conn, session)
        ctx["queue"].conn = conn

        if path.startswith("/approvals/"):
            action = path.rsplit("/", 1)[1]
            msg = post_approval_action(ctx, form, action)
            return _redirect(self, "/approvals", msg)
        route = POST_ROUTES.get(path)
        if route is None:
            return self._send_html(simple_page("404", "<div class='card'><h1>404</h1></div>"),
                                   status=404)
        fn, dest = route
        try:
            msg = fn(ctx, form)
        except Exception as e:
            log_error(conn, "web:" + path, str(e))
            msg = "Error: %s (details are on the Errors & Audit page)" % redact(str(e))
        return _redirect(self, dest, msg)

    def _finish_post(self, dest, ctx):
        if "?" in dest:
            path, qs = dest.split("?", 1)
            query = urllib.parse.parse_qs(qs)
            msg = (query.get("msg") or [""])[0]
            if path == "/login":
                return self._send_html(login_page(msg))
            if path == "/setup":
                return self._send_html(setup_page(msg))
        self.send_response(303)
        self.send_header("Location", dest)
        if ctx.get("set_cookie"):
            c = http_cookies.SimpleCookie()
            c["shads_session"] = ctx["set_cookie"]
            c["shads_session"]["httponly"] = True
            c["shads_session"]["samesite"] = "Lax"
            c["shads_session"]["path"] = "/"
            if os.environ.get("COOKIE_SECURE") == "1":
                c["shads_session"]["secure"] = True
            self.send_header("Set-Cookie", c.output(header="").strip())
        self.end_headers()


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    get_db()  # create schema + data dir up front
    server = ThreadingHTTPServer((host, port), Handler)
    print("SH Ads Desk running at http://%s:%d  (META_MODE=%s, DRY_RUN default ON)"
          % (host, port, os.environ.get("META_MODE", "MOCK")))
    print("First run: open /setup to set the owner password (or put OWNER_PASSWORD_HASH in .env).")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
