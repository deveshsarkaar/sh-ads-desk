# META_ACCESS.md — SH Ads Desk Step 2

**What Meta access this system needs, verified from Meta's official
documentation on 2026-11-16.** Every fact carries its source URL and the
date read. Evidence labels work exactly as in PRACTICES.md:

- **[DIRECT]** — official page loaded and read first-hand in this pass.
- **[CORROBORATED]** — official page content confirmed via multiple
  independent readings; the page itself returned HTTP 403 to this
  environment.
- **[UNVERIFIED]** — not established; listed at the bottom, never assumed.

**Bottom line first:** for managing **only the owner's own ad account**,
Meta's docs say **standard access to `ads_read` and `ads_management` is
sufficient**. Advanced access and App Review are for apps that manage
**other people's** ad accounts. SH Ads Desk is a single-owner system, so
it starts read-only on standard access and adds write permission only at
Step 4, with the owner's approval — exactly the brief's plan.

---

## 1. Permissions — what each objective needs

### The dashboard's required set (all Marketing API use cases)

When a Marketing API use case is added to an app, Meta's dashboard
requires this set for **all three** use cases ("Capture & manage ad
leads", "Create & manage ads", "Measure ad performance data"):

- Feature: **Ads Management Standard Access** (now labelled the
  **Marketing API Access Tier** feature — see §2) — required, cannot be
  removed.
- Permissions: **`ads_management`**, **`ads_read`**,
  **`business_management`**, **`pages_read_engagement`**,
  **`pages_show_list`**, **`public_profile`** — all required, cannot be
  removed.
- Products added automatically: **Facebook Login for Business** and
  **Webhooks**.

[DIRECT — https://developers.facebook.com/documentation/development/create-an-app/marketing-api-use-cases,
page updated 2025-09-09, read 2026-11-16]

### What to actually request, per goal (Meta's own use-case table)

| Goal | Permission to request | Feature |
|---|---|---|
| Read ad reports (Insights) on accounts you own / have access to | `ads_read` | Marketing API Access Tier |
| Read **and manage** ads on accounts you own / have access to | `ads_management` | Marketing API Access Tier |
| Both, across different client sets | `ads_management` **and** `ads_read` | Marketing API Access Tier |

[DIRECT — https://developers.facebook.com/documentation/ads-commerce/marketing-api/get-started/authorization,
page updated 2026-05-05, read 2026-11-16]

### Per objective for Software Hub

- **Traffic / Sales (website)** — the "Create & manage ads" use case.
  No extra permission beyond the required set above. (Measuring website
  conversions additionally needs a **Pixel / Conversions API dataset**
  connected to the ad account — that is an asset setup in Business
  Settings, not an API permission.)
- **Leads via Instant Forms** — the "Capture & manage ad leads" use
  case, which additionally **requires `leads_retrieval`** (to download
  the leads people submit) and **`page_manage_ads`** (required for this
  use case; optional for "Create & manage ads"). Instant Forms live on
  a **Facebook Page**, and the form needs a **privacy policy URL** —
  an owner-supplied page on softwarehub.tech, never invented by the
  system.
  [DIRECT for the permission requirements — Use Cases page above;
  CORROBORATED for the Page/privacy-policy requirement — Meta Business
  Help Center, Lead Ads guidance, 2026-11-16]
- **Read-only reporting (Step 3)** — the "Measure ad performance data"
  use case with `ads_read`. This is the only thing connected in Step 3.

## 2. Access tiers, App Review, business verification

### Marketing API Access Tier (renamed May 2026)

Meta renamed the tiers: **"Standard Access" → "Limited Access"** and
**"Advanced Access" → "Full Access"**. The permission identifiers did
not change and existing levels carry over automatically.

| | **Limited Access** (default) | **Full Access** (after App Review) |
|---|---|---|
| How to get | Automatic when the Marketing API product is added to the app | "+Upgrade" in App Dashboard, after meeting the requirements below |
| Rate limits | **Heavily** rate-limited per ad account — *for development only, not for production apps* | Lightly rate-limited per ad account |
| Ad accounts | Unlimited; app admins/developers can call on behalf of account admins/advertisers | Unlimited, given `ads_read`/`ads_management` from the account |
| Business Manager APIs | Limited; **no** Business Manager access to manage ad accounts, user permissions and Pages | All Business Manager and Catalog APIs |
| System users | 1 system user + 1 admin system user | 10 system users + 1 admin system user |
| Page creation via API | Not possible | Not possible |

**Full Access requirements:** at least **500 successful Marketing API
calls in the past 15 days** (threshold reduced from 1,500) **and** an
error rate **below 15%** across the last 500 calls.

[DIRECT — Authorization page above, read 2026-11-16]

**What this means for SH Ads Desk:** start on Limited Access. Its rate
limits are small but real (see §3) — enough for Step 3 read-only
comparisons and Step 4's first PAUSED drafts on the owner's own account.
Full Access is only worth pursuing if call volume grows; it is *not* a
prerequisite for managing the owner's own account.

### App Review — when it applies

- **Standard access** is what an app gets for permissions/features by
  default; **advanced access** must be approved through **App Review**,
  per permission/feature.
- The deciding question is whose data the app touches: *"If your app is
  only managing your ad account, standard access to the `ads_read` and
  `ads_management` permissions are sufficient. If your app is managing
  other people's ad accounts, you need advanced access."*
- Publishing the app is likewise only required if the app will access
  data the owner **doesn't own or manage** (or uses a product that
  requires publishing, such as Webhooks subscriptions).

[DIRECT — Authorization page and Use Cases page above, read 2026-11-16]

### Business verification — when it applies

- Meta describes business verification as required **"if your app will
  access sensitive data"** — it is not stated as a blanket requirement
  for standard-access use on your own account.
  [DIRECT — Authorization page]
- Separately, for the business portfolio connected to the app: *"You can
  add an unverified business portfolio however it must be verified
  before you can run ads."*
  [DIRECT — Use Cases page]
- Honest boundary: the docs read in this pass do **not** state that
  business verification is required for read-only `ads_read` standard
  access on the owner's own account, so this file does not claim it is.
  Expect verification to become relevant before ads actually run
  through the connected portfolio, and complete it on Meta's screens
  when Meta asks — never work around it.

## 3. Rate limits

Rate limiting is **per ad account**. Two meters apply at once:

**Meter 1 — ad-account score.** A read call costs **1 point**, a write
call **3 points**. Max score: **60 on Limited Access** (blocked for
300 seconds when hit) vs **9,000 on Full Access** (blocked 60 seconds).

**Meter 2 — hourly Business Use Case (BUC) quotas**, per ad account per
rolling hour:

| Use case | Limited Access | Full Access |
|---|---|---|
| `ads_management` | 300 + 40 × active ads | 100,000 + 40 × active ads |
| `ads_insights` | 600 + 400 × active ads − 0.001 × user errors | 190,000 + 400 × active ads − 0.001 × user errors |

**Error codes:** `80004` = ads-management BUC quota used up; `80000` =
Ads Insights BUC quota; `17` / `613` = ad-account limits (identify the
exact limit by subcode). Usage is reported in response headers
(`X-Ad-Account-Usage`, `X-Business-Use-Case-Usage`,
`X-FB-Ads-Insights-Throttle`), including an estimated time to regain
access. Correct behaviour: **back off and wait** — never hammer through
a throttle.

[CORROBORATED — Meta for Developers, "Marketing API Rate Limiting"
(developers.facebook.com), page updated 2026-08-19; figures identical
across multiple independent readings of that page, re-checked
2026-11-16. The page itself returns 403 to this environment.]

**Code note (Step 3 follow-up, not changed in Step 2):**
`app/meta_client.py` already backs off on HTTP 429 and codes
17/32/613/80004. The verified list above adds **`80000`** (Insights BUC)
— worth adding to `RATE_LIMIT_CODES` when Step 3 wires the live client,
so Insights pulls back off instead of retrying into the wall.

## 4. Page / Instagram / identity — per objective and placement

No blanket rules. What the docs actually say:

- **A Facebook Page is the identity anchor** for Ads Manager /
  Marketing API ads: the ad is built as a Page post (`page_id` in the
  creative). For SH Ads Desk's routes, a Page is required.
- **An Instagram account is NOT required to advertise on Instagram
  placements.** With no Instagram account connected, the **Facebook
  Page represents the business on Instagram** and the Page's details
  are shown in place of an Instagram profile.
- **To have the ad appear from an Instagram handle**, connect an
  **Instagram professional account** (business or creator) and select
  it at the **ad level** under Identity; via the API, `instagram_user_id`
  is supplied **alongside** `page_id`, not instead of it. A *personal*
  Instagram account cannot be an ad identity.
- **Per objective:** Instant-Form **Leads** ads need the Page (the form
  is a Page asset). **Messaging** destinations need the matching asset
  (Page for Messenger, Instagram professional account for Instagram
  Direct, a WhatsApp business number for WhatsApp). **Sales/Traffic**
  to a website need only the Page identity (+ a dataset for conversion
  optimisation).
- **Exception that does not apply to us:** a business boosting a post
  from an Instagram professional account *for the very first time* can
  do so without connecting an ad account or Page. That is an in-app
  boost route, not Ads Manager / API, and SH Ads Desk never uses it.

[CORROBORATED — Meta Business Help Center and Instagram Help Center,
advertising-identity guidance, read via multiple independent readings,
2026-11-16]

## 5. OAuth user token vs system-user token

- **OAuth / user tokens** come from **Facebook Login for Business**:
  the owner signs in on Meta's own screens and grants the app its
  permissions (`scope=ads_management` etc.). This is the brief's
  least-privilege first path, and the only one SH Ads Desk uses until
  Step 5. Tokens from the dashboard/Quickstart flow are time-limited —
  Meta's Quickstart-generated token is stated as **valid for 2 months**
  — so a user token needs periodic owner renewal.
- **System-user tokens** are Meta's route for **continuous access to
  business assets**: Facebook Login for Business configurations can
  request a system-user access token instead of a user token; Meta
  describes this as the option to use *"if this configuration needs
  continuous access to business assets, such as Facebook Pages, ad
  accounts or Instagram accounts"*, and it requires signing in with a
  **business portfolio**. Tier capacity: 1 system user (+1 admin) on
  Limited Access, 10 (+1 admin) on Full Access.
- **Guidance for this system:** Step 3–4 → owner-generated **user
  token**, stored only in the server `.env` (`META_ACCESS_TOKEN`),
  never typed into the app or sent in chat. Step 5 (unattended
  scheduled jobs) → **only if** token expiry becomes a real problem,
  create **one system user** in the owner's Business Settings, assign
  it **only his ad account and Page**, and use its token the same way.
  Scope never widens beyond his own assets.

[DIRECT — Use Cases page (Login for Business configurations, Quickstart
token validity) and Authorization page (system-user capacity), read
2026-11-16]

## 6. Fallback: manual Ads Manager

Everything in the brief's process — research notes aside — can be done
by hand in **Ads Manager** with the same approval rules: drafts stay
drafts until the owner approves them, activation is a separate click by
the owner, and Meta's native limits (account spending limit, campaign
spend caps) are set in Ads Manager/Business Settings. Meta also offers
**sandbox ad accounts** in the developer Quickstart for practising API
ad creation with mock data and **no charges and no payment method** —
a safe Step 3 companion if the owner wants it.
[DIRECT for sandbox accounts — Use Cases page, read 2026-11-16;
CORROBORATED for Ads Manager parity — Meta Business Help Center]

---

## UNVERIFIED — not established in this pass

1. The **rate-limiting page's own text** (developers.facebook.com) —
   403 here; §3's figures are corroborated from that official page via
   multiple independent readings, not read first-hand.
2. Whether Meta triggers **business verification** for own-account
   `ads_read` standard access in practice — the docs read do not state
   it either way; not assumed.
3. A per-placement **identity matrix** beyond §4 (e.g. Threads profile
   requirements for Threads placements) — not covered by the pages
   read; check before any Step 4 draft that uses a new placement.
4. Long-lived user-token mechanics beyond the Quickstart statement
   (exact renewal flow in the app dashboard) — to be confirmed on the
   owner's own screens in Step 3.

---
*Step 2 research pass, 2026-11-16. Primary sources loaded first-hand:
Meta for Developers — Authorization; Marketing API Use Cases.*
