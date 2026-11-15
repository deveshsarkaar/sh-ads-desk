# PRACTICES.md — SH Ads Desk

**Status: Step 2 — verified 2026-11-16.** Every point below carries its
source and the date it was read (2026-11-16). Nothing here is a hardcoded
default: thresholds still live in the owner's settings, exactly as the
brief requires. Where Meta publishes no number, this file says so instead
of inventing one.

## How to read the evidence labels

This build environment can load some Meta pages and not others
(developers.facebook.com and facebook.com return HTTP 403 to automated
readers on many paths). Each point is labelled honestly:

- **[DIRECT]** — the official Meta page was loaded and read in this
  session (2026-11-16).
- **[CORROBORATED]** — the official Meta page's content is confirmed by
  multiple independent sources that read that page; the page itself
  returned 403 here, so the wording was not re-read first-hand.
- **[UNVERIFIED]** — could not be established from an official source.
  These points sit in the UNVERIFIED section at the bottom and must not
  drive any decision until they are read on Meta's own pages.

---

## 1. Objectives

- Meta offers **six campaign objectives** (the "ODAX" set): **Awareness,
  Traffic, Engagement, Leads, App promotion, Sales**. The objective is
  chosen at the **campaign** level and **cannot be changed after the
  campaign is created** — changing objective means building a new
  campaign. Meta's own guidance is to pick the objective that matches the
  outcome you actually want, not the cheapest metric.
  [CORROBORATED — Meta Business Help Center, advertising-objectives
  guidance (facebook.com/business/help), read via multiple independent
  readings, 2026-11-16]
- For Software Hub this maps to: **Leads** (enquiries / reseller
  applications via Instant Forms, messages or website), **Sales**
  (website purchases with a conversion event), **Traffic** (visits to
  softwarehub.tech). The brief's main metric — cost per *qualified* lead —
  is a reporting layer on top of these, not an objective.

## 2. Campaign structure

- Three levels: **Campaign** (objective; optionally the budget, see §7)
  → **Ad set** (conversion location, optimisation event, audience,
  placements, budget, schedule, attribution setting) → **Ad** (format,
  creative, primary text, headline, CTA, destination, and the Page /
  Instagram identity).
  [CORROBORATED — Meta Business Help Center, campaign-structure guidance,
  2026-11-16]
- The brief's process fits this directly: separate campaigns for
  customers and for resellers, a small number of ad sets per campaign,
  3–5 ads with distinct angles per ad set. Fewer, stronger ad sets also
  serve the learning phase (§4): each ad set needs its own optimisation
  events, so splitting budget across too many ad sets starves all of
  them.

## 3. Targeting: broad / Advantage+ vs detailed

- **Advantage+ audience** (ad-set level) uses Meta's AI to find people
  from signals such as past conversions, pixel data and interactions
  with earlier ads. Advertiser selections act as **suggestions**;
  hard limits are applied only through audience **controls** (e.g.
  location, minimum age, exclusions where available).
  [CORROBORATED — Meta Business Help Center, "About Advantage+
  audience", 2026-11-16]
- Meta treats a plain **broad audience** setup as equivalent to
  Advantage+ audience in its own comparisons, and recommends **A/B
  testing Advantage+ audience for almost all campaign types — except
  retargeting campaigns**, where it does not recommend it.
  [CORROBORATED — same source]
- Practical reading for this system: detailed interest stacks are a
  suggestion layer now, not the primary lever. The Targeting Planner
  role should default to broad/Advantage+ with location + language
  controls (Hinglish/English, per settings) and treat interests as
  suggestions — but the final choice per campaign stays the owner's,
  made in the approval queue.

## 4. Learning phase — and what resets it

- After an ad set is created or significantly edited, it enters the
  **learning phase** while Meta's delivery system explores. During
  learning, performance is **less stable and cost per result is usually
  higher**. Meta says **not to try to avoid the learning phase
  completely** — it is how delivery stabilises.
  [CORROBORATED — Meta Business Help Center, "About the learning phase",
  https://www.facebook.com/business/help/112167992830700, 2026-11-16]
- An ad set usually **exits learning after about 50 optimisation events
  within the 7 days after its last significant edit**, counted per ad
  set. Ads Manager exposes **Results** and **Last significant edit**
  columns so this can be checked directly.
  [CORROBORATED — same source]
- **Learning Limited** is shown when an ad set is unlikely to reach
  about 50 events in that week. Meta lists the usual causes: small
  audience, low budget, low bid or cost control, auction overlap, or an
  optimisation event that happens too rarely. It is a forecast, not a
  penalty — the fix is structural (consolidate, widen, or pick an event
  that occurs often enough), not more editing.
  [CORROBORATED — Meta Business Help Center, "About learning limited",
  2026-11-16]
- **Significant edits** — the changes that send an ad set back into
  learning. Meta's list:
  - *Always significant:* any change to **targeting**, **ad creative**,
    or the **optimisation event**; **adding a new ad** to the ad set;
    **pausing the ad set for 7 days or longer** (it re-enters learning
    when unpaused); changing **bid strategy**.
  - *Significant only when large:* changes to **budget**, **bid amount**
    or **spending limits** — judged relative to the current amount.
    **Meta publishes no percentage.** Its own example: $100 → $101 is
    unlikely to reset learning; $100 → $1,000 may.
  - *Not significant:* Meta moving budget between ad sets itself;
    adding a new ad set does not reset the others; an edit to one ad set
    does not reset its siblings.
  [CORROBORATED — Meta Business Help Center, "Significant edits and the
  learning phase", 2026-11-16]
- **Direct consequence for the optimiser:** `MAX_BUDGET_CHANGE_PCT` is
  the *owner's* risk setting, **not a Meta number** — no "20% rule"
  exists in Meta's published guidance, and this system must never
  present it as one. Budget proposals should be batched (one change
  window, not daily nudges), because every large change can restart
  learning and the 50-event count with it.

## 5. Placements

- **Advantage+ placements** (ad-set level) lets Meta look across the
  available placements — Facebook, Messenger, Instagram, WhatsApp,
  Audience Network and Threads — for the most efficient opportunities,
  and is Meta's default/recommended setup; Sales, Leads and App
  promotion campaigns are created with Advantage+ audience, placements
  and campaign budget switched on by default ("Advantage+ campaigns").
  [CORROBORATED — Meta Business Help Center, Advantage+ guidance,
  2026-11-16]
- Manual placement selection still exists as an option in Ads Manager;
  excluding placements turns Advantage+ placements off for that ad set.
  [CORROBORATED — same source] (A reported gradual removal of manual
  placement choice for some objectives could not be confirmed — see
  UNVERIFIED.)

## 6. Creative formats

- Format lives at the **ad** level. The formats Meta's ad system works
  with are: **single image, single video, carousel** (multiple
  cards in one ad), **collection**, and flexible/dynamic combinations
  of supplied media. **Advantage+ creative** can automatically enhance
  supplied photos/videos (cropping, music, templates and similar).
  [CORROBORATED — Meta Business Help Center / Meta for Developers
  Advantage+ guidance, 2026-11-16]
- This matches the Creative Studio's outputs: poster (image), carousel
  (one image per slide brief) and reel (video). Exact per-placement
  specs (aspect ratios, durations, file limits) are **not** re-verified
  in this pass — see UNVERIFIED; check Meta's Ads Guide before Step 4
  rather than trusting any number from memory.

## 7. Budgets and budget changes

- A budget lives at **campaign level** (Advantage campaign budget,
  shared across ad sets, optional ad-set spend limits) or at **ad set
  level** — never per ad. This is also a hard rule in this system's
  code: both Meta clients reject per-ad budget writes.
  [CORROBORATED — Meta Business Help Center, budget guidance, 2026-11-16;
  code rule from the brief]
- Meta's native safety limits exist alongside this system's own caps:
  **account spending limit** and campaign/ad-set spend caps or lifetime
  budgets. Use them — the brief requires it, because Meta reporting
  lags and system-side caps are best-effort.
  [CORROBORATED — Meta Business Help Center, spending-limit guidance,
  2026-11-16]
- On *changing* budgets, Meta's published guidance is the learning-phase
  rule in §4: large relative changes are significant edits. There is no
  official "safe percentage" and no official daily-scaling rule; the
  optimiser's change limits come from the owner's settings
  (`MAX_BUDGET_CHANGE_PCT`, `MIN_DAYS_BETWEEN_CHANGES`) and from the
  learning-phase facts above, cited — not from benchmarks.

## 8. Attribution windows

- Attribution is set **per ad set**. For website and in-store
  conversions under the standard attribution model, Meta's current
  settings are: **click-through 1 day or 7 days**, **view-through
  1 day**, **engage-through 1 day** (a conversion after a non-link
  engagement, e.g. a like/share/save, or a qualifying video view).
  Results from ad sets with different attribution settings are not
  directly comparable.
  [CORROBORATED — Meta Business Help Center, "About attribution models
  and attribution settings", read via multiple independent readings,
  Oct–Nov 2026; re-checked 2026-11-16]
- The optimiser and reports must therefore always record **which
  attribution window a number was produced under** (the brief already
  requires this) and must not compare windows against each other.
- **January 2026 Insights API change:** Meta's developer blog post of
  2025-10-16 ("Ads Insights API metric availability updates") announced
  changes effective January 2026. The post itself is **UNVERIFIED** —
  it returned HTTP 403 on every load attempt, including the Step 2
  retry on 2026-11-16. Its headline change is widely corroborated by
  independent readers of the post: **from 2026-01-12 the Ads Insights
  API no longer returns 7-day view and 28-day view attribution
  windows**; the windows that remain include 1-day click, 7-day click,
  28-day click, 1-day view and 1-day engaged view. Treat the headline
  as corroborated and every finer detail (data-retention limits etc.)
  as UNVERIFIED until the post itself can be read. Source:
  https://developers.facebook.com/blog/post/2025/10/16/ads-insights-api-metric-availability-updates/

## 9. Split testing

- Meta's A/B testing (Experiments / split tests) compares versions of
  an ad strategy — image, text, audience, placement — by showing each
  version to a **segment of the audience and ensuring nobody sees
  both** (mutually exclusive audiences), then judging on cost per
  result. Meta explicitly recommends **against** informal testing such
  as switching ad sets on and off manually: audiences overlap and the
  results are unreliable.
  [CORROBORATED — Meta Business Help Center, "About A/B tests",
  quoted verbatim by multiple independent readers, 2026-11-16]
- The Marketing API has a dedicated split-testing guide
  (https://developers.facebook.com/docs/marketing-api/guides/split-testing/).
  That page returned 403 in this environment, so the API-level study
  mechanics stay UNVERIFIED (below) — but the brief's test-design rule
  (one variable at a time, mutually exclusive audiences where the API
  supports it, never CPC/CTR alone) is consistent with Meta's published
  Help Center guidance above.

## 10. Marketing API version

- **Current version: v27.0**, released **2026-11-04**. Meta's official
  Authorization doc — loaded and read first-hand in this pass — itself
  uses `facebook.com/v27.0/dialog/oauth` in its OAuth example.
  [DIRECT — https://developers.facebook.com/documentation/ads-commerce/marketing-api/get-started/authorization,
  page updated 2026-05-05, read 2026-11-16; release date CORROBORATED
  from Meta's official Marketing API changelog via multiple independent
  readings, 2026-11-16]
- Availability from the official changelog (same corroboration):
  **v25.0** (released 2026-02-18) is available only until
  **2027-02-23**; v24.0 ended 2026-11-10; v26.0 was released
  2026-07-29. The changelog page itself
  (https://developers.facebook.com/docs/marketing-api/changelog)
  returns 403 to this environment.
- **Decision (Step 2): the pin in `app/meta_client.py` is updated from
  v25.0 to v27.0.** v25.0 had under ~3 months of life left; v27.0 is
  the version Meta's own current docs use. The adapter remains
  **UNTESTED** against a live account either way — Step 3 validates it.
- Caution carried from the v27.0 changelog reporting: on v27.0, some
  newly API-created objects get new defaults — device-reach expansion
  switched on for eligible new Sales ad sets, and product showcase may
  be enabled on new ads when Meta is confident of a product match.
  Any Step 4 draft must state these fields explicitly rather than
  inheriting defaults silently.
  [CORROBORATED — v27.0 changelog coverage, 2026-11-16]

---

## UNVERIFIED — not established from an official source in this pass

Do not rely on any of these until they are read on Meta's own pages
(with the owner, on a connection that can load them):

1. **The Jan-2026 Insights blog post's full contents** — 403 on every
   attempt (Step 1 and the Step 2 retry, 2026-11-16). Only the headline
   (7-day/28-day view windows removed from the Insights API from
   2026-01-12) is corroborated. Reported-but-unverified details include
   new retention limits (unique/hourly breakdowns ~13 months, frequency
   breakdowns ~6 months, totals ~37 months).
   https://developers.facebook.com/blog/post/2025/10/16/ads-insights-api-metric-availability-updates/
2. **Split-testing API mechanics** — the developer guide page 403'd;
   study-object fields, cell creation and result endpoints are
   unverified. https://developers.facebook.com/docs/marketing-api/guides/split-testing/
3. **Exact creative specs** — aspect ratios, resolutions, durations and
   file-size limits per placement (Meta Ads Guide) were not re-read in
   this pass.
4. **Manual-placement removal rollout** — one source reported Meta is
   gradually removing manual ad-set placement choice for Engagement,
   Leads, App promotion and Sales campaigns (keeping it for Awareness
   and Traffic). Single-source; unverified.
5. **Dynamic learning thresholds** — one source reported the API now
   exposes per-ad-set dynamic conversion/day thresholds
   (`learning_stage_info`) rather than one fixed ~50-event rule. The
   Help Center still states "about 50"; the dynamic-threshold claim is
   unverified.
6. **March 2026 click-attribution change** — multiple sources report
   Meta announced (2026-03-03) that click-through for website/in-store
   conversions counts link clicks only, with other clicks moved to
   engage-through and the video engaged-view threshold cut from 10s to
   5s. Reported consistently, but the Meta for Business announcement
   itself was not loaded in this pass.

---
*Step 2 research pass, 2026-11-16. Sources: Meta for Developers
documentation and Meta Business Help Center only. Third-party pages were
used solely to locate and corroborate official content, never as the
authority for a claim.*
