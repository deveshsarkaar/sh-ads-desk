# SH Ads Desk — Investor Brief

Status: internal working brief, November 2026. Every traction statement
below is labelled by evidence level. Nothing here promises funding,
returns, or timelines.

## One-line positioning

SH Ads Desk is an approval-first AI operations layer for Meta
advertising: AI prepares research, creative briefs, campaign drafts and
optimisation proposals; a human approves every consequential step
before anything touches an ad account. It sits on top of Meta's
Advantage+ automation instead of duplicating it.

## Why this wedge

- Meta has automated the delivery core (Advantage+ targeting, bidding,
  placements, budget distribution) and ships its own creative
  generation and business agents. Third-party value has moved to
  governance: cross-account control, draft-approve-publish workflows,
  compliance and eligibility gates, creative-diversity operations,
  signal-readiness audits, and client-ready reporting.
- Meta's November 2026 Commercial Terms update makes advertisers
  solely responsible for AI-generated content. Approval gates,
  disclosure checks and audit trails answer that liability directly.
- Enterprise and agency buyers require exactly this control layer:
  granular roles, exportable audit logs, per-client approval rules and
  spend caps, and a security package before procurement says yes.

## What exists today (verified locally, 109+ automated tests)

- Multi-industry business profiles with per-profile settings,
  offerings and eligibility gates (resale permission default off).
- Growth Loop: competitor research board, creative studio, campaign
  drafting, approval queue, budget proposals, daily/weekly reporting.
- V2 modules: Advantage+ readiness audit, creative diversification
  matrix, test-lane planner, fatigue early-warning, subscription
  disclosure checker (built from Meta's published subscription
  services policy).
- Simple-by-mode UI (Customer / Agency / Enterprise), background
  worker jobs, full audit log with CSV export, kill switch, rollback,
  DRY_RUN + propose-only defaults. No Meta write happens without the
  account owner's approval of that specific draft.
- Honest limits: live Meta API path is untested end-to-end, there are
  no paying customers yet, and all products sit behind the
  eligibility gate until resale permission is confirmed per product.

## Competitive frame (named honestly)

Smartly (enterprise suite, opaque pricing), Madgicx (transparent
spend-tiered SMB/agency), Birch (rules automation), Hunch (catalog
creative), Motion/Segwise (creative analytics), AdCreative.ai/Pencil
(creative generation), plus funded AI-agent entrants such as Creatify,
Arcads and MAI. SH Ads Desk does not claim to be first or only. The
defensible edge is the combination: approval-first governance +
compliance gates + multi-industry playbooks + transparent India-SMB
pricing, closing the research-to-report loop in one product.

## Business model (owner-set pricing, recommendation on record)

Subscription per workspace: setup fee plus monthly tiers
(Starter/Growth/Pro-Agency), white-label option for agencies.
Suggested India bands from the November 2026 pricing review: setup
Rs 9,999-14,999; Starter Rs 7,999/mo; Growth Rs 14,999/mo;
Pro-Agency Rs 29,999/mo; white-label Rs 49,999-99,999. Final pricing
is the owner's decision and is not yet in market.

## Milestones before raising (sequenced)

1. Live proof on 2-3 real Meta ad accounts under the approval flow,
   results measured against each account's own baseline.
2. 3-5 paying pilot customers with written pilot terms and two
   measured case studies (no guaranteed-outcome language).
3. Customer references willing to take investor calls.
4. Company hygiene: cap table, vesting, IP assignment, data room.
5. Seed readiness: repeatable acquisition, MRR trend with cohort
   retention, unit economics, and a round sized to prove 18-24
   months of milestones.

## Risks investors will price

Platform dependency on Meta APIs and policy; category crowding;
SMB churn and CAC; compliance and account-safety posture. Mitigations
on record: customer-owned ad accounts, approval-first design,
eligibility and disclosure gates, self-hosting/portability, and
vertical playbooks that accumulate per industry.
