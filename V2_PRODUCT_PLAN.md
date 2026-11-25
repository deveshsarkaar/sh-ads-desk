# SH Ads Desk V2 — Product Plan (25 Nov 2026)

Built from worldwide research run on 25 Nov 2026: Meta's official help
articles + policy tool, 12 research inputs (Madgicx, Birch/Revealbot,
AdCreative.ai, Smartly, Motion, Hunch, Pencil, Segwise, YouTube
practitioners, agency articles, public social trends, AI creative
tools). Vendor/creator performance claims in that research are
attributed claims, not verified facts.

## Honest positioning

This market already has serious players. "World's first" is NOT a
claim this product makes. The defensible edge is different:

- **Approval-first, compliance-gated operation** — every Meta write
  stays a proposal until the owner approves; eligibility, destination
  and banned-claim gates fail closed (existing guardrails, unchanged).
- **Multi-industry playbooks** — industry presets with KPIs beyond
  e-commerce ROAS (leads, WhatsApp, calls, footfall), built for
  agencies, retailers and SMBs, not only DTC brands.
- **India-first operations** — Hinglish reporting, WhatsApp alerts,
  pricing SMBs can actually pay (global leaders start at $999-$2,500/mo).
- **Creative-and-signal operating system** — the research consensus is
  that creative diversity is the targeting lever under Advantage+;
  V2 is built around that loop, not audience tricks.

## What the research proved (core loop to match)

1. Daily AI audit -> ranked recommendations -> prepared paused
   actions -> human approval -> audit log/rollback (Madgicx pattern).
2. Rules with nested conditions, dry-run preview and execution logs
   (Birch pattern) — wrapped in guided recommendations so non-experts
   can use them.
3. Brand-kit creative generation with transparent scoring, then
   closing the loop into campaign drafting (AdCreative.ai / Pencil
   leave the Meta execution loop open).
4. Visual creative analytics: leaderboard, hook/angle/format/persona
   analysis, fatigue detection, weekly retro (Motion / Segwise).
5. Feed/catalog automation for retailers (Hunch / Smartly), packaged
   at SMB prices instead of enterprise quotes.
6. Practitioner system: distinct concepts over near-duplicates,
   ABO testing lane -> CBO/Advantage+ scale, 1-3x CPA thresholds,
   ~7-day reads, staged +10-20% scale steps, fatigue early-warning.

## Meta platform facts V2 is built on (official sources, 25 Nov 2026)

- Advantage+ sales/leads campaigns apply AI across audience,
  placement and budget; best practice = first-party data (Pixel +
  Conversions API), diverse creative assets, value tools, reporting
  segments. Opportunity Score does not guarantee performance.
- Advantage+ creative enhancements can be on by default; previews
  must be checked before publishing.
- Subscription-services policy: ads must disclose pricing and
  recurrent billing; PII-collecting ads are prohibited without an
  unchecked opt-in, clear cancellation language, and a clear
  price + billing interval.

## V2 modules shipped in this build

- `app/v2_readiness.py` — Advantage+ readiness audit (conversion
  volume, creative diversity, tracking, budget adequacy). Bands:
  ready / testing-lane-first / fix-tracking-first. No guarantees.
- `app/creative_matrix.py` — angle x persona x format x hook brief
  matrix from industry presets; diversity score; near-duplicate
  warnings; owner-supplied facts only.
- `app/test_lane.py` — ABO-style test-cell planner (threshold =
  1-3x target CPA), kill/iterate/graduate proposals, staged scale
  steps. Proposals only; never changes a budget.
- `app/fatigue.py` — fatigue early-warning from CTR / frequency /
  CPM / hook-rate movement. Recommendation only.
- `app/subscription_disclosure.py` — subscription-offer disclosure
  checker (price + interval, cancellation language, unchecked
  opt-in), fail-closed, from the retrieved Meta policy text.

## Packaging (recommendation, owner decides)

- Starter (retailer/SMB): 1 workspace, readiness audit, creative
  matrix, test lane, fatigue alerts, weekly report.
- Growth (agency): multi-client workspaces, white-label reports,
  approval roles, catalog/feed module.
- Pro-Agency: everything + client review links, API/report exports,
  priority support.
Pricing stays owner-set; competitor anchors from research:
Madgicx $32-$329/mo spend-tiered, Birch $49-$99/mo, AdCreative.ai
$39-$999/mo, Pencil $14-$55/mo generation-based, Motion/Segwise
$499-$999/mo+, Hunch $2,500/mo+. India SMB pricing must sit well
below the $999 floor to win the segment those tools ignore.

## Roadmap (next, in order)

1. Wire V2 modules into Mission Control pages (readiness card,
   creative matrix board, test-lane board, fatigue alerts).
2. Feed/catalog module (Sheets/CSV mapper, dynamic price/offer
   layers, catalog image-to-video briefs).
3. Rules engine v2 (nested conditions, dry-run preview, execution
   log) behind the existing approval queue.
4. Client-safe share links + white-label report exports.
5. Live Meta path only after a working Meta account exists and the
   owner approves specific drafts — guardrails unchanged.

## Non-negotiables (unchanged)

DRY_RUN + AUTOMATION_MODE=PROPOSE defaults; approval for every Meta
write (even PAUSED); eligibility/destination gates fail closed; kill
switch; audit log; rollback; mock-first; no result guarantees; no
policy-evasion wording or targeting.
