# PRACTICES.md — SH Ads Desk

**Status: UNVERIFIED in Step 1.** The brief (Part 2) requires every practice
point to be verified live on Meta's official documentation with URL + date
read, before it guides any decision. That verification is a **Step 2** task
and has NOT been done in this Step 1 mock build. Nothing below is a default,
a threshold, or a strategy instruction.

Points to verify in Step 2, from official sources only:
- Objectives and campaign / ad set / ad structure guidance.
- Targeting vs broad / automated audience options.
- Placements and creative formats.
- Learning phase: what it is, and how edits and budget changes affect it.
- Budget-change guidance (before the optimiser suggests any defaults).
- Attribution windows — what is available now.

Two items the brief itself flags as known starting points (to re-check live
in Step 2, with dates):
- Marketing API split testing on mutually exclusive audiences:
  https://developers.facebook.com/docs/marketing-api/guides/split-testing/
- Insights attribution-window changes announced for January 2026:
  https://developers.facebook.com/blog/post/2025/10/16/ads-insights-api-metric-availability-updates/

Meta access questions (permissions, access tier / App Review / business
verification for managing only the owner's own ad account, rate limits,
Page/Instagram identity options per objective) are likewise **Step 2** —
answered from the current official pages at
https://developers.facebook.com/documentation/ads-commerce/marketing-api/get-started/authorization
and https://developers.facebook.com/documentation/development/create-an-app/marketing-api-use-cases ,
each cited with URL and date. No blanket requirement is assumed in Step 1.

---
## Full-build note (2026-11-15)
This file was carried over from Step 1 unchanged except for this note.
Several points above remain **UNVERIFIED** against current official Meta
documentation — they must be re-checked with the owner in Step 2 before any
strategy or default relies on them. The Marketing API version pinned in
`app/meta_client.py` (v25.0) is likewise UNVERIFIED against the official
changelog in this build. Nothing in this file is used as a hardcoded
default anywhere in the code; every threshold lives in settings.
