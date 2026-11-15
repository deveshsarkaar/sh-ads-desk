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
from . import planner as planner_mod, policy_checker, providers
from . import reports as reports_mod
from . import roles, store, trends as trends_mod
from .approval_queue import ApprovalQueue
from .common import (audit, get_db, load_eligibility, load_settings,
                     log_error, redact, save_eligibility, save_settings)
from .execute import execute_approved_item
from .meta_client import API_VERSION_LABEL

CSS = """
:root{--ink:#17202b;--mut:#5b6b7f;--line:#dbe2ec;--bg:#f4f6fa;--card:#fff;
--brand:#1f4fd8;--brand2:#173ea8;--ok:#0d7a4a;--bad:#b3261e;--warn:#9a6a00;
--warnbg:#fff6dd;--okbg:#e7f6ee;--badbg:#fdecea;--radius:12px}
*{box-sizing:border-box}body{margin:0;font-family:'Segoe UI',system-ui,-apple-system,Roboto,Arial,sans-serif;
background:var(--bg);color:var(--ink);font-size:15px;line-height:1.55}
a{color:var(--brand);text-decoration:none}a:hover{text-decoration:underline}
header.top{background:#101c30;color:#fff;padding:0 18px;display:flex;align-items:center;
gap:14px;flex-wrap:wrap;position:sticky;top:0;z-index:5}
header.top .brand{font-weight:700;font-size:18px;padding:12px 0}
header.top .tag{font-size:11px;background:#274264;border-radius:20px;padding:3px 10px}
header.top form{margin-left:auto}
nav.main{background:#fff;border-bottom:1px solid var(--line);padding:8px 14px;
display:flex;gap:6px;flex-wrap:wrap;position:sticky;top:49px;z-index:4}
nav.main a{padding:6px 11px;border-radius:8px;color:var(--ink);font-size:14px}
nav.main a:hover{background:var(--bg);text-decoration:none}
nav.main a.on{background:var(--brand);color:#fff}
main{max-width:1060px;margin:0 auto;padding:20px 16px 60px}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
padding:18px 20px;margin:0 0 16px;box-shadow:0 1px 2px rgba(16,28,48,.04)}
h1{font-size:24px;margin:4px 0 6px}h2{font-size:18px;margin:2px 0 10px}
h3{font-size:15px;margin:14px 0 6px}.mut{color:var(--mut)}.small{font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
.kpi{font-size:26px;font-weight:700}
.pill{display:inline-block;border-radius:20px;padding:2px 10px;font-size:12px;font-weight:600}
.pill.ok{background:var(--okbg);color:var(--ok)}.pill.bad{background:var(--badbg);color:var(--bad)}
.pill.warn{background:var(--warnbg);color:var(--warn)}.pill.info{background:#e8effe;color:var(--brand2)}
.banner{border-radius:var(--radius);padding:12px 16px;margin:0 0 16px;font-size:14px}
.banner.warn{background:var(--warnbg);border:1px solid #ecd28a}
.banner.bad{background:var(--badbg);border:1px solid #f0b6b1}
.banner.ok{background:var(--okbg);border:1px solid #a9dcc2}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{border-bottom:1px solid var(--line);padding:8px 8px;text-align:left;vertical-align:top}
th{color:var(--mut);font-weight:600}
input,select,textarea{width:100%;padding:9px 11px;border:1px solid var(--line);
border-radius:8px;font:inherit;background:#fff;margin:4px 0 10px}
label{font-weight:600;font-size:14px}
button,.btn{display:inline-block;background:var(--brand);color:#fff;border:0;border-radius:8px;
padding:9px 16px;font:inherit;font-weight:600;cursor:pointer}
button:hover,.btn:hover{background:var(--brand2);text-decoration:none}
button.secondary,.btn.secondary{background:#e8edf5;color:var(--ink)}
button.danger{background:var(--bad)}button:disabled{opacity:.5;cursor:not-allowed}
.inline{display:inline}.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
pre{background:#0f1a2c;color:#d7e3f5;border-radius:10px;padding:12px;overflow:auto;
font-size:13px;white-space:pre-wrap;word-break:break-word}
.flash{border-radius:10px;padding:10px 14px;margin:0 0 14px;background:#e8effe;border:1px solid #b9ccfb}
.check li{margin:3px 0}.footer{color:var(--mut);font-size:12.5px;text-align:center;padding:18px}
@media(max-width:640px){main{padding:14px 10px 50px}h1{font-size:21px}
header.top .tag{display:none}table{font-size:13px}}
"""

NAV = [
    ("/", "Today"), ("/connect", "Connect"), ("/roles", "Roles"),
    ("/settings", "Settings"), ("/eligibility", "Eligibility"),
    ("/creative", "Creative Studio"), ("/providers", "API Providers"),
    ("/planner", "Planner"),
    ("/approvals", "Approvals"), ("/budget", "Budget"), ("/leads", "Leads"),
    ("/reports", "Reports"), ("/trends", "Trends"), ("/audit", "Errors & Audit"),
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

SETTING_FIELDS = [
    ("TOTAL_DAILY_BUDGET_CAP", "number", "Sab campaigns milakar ek din ka max kharch. 0/khaali = koi cap set nahi (optimiser safety-stop check nahi karega)."),
    ("PER_CAMPAIGN_CAP", "number", "Ek campaign ka max budget. 0/khaali = unset."),
    ("LIFETIME_CAP", "number", "Poori lifetime ka max kharch cap. 0/khaali = unset."),
    ("TARGET_COST_PER_QUALIFIED_LEAD", "number", "Ek qualified lead par target kharch. Optimiser isi se winner/loser judge karta hai — unset ho to judgement nahi hota."),
    ("MIN_SPEND", "number", "Isse kam spend wale ad ko 'not enough data' kaha jayega."),
    ("MIN_EVENTS", "number", "Isse kam enquiries wale ad ko judge nahi kiya jayega."),
    ("EVALUATION_WINDOW_DAYS", "number", "Kitne din ke data par judgement hoga."),
    ("CONVERSION_LAG_WINDOW_DAYS", "number", "Conversion report hone me lagne wale din — isse naye ad judge nahi honge."),
    ("MAX_BUDGET_CHANGE_PCT", "number", "Ek baar me budget badlav ki max % sima (proposal bhi isse zyada ka nahi banega)."),
    ("MIN_DAYS_BETWEEN_CHANGES", "number", "Do budget badlav ke beech kam se kam itne din."),
    ("ACCOUNT_CURRENCY", "text", "Ad account ki currency (jaise INR). Sirf display/reconciliation ke liye."),
    ("ACCOUNT_TIMEZONE", "text", "Ad account ka timezone (jaise Asia/Kolkata)."),
    ("ATTRIBUTION_WINDOW", "text", "Insights attribution window jo use ho raha hai (Step 3 me verify hoga — abhi UNVERIFIED)."),
    ("DESTINATION_URL", "text", "Ad kahan bhejegaa — owner hi set karega. Khaali = destination gate band."),
    ("DESTINATION_READY", "checkbox", "Tick karne ka matlab: destination page ready hai aur traffic wahan ja sakta hai."),
    ("DRY_RUN", "checkbox", "ON (default) = koi asli write nahi, sab MOCK par simulate hoga — LIVE mode me bhi."),
    ("AUTOMATION_MODE", "select", "OFF = sirf reports. PROPOSE (default) = har cheez approval ke baad. AUTO_WITHIN_RULES = sirf tab jab owner ne exact rules likh kar approve kiye hon (Step 5)."),
]


def esc(x):
    return html.escape(str(x if x is not None else ""))


def page(title, active, body, flash=None, conn=None):
    nav = "".join('<a href="%s" class="%s">%s</a>' % (href, "on" if href == active else "", label)
                  for href, label in NAV)
    kill = ""
    if conn is not None:
        q = ApprovalQueue()
        q.conn = conn
        if q.kill_switch_active():
            kill = ('<div class="banner bad"><strong>KILL SWITCH ON.</strong> '
                    'Automation disabled hai aur approvals/execution blocked hain. '
                    'Ye apne aap kabhi resume nahi hoga — Settings me jaakar owner '
                    'khud band karega.</div>')
    flash_html = '<div class="flash">%s</div>' % esc(flash) if flash else ""
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s · SH Ads Desk</title><style>%s</style></head><body>
<header class="top"><span class="brand">SH Ads Desk</span>
<span class="tag">Software Hub · Meta Ads</span><span class="tag">DRY_RUN + PROPOSE default</span>
<form method="post" action="/logout" class="inline"><button class="secondary" type="submit">Logout</button></form></header>
<nav class="main">%s</nav><main>%s%s%s</main>
<div class="footer">SH Ads Desk · Step 1 logic VERIFIED (local tests) · Live Meta path UNTESTED · API %s · Provider API keys sirf server ki data/secrets.env me rehti hain — app unhe kabhi dikhata ya log nahi karta</div>
</body></html>""" % (esc(title), CSS, nav, kill, flash_html, body, esc(API_VERSION_LABEL))


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
                'Asli Meta adapter code-complete hai lekin kisi real account par '
                'test NAHI hua. DRY_RUN=%s — jab tak DRY_RUN ON hai, writes MOCK '
                'par hi simulate honge.</div>' % esc(settings.get("DRY_RUN")))
    return ('<div class="banner ok"><strong>META_MODE=MOCK.</strong> Saara data aur '
            'saare writes mock hain. Asli Meta connection Steps 2–4 me aayega '
            '(abhi UNTESTED).</div>')


# ---------------------------------------------------------------- pages (GET)
def pg_today(ctx):
    conn, settings = ctx["conn"], ctx["settings"]
    store.seed_insights(conn=conn)
    rows = store.load_insight_rows(conn)
    queue = ctx["queue"]
    pending = queue.list_pending()
    spend = sum(float(r.get("spend") or 0) for r in rows)
    enq = sum(int(r.get("enquiries") or 0) for r in rows)
    qual = sum(int(r.get("qualified_leads") or 0) for r in rows)
    leads = store.lead_summary(conn)
    body = """
<h1>Today</h1><p class="mut">Software Hub ke Meta ads ka control desk. Default mode:
<strong>DRY_RUN + PROPOSE</strong> — kuch bhi aapke approval ke bina nahi hota.</p>
%s
<div class="grid">
 <div class="card"><div class="mut small">Reported spend (MOCK data)</div><div class="kpi">%s</div>
 <div class="small mut">Currency setting: %s · Reporting lag ho sakta hai</div></div>
 <div class="card"><div class="mut small">Enquiries</div><div class="kpi">%d</div>
 <div class="small mut">Qualified leads: %d · Junk: %d</div></div>
 <div class="card"><div class="mut small">Approvals pending</div><div class="kpi">%d</div>
 <div class="small mut"><a href="/approvals">Approval queue kholo</a> — har item pehle dikhega, phir action hoga</div></div>
 <div class="card"><div class="mut small">Lead log (counts only)</div><div class="kpi">%d</div>
 <div class="small mut">Orders: %d · Reseller applications: %d</div></div>
</div>
<div class="card"><h2>Shuruaat yahan se</h2><ol class="check">
<li><a href="/connect">Connect wizard</a> — Meta connection me kya ready hai, kya baki hai</li>
<li><a href="/eligibility">Eligibility</a> — jab tak kisi product ki resale permission proof ke saath confirm nahi, uska ad ban hi nahi sakta (gate fails closed)</li>
<li><a href="/creative">Creative Studio</a> — angles, copy, poster brief, reel script banao aur policy check karo</li>
<li><a href="/providers">API Providers</a> — apni generation APIs (OpenAI/Claude/Higgsfield/Kling) connect karo; phir Creative Studio se asal copy, poster, carousel aur reel banege</li>
<li><a href="/planner">Planner</a> — campaign structure ka plan banao aur approval ke liye bhejo</li>
<li><a href="/reports">Reports</a> — daily/weekly report (Hinglish option ke saath)</li></ol>
<p class="small mut">Neeche ke numbers MOCK demo dataset ke hain — asli numbers Step 3 (read-only API) ke baad aayenge.</p></div>
""" % (mode_banner(settings), esc(spend), esc(settings.get("ACCOUNT_CURRENCY") or "unset"),
       enq, qual, int(leads.get("junk", 0)), len(pending),
       sum(leads.values()), int(leads.get("order", 0)),
       int(leads.get("reseller_application", 0)))
    return page("Today", "/", body, ctx["flash"], conn)


def pg_connect(ctx):
    conn = ctx["conn"]
    checks = [
        ("Facebook Page (owner khud banayega Meta par)", bool(os.environ.get("META_PAGE_ID")),
         "META_PAGE_ID env"),
        ("Meta Business portfolio + ad account", bool(os.environ.get("META_AD_ACCOUNT_ID")),
         "META_AD_ACCOUNT_ID env"),
        ("Developer app + access token (Meta ki apni screen se milega)",
         bool(os.environ.get("META_ACCESS_TOKEN")), "META_ACCESS_TOKEN env — app me kabhi type nahi hota"),
        ("Mode", True, "META_MODE=%s (default MOCK)" % os.environ.get("META_MODE", "MOCK")),
    ]
    rows_html = "".join(
        "<tr><td>%s</td><td>%s</td><td class='small mut'>%s</td></tr>"
        % (esc(name), '<span class="pill ok">Set hai</span>' if ok else '<span class="pill bad">Missing</span>', esc(hint))
        for name, ok, hint in checks)
    body = """
<h1>Connect Wizard — Meta setup (Step 2 guide)</h1>
<p class="mut">Ye page sirf batata hai kya connected hai aur kya baki hai. Ye app
<strong>kabhi password nahi mangta</strong> — login hamesha Meta ki apni screens par hota hai.
Token sirf server ke environment (.env) me rehta hai, app ke andar type nahi hota.</p>
%s
<div class="card"><h2>Status</h2><table><tr><th>Cheez</th><th>Status</th><th>Note</th></tr>%s</table></div>
<div class="card"><h2>Owner ke manual steps (Meta ki screens par)</h2><ol class="check">
<li>Facebook Page banao (agar nahi hai) — facebook.com/pages/create</li>
<li>business.facebook.com par Business portfolio banao aur Page + Ad account jodo</li>
<li>Ad account me payment method Meta ki billing screen me add karo (app kabhi card nahi mangta)</li>
<li>developers.facebook.com par app banao → Marketing API use case chuno</li>
<li>Permissions: pehle sirf read-only (ads_read) — write (ads_management) Step 4 ki approval ke baad hi</li>
<li>Token generate karke apne server ke .env me META_ACCESS_TOKEN rakho; ad account id META_AD_ACCOUNT_ID me</li>
<li>META_MODE ko tab tak MOCK rakho jab tak Step 3 (read-only compare) pass na ho</li></ol>
<p class="small mut">Kaunsi permission/access-tier lagegi ye objective par nirbhar hai —
official doc: developers.facebook.com/documentation/ads-commerce/marketing-api/get-started/authorization
(ye page is build me live fetch NAHI hua — UNVERIFIED, Step 2 me owner ke saath padha jayega.)
API version pin: %s</p></div>
""" % (mode_banner(ctx["settings"]), rows_html, esc(API_VERSION_LABEL))
    return page("Connect", "/connect", body, ctx["flash"], conn)


def pg_roles(ctx):
    conn = ctx["conn"]
    last = {}
    for r in conn.execute(
            "SELECT role, status, MAX(created_at) AS t FROM role_runs GROUP BY role").fetchall():
        last[r["role"]] = r
    errs = {r["role"] for r in conn.execute(
        "SELECT DISTINCT role FROM role_runs WHERE status = 'error'").fetchall()}
    cards, current_group = [], None
    for key, label, group in ROLE_NAMES:
        if group != current_group:
            cards.append('<h3>%s</h3><div class="grid">' % esc(group))
            if current_group is not None:
                cards.append("</div>")
            current_group = group
        run = last.get(key)
        status = ('<span class="pill ok">Done %s</span>' % esc(run["t"][:16].replace("T", " "))
                  if run else '<span class="pill info">Idle — abhi run nahi hua</span>')
        if key in errs:
            status += ' <span class="pill bad">Errors hue hain</span>'
        cards.append('<div class="card"><strong>%s</strong><br>%s</div>' % (esc(label), status))
    cards.append("</div>")
    body = """
<h1>Roles — 20 logical roles</h1>
<p class="mut">Har role ka output alag aur auditable hai. Status asal <code>role_runs</code>
table se aata hai — jobs chalane par (<code>python -m app.jobs optimise</code>) ya
neeche wale button se roles run hote hain. Koi always-on agent nahi hai.</p>
<form method="post" action="/roles/run">%s
<p class="small">Ye button dabane se Roles 1–9, 11, 12, 15–18, 20 ek baar MOCK data par
chalenge aur unke outputs is page + audit log me dikhenge. Role 10/13/14/19 apne
pages (Creative/Approvals/Optimiser) se chalte hain. Kuch bhi Meta par write nahi hoga.</p>
<button type="submit">Roles ek baar chalao (MOCK)</button></form>
%s
""" % (ctx["csrf_field"], "".join(cards))
    return page("Roles", "/roles", body, ctx["flash"], conn)


def pg_settings(ctx):
    conn = ctx["conn"]
    settings = ctx["settings"]
    fields = []
    for key, kind, helptext in SETTING_FIELDS:
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
            input_html = '<input name="%s" value="%s">' % (key, esc(val if val is not None else ""))
        fields.append('<label>%s</label>%s<p class="small mut" style="margin-top:-6px">%s</p>'
                      % (key, input_html, esc(helptext)))
    kill_on = ctx["queue"].kill_switch_active()
    body = """
<h1>Settings</h1>
<p class="mut">Saari values yahin se badalti hain — code me kuch hardcoded nahi hai.
Defaults khaali/zero hain; koi benchmark number default nahi rakha gaya hai.</p>
<div class="card"><form method="post" action="/settings">%s%s
<p class="small">Save dabane se settings is server ki local settings file me save hongi
(audit log me entry ke saath). Isse koi Meta write nahi hota.</p>
<button type="submit">Settings save karo</button></form></div>
<div class="card"><h2>Kill Switch</h2>
<p>Kill switch ON karne se: automation band, saare managed objects (mock/live registry)
PAUSED, aur approvals/execution blocked. Ye <strong>apne aap kabhi resume nahi hota</strong> —
band bhi owner khud karega.</p>
<p>Abhi ki sthiti: %s</p>
<form method="post" action="/killswitch">%s
<input type="hidden" name="action" value="%s">
<button class="danger" type="submit">%s</button></form></div>
""" % (ctx["csrf_field"], "".join(fields),
       '<span class="pill bad">ON — sab ruka hua hai</span>' if kill_on else '<span class="pill ok">OFF</span>',
       ctx["csrf_field"], "off" if kill_on else "on",
       "Kill switch band karo (owner action)" if kill_on else "KILL SWITCH ON karo — sab roko")
    return page("Settings", "/settings", body, ctx["flash"], conn)


def pg_eligibility(ctx):
    conn, settings = ctx["conn"], ctx["settings"]
    products = load_eligibility()
    rows_html = []
    for p in products:
        confirmed = p.get("resale_permission_confirmed") is True
        pill = ('<span class="pill ok">CONFIRMED</span>' if confirmed
                else '<span class="pill bad">NOT CONFIRMED — ad nahi ban sakta</span>')
        rows_html.append(
            "<tr><td><strong>%s</strong></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (esc(p.get("product")), esc(p.get("supplier") or "—"), pill,
               esc(p.get("proof_note") or "—"), esc(p.get("terms_checked_date") or "—")))
    options = "".join('<option>%s</option>' % esc(p.get("product")) for p in products)
    dest = policy_checker.check_destination(settings)
    body = """
<h1>Product Eligibility &amp; Destination Gate</h1>
<p class="mut">Rule: jab tak kisi product ki <strong>resale permission proof note +
terms-checked date</strong> ke saath confirm nahi hoti, us product ka ad system
banane hi nahi dega (fails closed). Kuch bhi invent nahi kiya gaya hai — saari
entries abhi unconfirmed hain.</p>
<div class="card"><h2>Products (%d)</h2>
<table><tr><th>Product</th><th>Supplier</th><th>Resale permission</th><th>Proof note</th><th>Terms checked</th></tr>%s</table></div>
<div class="card"><h2>Permission confirm karo (owner only)</h2>
<form method="post" action="/eligibility/confirm">%s
<label>Product</label><select name="product">%s</select>
<label>Supplier</label><input name="supplier" placeholder="Supplier ka naam (jaisa proof me hai)">
<label>Proof note</label><input name="proof_note" placeholder="Proof kahan hai — file/agreement ka sandarbh" required>
<label>Terms checked date</label><input name="terms_checked_date" type="date" required>
<p class="small">Confirm dabane se sirf is product ki entry PRODUCT_ELIGIBILITY.yaml me
update hogi. Proof note ya date khaali ho to confirm <strong>refuse</strong> ho jayega.
Isse koi ad create nahi hota — ye sirf gate kholta hai.</p>
<button type="submit">Permission confirm karo</button></form>
<form method="post" action="/eligibility/unconfirm" style="margin-top:10px">%s
<label>Permission wapas lo — Product</label><select name="product">%s</select>
<p class="small">Unconfirm dabane se us product ke ads phir se block ho jayenge.</p>
<button class="secondary" type="submit">Unconfirm karo</button></form></div>
<div class="card"><h2>Destination gate</h2>
<p>Abhi ki sthiti: %s</p>
<p class="small mut">DESTINATION_URL aur DESTINATION_READY Settings page se set hote hain —
system khud koi destination nahi chunta, aur Lucifer bot par traffic tab tak nahi
jayega jab tak owner na kahe.</p></div>
""" % (len(products), "".join(rows_html), ctx["csrf_field"], options,
       ctx["csrf_field"], options,
       '<span class="pill ok">KHULA hai</span>' if dest["allowed"]
       else '<span class="pill bad">BAND hai</span> — ' + esc("; ".join(dest["reasons"])))
    return page("Eligibility", "/eligibility", body, ctx["flash"], conn)


def pg_creative(ctx):
    conn = ctx["conn"]
    products = load_eligibility()
    options = "".join('<option>%s</option>' % esc(p.get("product")) for p in products)
    segments = "".join('<option>%s</option>' % s for s in
                       ("students", "freelancers", "creators", "bot owners", "agencies"))
    saved = store.list_creatives(conn)
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
                view = ' <a href="/generated/%s" target="_blank" rel="noopener">dekho</a>' % esc(a["filename"])
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
                '<span class="small">— <a href="/providers">API Providers page</a> se connect karo</span>')

    jobs = store.list_video_jobs(conn)
    job_html = ""
    for j in jobs[-10:]:
        job_html += ('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
                     '<td><form method="post" action="/creative/api_video_check" class="inline">%s'
                     '<input type="hidden" name="job_id" value="%s">'
                     '<button class="secondary" type="submit">Status check karo</button></form></td></tr>'
                     % (esc(j.get("job_id")), esc(j.get("provider")), esc(j.get("status")),
                        esc((j.get("prompt") or "")[:60]), ctx["csrf_field"],
                        esc(j.get("job_id"))))
    api_section = """
<div class="card"><h2>Generate with API (owner ki connected APIs)</h2>
<p class="small mut">Ye actions sirf generation karte hain — Meta par kuch write nahi hota.
Generated copy pehle policy check se guzregi; generated files asset bankar visual-check
PENDING ke saath save hongi. Cost har jagah <strong>unknown — provider billing</strong>
rahega. Adapters real accounts par UNTESTED hain.</p>
<h3>Ad copy — Text API: %s</h3>
<form method="post" action="/creative/api_copy">%s
<label>Product</label><select name="product">%s</select>
<label>Segment</label><select name="segment">%s</select>
<label>Extra instruction (optional)</label><input name="instruction" placeholder="Jaise: hostel students ke angle se likho">
<p class="small">API connected na ho to template drafts banenge aur saaf label lagega.</p>
<button type="submit">Copy generate karo (API/templates)</button></form>
<h3>Poster image — Image API: %s</h3>
<form method="post" action="/creative/api_image">%s
<label>Image prompt</label><textarea name="prompt" rows="2" placeholder="Poster ke liye prompt — saaf, bina kisi brand logo/claim ke" required></textarea>
<button type="submit">Poster image banao</button></form>
<h3>Carousel — Image API (ek slide = ek line = ek image)</h3>
<form method="post" action="/creative/api_carousel">%s
<label>Slide briefs (har line ek slide ka prompt)</label>
<textarea name="slides" rows="4" placeholder="Slide 1 ka prompt&#10;Slide 2 ka prompt&#10;Slide 3 ka prompt" required></textarea>
<button type="submit">Carousel images banao</button></form>
<h3>Reel video — Video API: %s</h3>
<form method="post" action="/creative/api_video">%s
<label>Video prompt</label><textarea name="prompt" rows="2" placeholder="Reel ke liye prompt" required></textarea>
<label>Image URL (optional — image-to-video ke liye)</label><input name="image_url">
<div class="row"><div style="flex:1"><label>Duration (optional)</label><input name="duration" placeholder="5"></div>
<div style="flex:1"><label>Aspect ratio (optional)</label><input name="aspect" placeholder="9:16"></div></div>
<p class="small">Submit dabane se video job provider par jayega. Status neeche wali table
me "Status check karo" se poll hoga — done hone par file yahin asset bankar aa jayegi.</p>
<button type="submit">Reel video submit karo</button></form>
%s
</div>
""" % (api_pill("text"), ctx["csrf_field"], options, segments,
       api_pill("image"), ctx["csrf_field"], ctx["csrf_field"],
       api_pill("video"), ctx["csrf_field"],
       ('<h3>Video jobs</h3><table><tr><th>Job ID</th><th>Provider</th><th>Status</th>'
        '<th>Prompt</th><th>Action</th></tr>%s</table>' % job_html) if job_html else "")
    body = """
<h1>Creative Studio</h1>
<p class="mut">Yahan TEXT banta hai: angles, Hinglish + English copy, poster BRIEF aur
reel SCRIPT. Asal image/video files aur API-wali copy neeche ke <strong>Generate with
API</strong> section se banti hai — lekin sirf tab, jab owner ne
<a href="/providers">API Providers</a> page par apni API (Higgsfield/Kling/OpenAI/Claude
wagairah) connect ki ho. Koi API connect na ho to wo buttons saaf bolenge "API not
connected" aur template wala rasta chalta rahega. Owner apni file khud bhi upload kar
sakta hai. Har asset — generated ho ya uploaded — visual check pass hue bina approval
queue me nahi ja sakta, aur generated copy bhi pehle policy check se guzarti hai.</p>
<div class="card"><h2>Naya creative set banao</h2>
<form method="post" action="/creative/generate">%s
<label>Product</label><select name="product">%s</select>
<label>Segment</label><select name="segment">%s</select>
<p class="small">Generate dabane se Roles 6–9 chalenge, copy Role 10 (policy checker)
se pass hogi, aur set neeche save ho jayega. Eligibility/destination gate band ho to
copy <strong>BLOCKED</strong> mark hogi aur approval ke liye bhejna mumkin nahi hoga.</p>
<button type="submit">Creative set generate karo</button></form></div>
<div class="card"><h2>Policy checker (turant test)</h2>
<form method="post" action="/creative/policycheck">%s
<label>Ad text</label><textarea name="text" rows="3" placeholder="Apni ad line yahan likho — banned claims turant pakde jayenge"></textarea>
<p class="small">Check dabane se sirf scan hoga — kuch save ya create nahi hoga.</p>
<button class="secondary" type="submit">Claims check karo</button></form></div>
<div class="card"><h2>Saved creative sets</h2>
<table><tr><th>#</th><th>Product</th><th>Kind</th><th>Policy</th></tr>%s</table></div>
%s
<div class="card"><h2>Assets (generated + manual upload)</h2>
<form method="post" action="/creative/upload">%s
<label>File ka naam (file aap apne paas rakho — yahan sirf registry entry banti hai)</label>
<input name="filename" placeholder="poster-v1.png" required>
<label>Kind</label><select name="kind"><option>image</option><option>video</option></select>
<p class="small">Upload dabane se asset PENDING visual-check ke saath register hoga.
Neeche checklist ke saare item tick karke hi PASS hoga — uske bina asset approval
queue me nahi ja sakta.</p>
<button class="secondary" type="submit">Asset register karo</button></form>
<table><tr><th>File</th><th>Kind</th><th>Source</th><th>Visual check</th></tr>%s</table>
<form method="post" action="/creative/visualcheck" style="margin-top:12px">%s
<label>Asset file naam (PASS karne ke liye)</label><input name="filename" required>
<label><input type="checkbox" name="c1" style="width:auto"> Readable text hai</label><br>
<label><input type="checkbox" name="c2" style="width:auto"> Product names/logos sahi hain</label><br>
<label><input type="checkbox" name="c3" style="width:auto"> Koi misleading claim nahi hai</label><br>
<label><input type="checkbox" name="c4" style="width:auto"> Koi unauthorized brand mark nahi hai</label>
<p class="small">PASS dabane se asset ka visual check PASS mark hoga (audit entry ke saath).
Ek bhi item untick ho to refuse ho jayega.</p>
<button type="submit">Visual check PASS karo</button></form></div>
""" % (ctx["csrf_field"], options, segments, ctx["csrf_field"],
       saved_html or '<tr><td colspan="4" class="mut">Abhi koi creative set save nahi hai</td></tr>',
       api_section,
       ctx["csrf_field"], asset_html or '<tr><td colspan="4" class="mut">Koi asset register nahi hai</td></tr>',
       ctx["csrf_field"])
    return page("Creative Studio", "/creative", body, ctx["flash"], conn)


PROVIDER_FIELD_LABELS = {
    "text": [("chat_path", "Chat/messages path")],
    "image": [("image_path", "Image generation path"),
              ("prompt_field", "Prompt field name"),
              ("model_field", "Model field name"),
              ("size_field", "Size field name"), ("size", "Size"),
              ("response_url_path", "Response me image URL ka path"),
              ("response_b64_path", "Response me b64 image ka path")],
    "video": [("submit_path", "Submit path"),
              ("poll_path", "Status/poll path ({id} = job id)"),
              ("prompt_field", "Prompt field name"),
              ("model_field", "Model field name"),
              ("image_field", "Image URL field name"),
              ("duration_field", "Duration field name"),
              ("aspect_field", "Aspect ratio field name"),
              ("job_id_path", "Job ID ka response path"),
              ("status_path", "Status ka response path"),
              ("done_values", "Done status values (comma se)"),
              ("fail_values", "Fail status values (comma se)"),
              ("result_url_path", "Result video URL ka response path"),
              ("poll_interval_sec", "Poll interval (seconds)"),
              ("max_wait_sec", "Max wait (seconds)")],
}

PROVIDER_TITLES = {
    "text": ("Text / LLM", "Ad copy ke liye — OpenAI (ChatGPT models), Anthropic Claude, ya koi OpenAI-compatible API."),
    "image": ("Image generation", "Poster aur carousel images ke liye — OpenAI-compatible image API ya custom mapping wali API."),
    "video": ("Video generation", "Reel video ke liye — Higgsfield, Kling-style async APIs (submit + poll)."),
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
    key_pill = ('<span class="pill ok">Key set hai (%s)</span>' % esc(status["key_source"])
                if status["key_set"] else '<span class="pill bad">Key set nahi hai</span>')
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
                         ("custom", "Custom header + prefix (jaise Higgsfield: Authorization + 'Key ')")))
    fmt_opts = "".join(
        '<option value="%s" %s>%s</option>'
        % (v, "selected" if cfg.get("payload_format") == v else "", v)
        for v in ("openai", "anthropic"))
    remove_html = ""
    if status["key_source"] == "file":
        remove_html = ("""<form method="post" action="/providers/removekey" class="inline">%s
<input type="hidden" name="capability" value="%s">
<button class="secondary" type="submit">Key hatao</button></form>"""
                       % (ctx["csrf_field"], cap))
    elif status["key_source"] == "env":
        remove_html = ('<p class="small mut">Key environment variable %s se aa rahi hai — '
                       'hatana hai to server ke env se hatao.</p>'
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
<label>Preset badlo (preset ke pre-filled defaults lag jayenge — base URL, model, paths reset ho jayenge; key bani rahegi)</label>
<select name="preset">%s</select>
<button class="secondary" type="submit">Preset lagao</button></form>
<form method="post" action="/providers/save">%s
<input type="hidden" name="capability" value="%s">
<input type="hidden" name="preset" value="%s">
<label>Provider naam (apni pehchan ke liye)</label>
<input name="provider_name" value="%s">
<label>Model</label>
<input name="model" value="%s">
<label>API key %s</label>
<input type="password" name="api_key" autocomplete="off" placeholder="%s">
<details><summary><strong>Advanced (optional)</strong> — base URL override, auth aur paths. Known presets me ye sab pehle se bhara hai; sirf tab badlo jab provider ki docs kuch aur kahein.</summary>
<label>Base URL %s</label>
<input name="base_url" value="%s">
<label>Auth style</label><select name="auth_style">%s</select>
<label>Auth header name</label><input name="auth_header" value="%s">
<label>Auth value prefix (jaise 'Key ' ya 'Bearer ')</label><input name="auth_prefix" value="%s">
<label>Extra headers (JSON object, optional)</label>
<textarea name="extra_headers" rows="2">%s</textarea>
<label>Test connection path (GET — models/list type ka harmless endpoint)</label>
<input name="test_path" value="%s">
<label>Payload format</label><select name="payload_format">%s</select>
%s
</details>
<p class="small">Save dabane se sirf upar ki settings save hongi. Key sirf tab badlegi jab
key wale khane me nayi key likhi ho — khaali chhodne par purani key bani rehti hai.
Key server ki <code>data/secrets.env</code> file me jaati hai (kabhi settings/DB/log me nahi)
aur yahan kabhi wapas dikhti nahi.</p>
<button type="submit">Connection save karo</button></form>
<div class="row" style="margin-top:10px">
<form method="post" action="/providers/test" class="inline">%s
<input type="hidden" name="capability" value="%s">
<button class="secondary" type="submit">Test connection</button></form>
%s</div>
<p class="small mut">Test connection sirf ek harmless GET karta hai (models/list type) —
koi generation nahi hoti, koi paisa nahi katata. Green ka matlab hai endpoint ne jawab
diya; generation chalegi hi, ye guarantee nahi hai. Ye adapters real provider accounts
par <strong>UNTESTED</strong> hain.</p>
</div>
""" % (esc(PROVIDER_TITLES[cap][0]), esc(PROVIDER_TITLES[cap][1]),
       conn_pill, key_pill, esc(preset_meta["label"]), esc(cfg.get("base_url") or "—"),
       esc(cfg.get("model") or "—"), esc(preset_meta["base_url_source"]), test_html,
       ctx["csrf_field"], cap, preset_opts, ctx["csrf_field"], cap, preset,
       esc(cfg.get("provider_name") or ""), esc(cfg.get("model") or ""),
       "(env var %s se set hai)" % providers.ENV_KEY_NAMES[cap] if status["key_source"] == "env"
       else "(server ki secrets file me jayegi)",
       "Key set hai — badalne ke liye hi nayi key likho, warna khaali chhodo"
       if status["key_set"] else "Apni API key yahan paste karo",
       "— Custom preset me mandatory" if preset == "custom" else "(optional override)",
       esc(cfg.get("base_url") or ""), auth_opts, esc(cfg.get("auth_header") or ""),
       esc(cfg.get("auth_prefix") or ""), esc(cfg.get("extra_headers") or ""),
       esc(cfg.get("test_path") or ""), fmt_opts, cap_fields,
       ctx["csrf_field"], cap, remove_html)


def pg_providers(ctx):
    cards = "".join(_provider_card(ctx, cap) for cap in providers.CAPABILITIES)
    body = """
<h1>API Providers — apni APIs connect karo</h1>
<p class="mut">Yahan aap apni generation APIs jodte ho: text ke liye OpenAI/Claude,
image ke liye image API, video ke liye Higgsfield/Kling-style API. Known presets me
<strong>base URL aur default model pehle se bhara hai — aapko bas API key paste karni hai</strong>.
Phir Creative Studio ke "Generate with API" buttons inhi APIs se copy, poster, carousel
aur reel banayenge. System khud koi vendor select nahi karta aur koi key apne paas
nahi rakhta — key sirf is server ki <code>data/secrets.env</code> me rehti hai.</p>
<div class="banner warn"><strong>UNTESTED:</strong> ye adapters kisi real provider account
par test nahi hue hain (koi asal key is build ke paas nahi thi). Pehli asal generation
dhyaan se, chhote prompt se test karo. Generation ka kharcha provider ke billing par
jata hai — app me cost hamesha "unknown — provider billing" likha aayega, koi andaz
nahi lagaya jayega.</div>
%s
<div class="card"><h2>Environment variables (dusra tareeka)</h2>
<p class="small">UI ki jagah server ke env me bhi key rakh sakte ho — env wali key
hamesha jeet-ti hai: <code>SH_ADS_TEXT_API_KEY</code>, <code>SH_ADS_IMAGE_API_KEY</code>,
<code>SH_ADS_VIDEO_API_KEY</code>. <code>data/secrets.env</code> ka backup surakshit
jagah rakho — use kabhi git/commit/chat me mat daalo.</p></div>
""" % cards
    return page("API Providers", "/providers", body, ctx["flash"], ctx["conn"])


def pg_planner(ctx):
    products = load_eligibility()
    options = "".join('<option>%s</option>' % esc(p.get("product")) for p in products)
    body = """
<h1>Campaign Planner</h1>
<p class="mut">Plan banana sirf data hai — isse Meta par kuch write nahi hota. Plan
approval queue me jayega; wahan Approve hone ke baad bhi execution sirf PAUSED
objects banayegi (aur DRY_RUN ON ho to MOCK par). Customer aur reseller campaigns
hamesha alag rehte hain.</p>
<div class="card"><form method="post" action="/planner/plan">%s
<label>Product</label><select name="product">%s</select>
<label>Segment</label><select name="segment">
<option>students</option><option>freelancers</option><option>creators</option>
<option>bot owners</option><option>agencies</option></select>
<label>Audience type</label><select name="audience_type">
<option>customers</option><option>resellers</option></select>
<label>Format</label><select name="format"><option>REEL</option><option>IMAGE</option><option>CAROUSEL</option></select>
<label>Daily budget (campaign level — optional, caps ke andar)</label>
<input name="daily_budget" placeholder="Khaali chhodo to budget plan me nahi lagega">
<p class="small">Plan dabane se structure plan (AUD_ANGLE_FORMAT_DATE_VERSION naam ke saath)
bankar neeche dikhega aur ek CAMPAIGN_DRAFT approval queue me chala jayega. Plan ki
copy policy check se guzregi — gate band ho to draft BLOCKED rahega aur execute nahi hoga.</p>
<button type="submit">Plan banao + approval ke liye bhejo</button></form></div>
""" % (ctx["csrf_field"], options)
    return page("Planner", "/planner", body, ctx["flash"], ctx["conn"])


def pg_approvals(ctx):
    conn = ctx["conn"]
    queue = ctx["queue"]
    pending = queue.list_pending()
    all_items = ctx["conn"].execute(
        "SELECT * FROM proposals ORDER BY id DESC LIMIT 50").fetchall()
    cards = []
    for item in pending:
        payload = item["payload"]
        cards.append("""
<div class="card"><h3>#%d · %s</h3>
<p class="small mut">Approve karne se EXACTLY ye hoga: item APPROVED mark hoga. Uske baad
"Execute" dabane par hi — DRY_RUN ke hisaab se MOCK ya (Step 4 ke baad) LIVE — PAUSED
objects banenge. Activation kabhi auto nahi hota.</p>
<pre>%s</pre>
<div class="row">
<form method="post" action="/approvals/approve" class="inline">%s<input type="hidden" name="id" value="%d"><button type="submit">Approve</button></form>
<form method="post" action="/approvals/reject" class="inline">%s<input type="hidden" name="id" value="%d"><button class="secondary" type="submit">Reject</button></form>
</div>
<form method="post" action="/approvals/edit" style="margin-top:10px">%s
<label>Payload edit karo (JSON)</label><textarea name="payload" rows="4">%s</textarea>
<p class="small">Save dabane se sirf draft badlega — kuch execute nahi hoga.</p>
<button class="secondary" type="submit">Edit save karo</button>
<input type="hidden" name="id" value="%d"></form></div>
""" % (item["id"], esc(item["kind"]),
       esc(json.dumps(payload, ensure_ascii=False, indent=1)[:3000]),
       ctx["csrf_field"], item["id"], ctx["csrf_field"], item["id"],
       ctx["csrf_field"], esc(json.dumps(payload, ensure_ascii=False)), item["id"]))
    history = "".join(
        "<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (r["id"], esc(r["kind"]), esc(r["status"]), esc(r["created_at"]),
           '<form method="post" action="/approvals/execute" class="inline">%s'
           '<input type="hidden" name="id" value="%d"><button type="submit">Execute (PAUSED only)</button></form>'
           % (ctx["csrf_field"], r["id"]) if r["status"] == "APPROVED" else "")
        for r in all_items)
    body = """
<h1>Approval Queue</h1>
<p class="mut">Har draft aur har change yahan rukta hai. Bina Approve hue kuch execute
nahi hota — Meta me PAUSED draft banana bhi ek write hai, isliye uske liye bhi
isi queue ki approval lagti hai (brief rule 3).</p>
%s
<div class="card"><h2>History</h2>
<table><tr><th>#</th><th>Kind</th><th>Status</th><th>Created</th><th>Action</th></tr>%s</table>
<p class="small mut">Execute dabane se: kill switch OFF + status APPROVED ho to hi aage
badhega; CAMPAIGN_DRAFT ke liye saare gates (eligibility, claims, destination) phir se
check honge — fail ho to blocked. Result meta_writes + audit log me jayega.</p></div>
""" % ("".join(cards) or '<div class="card">Koi pending item nahi hai.</div>', history)
    return page("Approvals", "/approvals", body, ctx["flash"], conn)


def pg_budget(ctx):
    conn, settings = ctx["conn"], ctx["settings"]
    store.seed_insights(conn=conn)
    rows = store.load_insight_rows(conn)
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
<div class="kpi">%s</div><div class="small mut">0/khaali = cap unset</div></div>
<div class="card"><div class="mut small">Reported spend (MOCK dataset)</div>
<div class="kpi">%s</div><div class="small mut">%s</div></div>
<div class="card"><div class="mut small">PER_CAMPAIGN_CAP / LIFETIME_CAP</div>
<div class="kpi">%s / %s</div><div class="small mut">Settings se badalte hain</div></div>
</div>
<div class="banner warn"><strong>Reporting delay note:</strong> Meta ka reported spend
lag karta hai — caps best-effort hain, overspend ho sakta hai. Isiliye Meta ke apne
native limits (account spend limit, campaign/ad-set caps) bhi lagane hain (Step 2/4
checklist me hai). Breach par system safety-stop propose karta hai aur kabhi
auto-resume nahi karta.</div>
<div class="card"><h2>Budget kis object par hai</h2>
<p class="small mut">Budget hamesha campaign ya ad-set level par hota hai — per-ad
budget kabhi nahi. Optimiser proposal banate waqt asal owner detect karta hai.</p>
<table><tr><th>Budget object</th><th>Owner level</th><th>Current budget</th><th>Spend</th><th>Ad</th></tr>%s</table></div>
<div class="card"><h2>Demo dataset badlo (MOCK)</h2>
<form method="post" action="/budget/dataset">%s
<label>Scenario</label><select name="dataset">
<option>thin_data</option><option>one_big_winner</option><option>all_losers</option>
<option>cheap_junk_leads</option><option>lagged_conversions</option>
<option>spend_breach</option><option>fatigue</option></select>
<p class="small">Dataset badalne se Budget/Reports/Optimiser ke demo numbers badal
jayenge. Ye sirf MOCK data hai — asli data Step 3 ke baad aayega.</p>
<button class="secondary" type="submit">Dataset badlo</button></form>
<form method="post" action="/budget/optimise" style="margin-top:10px">%s
<p class="small">Optimiser chalane se Role 19 abhi ke rows par proposals banakar
approval queue me dalega (PROPOSE — kuch apply nahi hoga). Spend breach mile to
safety stop + kill switch engage ho jayega.</p>
<button type="submit">Optimiser chalao — proposals banao</button></form></div>
""" % (mode_banner(settings), esc(cap if cap else "unset"), esc(total),
       ('<span class="pill bad">CAP BREACH (MOCK)</span>' if cap and total > cap
        else '<span class="pill ok">Cap ke andar / cap unset</span>'),
       esc(settings.get("PER_CAMPAIGN_CAP") or "unset"),
       esc(settings.get("LIFETIME_CAP") or "unset"), per_rows,
       ctx["csrf_field"], ctx["csrf_field"])
    return page("Budget", "/budget", body, ctx["flash"], conn)


def pg_leads(ctx):
    conn = ctx["conn"]
    summary = store.lead_summary(conn)
    rows = conn.execute("SELECT * FROM lead_log ORDER BY id DESC LIMIT 30").fetchall()
    hist = "".join("<tr><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>"
                   % (esc(r["ad_ref"]), esc(r["status"]), r["count"], esc(r["created_at"]))
                   for r in rows)
    body = """
<h1>Lead Quality Log</h1>
<p class="mut">Yahan sirf <strong>counts aur status</strong> store hote hain — koi naam,
phone, email ya chat kabhi nahi. Main metric cost per QUALIFIED lead hai; cost per
enquiry hamesha provisional kahlayega.</p>
<div class="grid">%s</div>
<div class="card"><h2>Entry add karo</h2>
<form method="post" action="/leads/add">%s
<label>Ad reference (ad id / naam)</label><input name="ad_ref" required>
<label>Status</label><select name="status">
<option>enquiry</option><option>real_conversation</option>
<option>reseller_application</option><option>order</option><option>junk</option></select>
<label>Count</label><input name="count" type="number" value="1" min="1">
<p class="small">Add dabane se sirf ye count lead_log me judega (audit entry ke saath).
Koi personal data mat likho — ad_ref me sirf ad ki pehchan rakho.</p>
<button type="submit">Lead count add karo</button></form></div>
<div class="card"><h2>Recent entries</h2>
<table><tr><th>Ad ref</th><th>Status</th><th>Count</th><th>When</th></tr>%s</table></div>
""" % ("".join('<div class="card"><div class="mut small">%s</div><div class="kpi">%d</div></div>'
               % (esc(k), v) for k, v in summary.items()),
       ctx["csrf_field"], hist or '<tr><td colspan="4" class="mut">Abhi koi entry nahi</td></tr>')
    return page("Leads", "/leads", body, ctx["flash"], conn)


def pg_reports(ctx):
    conn = ctx["conn"]
    saved = store.list_reports(conn)
    hist = "".join("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                   % (r["id"], esc(r["kind"]), esc(r["language"]), esc(r["created_at"]))
                   for r in saved)
    latest = saved[0]["body"] if saved else ""
    body = """
<h1>Reports</h1>
<p class="mut">Daily report: spend, enquiries, cost per enquiry (provisional) aur per
qualified lead, data-quality notes, top/bottom 3, pending proposals. Weekly: winning
angle/format, next test, quality results, budget sifarish, trend notes. Bhasha
settings ke LANGUAGES se aati hai (Hinglish default).</p>
<div class="row">
<form method="post" action="/reports/generate" class="inline">%s
<input type="hidden" name="kind" value="daily"><button type="submit">Daily report banao</button></form>
<form method="post" action="/reports/generate" class="inline">%s
<input type="hidden" name="kind" value="weekly"><button class="secondary" type="submit">Weekly report banao</button></form>
</div>
<p class="small mut">Report banao dabane se report generate hokar neeche save ho jayegi.
Numbers abhi MOCK dataset ke hain.</p>
%s
<div class="card"><h2>Saved reports</h2>
<table><tr><th>#</th><th>Kind</th><th>Language</th><th>When</th></tr>%s</table></div>
""" % (ctx["csrf_field"], ctx["csrf_field"],
       ('<div class="card"><h2>Latest report</h2><pre>%s</pre></div>' % esc(latest)) if latest else "",
       hist or '<tr><td colspan="4" class="mut">Abhi koi report save nahi hai</td></tr>')
    return page("Reports", "/reports", body, ctx["flash"], conn)


def pg_trends(ctx):
    items = ""
    for t in trends_mod.TREND_ITEMS:
        pill = ('<span class="pill ok">VERIFIED</span>' if t["verified"]
                else '<span class="pill warn">UNVERIFIED</span>')
        items += ('<tr><td><a href="%s" target="_blank" rel="noopener">%s</a></td>'
                  '<td>%s</td><td>%s</td><td class="small">%s</td></tr>'
                  % (esc(t["url"]), esc(t["title"]), esc(t["date"]), pill, esc(t["note"])))
    body = """
<h1>Trend Watch — sirf official sources</h1>
<p class="mut">Har item ke saath URL aur date hai. Jo item is build me live fetch nahi
hua wo <strong>UNVERIFIED</strong> hai — pehle official page par khud check karo, phir
hi koi faisla. Koi trend strategy ko apne aap nahi badalta; badlav hamesha owner ke
faisle se hoga.</p>
<div class="card"><table><tr><th>Item</th><th>Date</th><th>Status</th><th>Note</th></tr>%s</table></div>
<div class="card"><h2>PRACTICES note</h2>
<p class="small">Objectives, structure, targeting/broad, placements, learning phase,
budget badlav aur attribution par official guidance PRACTICES.md me hai (repo ke
saath) — uske kai points abhi UNVERIFIED hain aur Step 2 me official docs ke saath
verify honge. Tab tak koi bhi number default ke roop me use nahi hota.</p></div>
""" % items
    return page("Trends", "/trends", body, ctx["flash"], ctx["conn"])


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
<p class="mut">Har proposal, approval aur write yahan record hota hai — secrets aur
personal data logs me jaane se pehle redact ho jate hain (email/phone/token patterns).</p>
<div class="card"><h2>Meta writes</h2>
<table><tr><th>#</th><th>Mode</th><th>Status</th><th>When</th></tr>%s</table>
<p class="small mut">Rollback: kisi bhi write ka rollback fresh state padhkar, diff
dikha kar aur owner ki alag approval lekar hi hota hai — CLI/library
(<code>app.rollback</code>) se, kabhi auto nahi. Rollback kharch wapas nahi karta.</p></div>
<div class="card"><h2>Errors</h2>
<table><tr><th>Source</th><th>Message (redacted)</th><th>When</th></tr>%s</table></div>
<div class="card"><h2>Audit log (latest 60)</h2>
<table><tr><th>#</th><th>Event</th><th>Detail (redacted)</th><th>When</th></tr>%s</table></div>
""" % (w_html or '<tr><td colspan="4" class="mut">Abhi koi write nahi hua</td></tr>',
       e_html or '<tr><td colspan="3" class="mut">Koi error record nahi hai</td></tr>',
       a_html)
    return page("Errors & Audit", "/audit", body, ctx["flash"], conn)


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
    return "/login?msg=" + urllib.parse.quote("Galat password — dobara try karo.")


def post_setup(ctx, form):
    conn = ctx["conn"]
    if auth.owner_exists(conn):
        return "/login?msg=" + urllib.parse.quote("Owner pehle se set hai — setup band hai.")
    try:
        auth.create_owner(form.get("password", ""), conn)
    except ValueError as e:
        return "/setup?msg=" + urllib.parse.quote(str(e))
    token, _csrf = auth.create_session(conn)
    ctx["set_cookie"] = token
    return "/?msg=" + urllib.parse.quote("Owner set ho gaya. Dashboard ready hai.")


def post_settings(ctx, form):
    settings = dict(ctx["settings"])
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
    return "Settings save ho gaye."


def post_killswitch(ctx, form):
    queue = ctx["queue"]
    if form.get("action") == "on":
        from .mock_meta import MockMetaClient
        queue.engage_kill_switch("owner pressed kill switch in UI", mock_client=MockMetaClient())
        return "Kill switch ON — automation band, execution blocked. Auto-resume kabhi nahi hoga."
    queue.conn.execute("INSERT OR REPLACE INTO kv (key, value) VALUES ('kill_switch', '0')")
    queue.conn.commit()
    audit(ctx["conn"], "kill_switch_released", "Owner released the kill switch manually.")
    return "Kill switch OFF — owner ne khud release kiya. AUTOMATION_MODE pehle jaisa hi rahega jo settings me hai."


def post_eligibility_confirm(ctx, form):
    product = form.get("product", "")
    proof = (form.get("proof_note") or "").strip()
    tdate = (form.get("terms_checked_date") or "").strip()
    if not proof or not tdate:
        return "Refused: proof note aur terms-checked date dono zaroori hain — bina inke confirm nahi hoga."
    products = load_eligibility()
    for p in products:
        if p.get("product") == product:
            p["supplier"] = (form.get("supplier") or "").strip()
            p["proof_note"] = proof
            p["terms_checked_date"] = tdate
            p["resale_permission_confirmed"] = True
    save_eligibility(products)
    audit(ctx["conn"], "eligibility_confirmed", "product=%s (proof recorded)" % product)
    return "%s ki resale permission confirm ho gayi (proof + date ke saath)." % product


def post_eligibility_unconfirm(ctx, form):
    product = form.get("product", "")
    products = load_eligibility()
    for p in products:
        if p.get("product") == product:
            p["resale_permission_confirmed"] = False
    save_eligibility(products)
    audit(ctx["conn"], "eligibility_unconfirmed", "product=%s" % product)
    return "%s unconfirm ho gaya — uske ads phir se blocked hain." % product


def post_creative_generate(ctx, form):
    conn = ctx["conn"]
    result = creative_mod.generate_creative_set(
        form.get("product", ""), form.get("segment", "students"), settings=ctx["settings"])
    cid = store.save_creative(result["product"], result["segment"], "creative_set",
                              result, result["policy"], conn)
    from .common import log_role_run
    log_role_run(conn, "06_angle_generator", "done", {"angles_for": result["segment"]})
    log_role_run(conn, "07_copywriter", "done", result["copy"])
    log_role_run(conn, "10_policy_checker", "done", result["policy"])
    if result["policy"]["allowed"]:
        return "Creative set #%d save ho gaya aur policy PASS hai. Planner se ise approval ke liye bhej sakte ho." % cid
    return ("Creative set #%d save ho gaya lekin policy BLOCKED hai: %s"
            % (cid, "; ".join(result["policy"]["reasons"])))


def post_policycheck(ctx, form):
    result = policy_checker.check_claims(form.get("text", ""))
    if result["allowed"]:
        return "Policy check: koi banned claim nahi mila. (Sirf claims scan hua — eligibility/destination alag gates hain.)"
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
    return "Asset register ho gaya — visual check PENDING hai, tab tak approval queue me nahi ja sakta."


def post_visualcheck(ctx, form):
    conn = ctx["conn"]
    if not all(form.get(k) for k in ("c1", "c2", "c3", "c4")):
        return "Refused: visual checklist ke saare 4 item tick hone chahiye."
    cur = conn.execute(
        "UPDATE assets SET visual_check = 'PASS' WHERE filename = ?",
        (form.get("filename", ""),))
    conn.commit()
    if cur.rowcount == 0:
        return "Is naam ka koi asset register nahi hai — pehle register karo."
    audit(conn, "asset_visual_check_pass", "file=%s" % form.get("filename", ""))
    return "Visual check PASS mark ho gaya."


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
    return ("%s connection save ho gaya. Key: %s. Base URL: %s · Model: %s"
            % (cap, "set hai" if status["key_set"] else "set NAHI hai",
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
    return ("%s par preset '%s' lag gaya — base URL %s, model %s pre-filled hai. "
            "Ab bas API key paste karke save karo."
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
    return "%s ki API key secrets file se hat gayi." % cap


def post_api_copy(ctx, form):
    conn = ctx["conn"]
    try:
        result = creative_mod.generate_copy_with_api(
            form.get("product", ""), form.get("segment", "students"),
            settings=ctx["settings"], instruction=form.get("instruction", ""))
    except providers.ProviderError as e:
        log_error(conn, "providers:text", str(e))
        return "Text API error: %s" % e
    kind = "api_copy" if result.get("source") == "api" else "creative_set"
    cid = store.save_creative(result["product"], result["segment"], kind,
                              result, result["policy"], conn)
    audit(conn, "creative_generated",
          "id=%s source=%s provider=%s model=%s request=%s cost=%s"
          % (cid, result.get("source"), result.get("provider", "-"),
             result.get("model", "-"), result.get("request_id", "-"),
             providers.COST_NOTE))
    if result.get("source") != "api":
        return ("Creative set #%d TEMPLATE se bana — %s. Policy: %s"
                % (cid, result["label"],
                   "PASS" if result["policy"]["allowed"]
                   else "BLOCKED — " + "; ".join(result["policy"]["reasons"])))
    if result["policy"]["allowed"]:
        return ("API copy #%d ban gayi (%s, %s) aur policy PASS hai. Cost: %s"
                % (cid, result.get("provider"), result.get("model"), providers.COST_NOTE))
    return ("API copy #%d ban gayi lekin policy BLOCKED hai: %s"
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
    return ("Asset %s ban gaya (%s, %s) — visual check PENDING hai; checklist "
            "PASS kiye bina approval queue me nahi jayega. Cost: %s"
            % (meta["filename"], meta["provider"], meta["model"], providers.COST_NOTE))


def post_api_image(ctx, form):
    prompt = (form.get("prompt") or "").strip()
    if not prompt:
        return "Refused: image prompt khaali hai."
    if not providers.is_configured("image"):
        return "API not connected — pehle API Providers page se Image API connect karo."
    try:
        meta = creative_mod.generate_poster_image(prompt)
    except providers.ProviderError as e:
        log_error(ctx["conn"], "providers:image", str(e))
        return "Image API error: %s" % e
    return _register_generated(ctx, meta, "image", prompt, "api-image")


def post_api_carousel(ctx, form):
    slides = [s.strip() for s in (form.get("slides") or "").splitlines() if s.strip()]
    if not slides:
        return "Refused: kam se kam ek slide brief likho."
    if not providers.is_configured("image"):
        return "API not connected — pehle API Providers page se Image API connect karo."
    try:
        metas = creative_mod.generate_carousel_images(slides)
    except providers.ProviderError as e:
        log_error(ctx["conn"], "providers:image", str(e))
        return "Image API error: %s" % e
    msgs = []
    for i, meta in enumerate(metas, 1):
        msgs.append(_register_generated(ctx, meta, "image", slides[i - 1],
                                        "api-carousel slide %d" % i))
    return "Carousel ke %d slides ban gaye. " % len(metas) + " | ".join(msgs)


def post_api_video(ctx, form):
    prompt = (form.get("prompt") or "").strip()
    if not prompt:
        return "Refused: video prompt khaali hai."
    if not providers.is_configured("video"):
        return "API not connected — pehle API Providers page se Video API connect karo."
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
    return ("Video job submit ho gaya — job id %s (%s, %s). Neeche Video jobs table me "
            "'Status check karo' se poll karo. Cost: %s"
            % (out["job_id"], out["provider"], out["model"], providers.COST_NOTE))


def post_api_video_check(ctx, form):
    conn = ctx["conn"]
    job_id = form.get("job_id", "")
    job = next((j for j in store.list_video_jobs(conn)
                if str(j.get("job_id")) == str(job_id)), None)
    if job is None:
        return "Is id ka koi video job record nahi hai."
    if job.get("status") == "done":
        return "Ye job pehle hi done hai — asset register ho chuka hai."
    try:
        out = creative_mod.poll_reel_video(job_id)
    except providers.ProviderError as e:
        log_error(conn, "providers:video", str(e))
        return "Video API error: %s" % e
    if out["state"] == "pending":
        store.update_video_job(job_id, {"status": "pending: %s" % out["raw_status"]}, conn)
        return "Job %s abhi processing me hai (status: %s). Thodi der baad phir check karo." \
            % (job_id, out["raw_status"])
    if out["state"] == "failed":
        store.update_video_job(job_id, {"status": "failed"}, conn)
        audit(conn, "video_job_failed", "job=%s" % job_id)
        return "Job %s FAILED ho gaya provider par. Prompt badalkar dobara try karo." % job_id
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
    plan = planner_mod.plan_structure(
        product, segment, form.get("audience_type", "customers"),
        form.get("format", "REEL"), 1, form.get("daily_budget", ""))
    creative = creative_mod.generate_creative_set(product, segment, settings=ctx["settings"])
    draft = {
        "kind": "CAMPAIGN_DRAFT",
        "product": product,
        "campaign_name": plan["campaign_name"],
        "adset_name": plan["ad_sets"][0]["name"],
        "ad_name": plan["ad_sets"][0]["ads"][0]["ad_name"],
        "creative_text": creative["copy"]["hinglish"]["headline"] + " "
                         + creative["copy"]["hinglish"]["text"],
        "daily_budget": form.get("daily_budget", ""),
        "plan": plan,
        "policy_preview": creative["policy"],
        "cost_effect": "Create hone par objects PAUSED rahenge — spend tabhi shuru "
                       "hoga jab activation ki ALAG approval milegi (is build me "
                       "activation ka koi automatic path nahi hai).",
    }
    item_id = ctx["queue"].add_item("CAMPAIGN_DRAFT", draft)
    from .common import log_role_run
    log_role_run(conn, "11_structure_planner", "done", plan)
    return ("Plan ban gaya aur CAMPAIGN_DRAFT #%d approval queue me gaya. "
            "Policy preview: %s" % (item_id, "PASS" if creative["policy"]["allowed"]
                                    else "BLOCKED — " + "; ".join(creative["policy"]["reasons"])))


def post_approval_action(ctx, form, action):
    queue = ctx["queue"]
    item_id = int(form.get("id", "0"))
    if action == "approve":
        if queue.kill_switch_active():
            return "Kill switch ON hai — approvals blocked hain."
        queue.approve(item_id)
        return "Item #%d APPROVED. Execute alag step hai (History table se) — activation kabhi auto nahi." % item_id
    if action == "reject":
        queue.reject(item_id)
        return "Item #%d REJECTED." % item_id
    if action == "edit":
        try:
            payload = json.loads(form.get("payload", "{}"))
        except ValueError:
            return "Edit refused: payload valid JSON nahi hai."
        queue.edit_item(item_id, payload)
        return "Item #%d ka draft edit save ho gaya." % item_id
    if action == "execute":
        result = execute_approved_item(item_id, ctx["settings"], conn=ctx["conn"], queue=queue)
        if result.get("ok"):
            return "Execute ho gaya (%s): %s" % (result.get("mode"), result.get("note"))
        return "Execute BLOCKED: %s %s" % (result.get("blocked", ""),
                                           "; ".join(result.get("reasons", [])))
    return "Unknown action."


def post_budget_dataset(ctx, form):
    n = store.replace_insights(form.get("dataset", "one_big_winner"), ctx["conn"])
    return "MOCK dataset badal gaya — ab %d rows active hain." % n


def post_budget_optimise(ctx, form):
    from . import jobs
    rc = jobs.cmd_optimise(None)
    return "Optimiser chala (rc=%s). Proposals approval queue me dekho." % rc


def post_leads_add(ctx, form):
    try:
        store.add_lead(form.get("ad_ref", ""), form.get("status", "enquiry"),
                       int(form.get("count", "1")), ctx["conn"])
    except ValueError as e:
        return "Refused: %s" % e
    return "Lead count add ho gaya (sirf count/status — koi personal data store nahi hua)."


def post_reports_generate(ctx, form):
    from . import jobs
    kind = form.get("kind", "daily")
    jobs._report(None, kind)
    return "%s report generate hokar save ho gayi." % kind.capitalize()


def post_roles_run(ctx, form):
    conn = ctx["conn"]
    from .common import log_role_run
    settings = ctx["settings"]
    rows = store.load_insight_rows(conn) or store.seed_insights(conn=conn) \
        and store.load_insight_rows(conn)
    ran = []

    def run(result):
        log_role_run(conn, result["role"], "done", result["output"])
        ran.append(result["role"])

    run(roles.role_01_audience_research())
    run(roles.role_02_competitor_watch())
    run(roles.role_03_trend_analysis())
    run(roles.role_04_funnel_strategy())
    run(roles.role_05_budget_planning(settings))
    angles = roles.role_06_angle_generator("students")["output"]["angles"]
    run(roles.role_06_angle_generator("students"))
    run(roles.role_07_copywriter(angles[0]))
    run(roles.role_08_visual_poster_brief(angles[0]))
    run(roles.role_09_reel_script(angles[0]))
    run(roles.role_11_structure_planner())
    run(roles.role_12_targeting_planner())
    run(roles.role_15_account_health_monitor())
    run(roles.role_16_data_collector())
    run(roles.role_17_lead_quality_tracker(rows))
    run(roles.role_18_creative_analyst(rows))
    run(roles.role_20_reporter(rows, [], (settings.get("LANGUAGES") or ["Hinglish"])[0]))
    audit(conn, "roles_manual_run", "roles=%s" % ",".join(ran))
    return "%d roles MOCK data par chal gaye — outputs role_runs me logged hain." % len(ran)


POST_ROUTES = {
    "/settings": (post_settings, "/settings"),
    "/killswitch": (post_killswitch, "/settings"),
    "/eligibility/confirm": (post_eligibility_confirm, "/eligibility"),
    "/eligibility/unconfirm": (post_eligibility_unconfirm, "/eligibility"),
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
    "/leads/add": (post_leads_add, "/leads"),
    "/reports/generate": (post_reports_generate, "/reports"),
    "/roles/run": (post_roles_run, "/roles"),
    "/budget/dataset": (post_budget_dataset, "/budget"),
    "/budget/optimise": (post_budget_optimise, "/approvals"),
}

GET_ROUTES = {
    "/": pg_today, "/connect": pg_connect, "/roles": pg_roles,
    "/settings": pg_settings, "/eligibility": pg_eligibility,
    "/creative": pg_creative, "/providers": pg_providers,
    "/planner": pg_planner,
    "/approvals": pg_approvals, "/budget": pg_budget, "/leads": pg_leads,
    "/reports": pg_reports, "/trends": pg_trends, "/audit": pg_audit,
}


def login_page(msg=""):
    body = """<div class="card"><h1>SH Ads Desk — Owner Login</h1>
<p class="mut">Single-owner app. Password wahi jo owner ne setup/env me rakha tha —
password kabhi chat ya code me nahi hota.</p>
%s<form method="post" action="/login">
<label>Password</label><input type="password" name="password" required>
<button type="submit" style="width:100%%">Login</button></form>
<p class="small mut" style="margin-top:12px">Pehli baar? Agar owner abhi set nahi hai to
<a href="/setup">first-run setup</a> par jao.</p></div>""" % (
        ('<div class="flash">%s</div>' % esc(msg)) if msg else "")
    return simple_page("Login", body)


def setup_page(msg=""):
    body = """<div class="card"><h1>First-run Setup</h1>
<p class="mut">Owner password set karo (kam se kam 10 characters). Ye sirf ek baar
hota hai — hash bankar local database me rahega, password khud kabhi store nahi hota.
Iske baad setup hamesha ke liye band ho jayega.</p>
%s<form method="post" action="/setup">
<label>Naya owner password</label><input type="password" name="password" required>
<button type="submit" style="width:100%%">Owner set karo</button></form></div>""" % (
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
                                               "<p>File nahi mila.</p></div>"), status=404)
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
        return {
            "conn": conn,
            "settings": load_settings(),
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
                                               "<p>Page nahi mila.</p></div>"), status=404)
        ctx = self._ctx(conn, session, flash=msg)
        ctx["queue"].conn = conn
        try:
            return self._send_html(handler(ctx))
        except Exception as e:  # record redacted, show plain message
            log_error(conn, "web:" + path, str(e))
            return self._send_html(simple_page(
                "Error", "<div class='card'><h1>Kuch gadbad hui</h1><p>%s</p>"
                         "<p class='small mut'>Detail Errors &amp; Audit page me logged hai (redacted).</p></div>"
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
                "Blocked", "<div class='card'><h1>CSRF check fail</h1>"
                           "<p>Form dobara kholkar try karo.</p></div>"), status=403)
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
            msg = "Error: %s (detail Errors & Audit me hai)" % redact(str(e))
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
    print("First run: kholo /setup par owner password set karo (ya .env me OWNER_PASSWORD_HASH rakho).")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
