# SH Ads Desk — Enterprise Readiness Roadmap

Built from the November 2026 enterprise-requirements research.
Status labels: HAVE (in product today), PARTIAL, MISSING.

## Procurement must-haves

| Requirement | Status | Next step |
|---|---|---|
| Exportable audit logs | HAVE (CSV export, /audit/export) | Add date-range filter |
| Approval workflows + spend caps | HAVE (approval queue, budget caps, kill switch) | Per-client approval rules |
| Per-client workspace isolation | PARTIAL (business profiles) | Profile-level data scoping audit |
| Granular RBAC (owner/member/viewer) | MISSING (single owner login) | E1: multi-user roles |
| MFA enforcement | MISSING | E1: TOTP for owner/admin |
| SAML/OIDC SSO + SCIM | MISSING | E2: OIDC first, SCIM after |
| SOC 2 Type II / ISO 27001 | MISSING | E3: controls + auditor path |
| Security package (data flow, subprocessors, IR plan, AI disclosure) | PARTIAL (secrets handling documented) | E1: publish SECURITY.md |
| SLA + annual invoicing | MISSING (business process) | Owner decision with first enterprise pilot |
| Data residency / self-hosting | HAVE (Docker on customer VPS, data portability) | Document deployment guide |

## Agency must-haves

| Requirement | Status | Next step |
|---|---|---|
| Cross-account dashboard | PARTIAL (Mission Control per profile) | E2: multi-profile rollup |
| White-label scheduled reports | PARTIAL (reports exist) | E2: scheduled client exports |
| Fast access revocation | PARTIAL (profile switcher) | E1 with RBAC |
| Bulk operations | MISSING | E2 |

## Meta platform gate

Serving other businesses' ad accounts through one vendor app requires
Meta Advanced/Full Access via App Review + Business Verification.
SH Ads Desk's model keeps ad accounts customer-owned, which reduces
dependence on a single vendor app approval; App Review preparation
starts only after live pilot proof exists.

## Phases

- E1 (next build): multi-user roles (owner/member/viewer), TOTP MFA,
  SECURITY.md security package, audit export date filter.
- E2: OIDC SSO, cross-account rollup, white-label scheduled reports,
  bulk operations.
- E3: SOC 2 readiness (controls, evidence collection), SCIM,
  enterprise SLA packaging.

No phase promises enterprise revenue. Each phase removes a named
procurement blocker so pilot conversations can proceed.
