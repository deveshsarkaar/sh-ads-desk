# SUBSCRIPTION_TRAINING.md — Subscription vertical pack, integrated

On 2026-11-20 the owner asked for two things: (1) research how the
Instagram subscription-seller world actually uses Meta ads — who
advertises, with what creative, in which countries, for which
products, and what Facebook Marketplace looks like for this
category; (2) train the findings into SH Ads Desk so the system
understands his subscription business (Software Hub: official
coupon codes, 50–90% off official price, guaranteed/official
products only) without being re-explained.

**Source report (read in full before this integration):**
`~/workspace/research_notes/subscription-meta-ads/report.md`,
built on the 501-seller map in
`~/workspace/research_notes/instagram-subscription-sellers.md`,
seller storefronts (several opened and read directly), social
search, and Meta policy pages.

## What the research found (short version)

- **Almost nobody in the mapped niche verifiably advertises.**
  19 named sellers were checked individually; the search index
  held no Ad Library record for any of them. Their funnels run on
  organic posters + WhatsApp + their own storefronts.
- **Only two paid traces exist:** one Bangladeshi OTT storefront
  whose landing URL carries a Facebook paid UTM, and
  press-reported Instagram ads for Rs 299 OTT bundles in India
  (reported as scam circulation). No Page name or ad start date
  was recoverable for either.
- **The creative system is consistent across countries:**
  price-grid posters, official-vs-ours strike-through pricing,
  bundle heroes, duration anchors (18-month / annual), own-email
  activation as the quality claim, warranty printed on the
  creative, local-payment hooks, WhatsApp-first conversion.
- **Facebook Marketplace is a prohibited channel** for digital
  products/subscriptions (Meta Commerce Policies) — auto-rejected
  listings, plus an India-specific commercial-seller restriction.
- **Telegram Premium has no Facebook storefront layer at all**
  (Fragment/crypto gifting); Spotify rides inside bundles;
  official brand Pages (Canva, Spotify, Google, Jio × Canva)
  dominate keyword searches and must be filtered out by Page.

## What was integrated

**Integration point 1 — Strategy Library (`app/strategy_library.py`):**
12 entries seeded as **SUB-1…SUB-12** (source label
"Subscription vertical research (seller-market study,
2026-11-20)", date_read 2026-11-20) plus two screening entries
**SUB-DNA1 / SUB-DNA2** as DO_NOT_APPLY. They cover: organic-layer
competitor discovery, patterns T1/T2/T4/T5/T6/T7, the WhatsApp
funnel, the tier-ladder adaptation (duration/pack, never
shared-login), the country × product demand map, the Marketplace
ban, and the no-winner-language rule.

**Integration point 2 — Subscription Business Profile
(`app/subscription_profile.py`):** a loadable data profile —
business summary, positioning, audiences, funnel, per-family
hooks/CTAs/market notes (Canva, ChatGPT, Gemini, CapCut, OTT,
Spotify, Telegram Premium), the T1–T10 creative taxonomy,
copy rules, the daily Growth Loop specialised for this business,
compliance do/don't lists, and the research's coverage limits.

**Integration point 3 — Competitor Research Board
(`app/competitor_seeds.py`):** the "software-hub" seed list gains
the research-found names for this vertical — Tradeello (organic
promotion observed), OTT Services BD (paid UTM trace), SubsHub,
AcademicTools, GroupAITools, OTTSeller — each with the standard
Ad Library keyword-search URL for a live check and an honesty
note: **no Library record found, longevity UNMEASURED**.

## Screened OUT

- **Every seller performance implication.** No CTR/CPC/spend/
  ROAS figure exists for this niche in the evidence, and none
  was seeded. Longevity — the only legitimate winner signal —
  is unmeasured because the Ad Library returned HTTP 403 to the
  research fetcher and no source carried an ad start date.
- **Seller marketing numbers** (90–98% OFF headlines, customer
  counts, years in business, delivery-time claims) — quarantined
  as SUB-DNA2, same discipline as Damini S26 and YT-DNA.
- **Grey-layer tactics** (shared logins, credential supply,
  checkout-mismatched discounts, fake urgency, guaranteed-income
  claims, fake official affiliation) — quarantined as SUB-DNA1;
  several are already blocked by the `software_digital`
  compliance pack in `app/industries.py`.
- **Marketplace as a channel** — prohibited for this category;
  seeded as a go_live warning (SUB-11), never as a tactic.

## Guardrails — unchanged by this pack

- `PRODUCT_ELIGIBILITY.yaml` is **untouched**: every product
  still has `resale_permission_confirmed: false`. Training is
  not permission to advertise; the eligibility gate still
  blocks every launch.
- `AUTOMATION_MODE` stays **PROPOSE**; `DRY_RUN` stays **true**
  (settings.yaml / settings.json untouched).
- No Meta writes of any kind were made. No live ad exists.
- All new in-software wording is English only.
- Compliance notes carried into the pack: no guaranteed-income/
  earnings claims; no fake official affiliation; discount
  claims only where the underlying offer is real and matches
  checkout.

## Honest labels

- **VERIFIED:** the report's OBSERVED items were seen in the
  sources named there (seller storefronts opened directly on
  2026-11-20 include ottseller.com and groupaitools.com);
  the pack's files and tests are in this repo.
- **UNVERIFIED:** all seller marketing claims and all
  practitioner funnel guidance (labelled inside the entries).
- **UNMEASURED:** Ad Library longevity for every advertiser in
  this vertical — the first live Library pass (owner's browser,
  Page + country, per report section 5) is the step that can
  produce real start dates.
- **UNTESTED:** no live Meta run — the owner's Meta accounts
  remain suspended, so nothing in this pack has been exercised
  against a real ad account.
