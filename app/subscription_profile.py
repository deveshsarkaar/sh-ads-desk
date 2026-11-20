"""Subscription Business Profile — SH Ads Desk vertical training pack.

Loadable business profile for the owner's subscription business
(Software Hub: official coupon codes for AI/software subscriptions,
sold at 50-90% off the official price, guaranteed/official products
only), so the system understands this vertical without the owner
re-explaining it for every campaign.

SOURCE: subscription-vertical research, 2026-11-20 —
~/workspace/research_notes/subscription-meta-ads/report.md
(501 Instagram subscription sellers mapped in
~/workspace/research_notes/instagram-subscription-sellers.md, seller
storefronts, Facebook/Instagram practitioner material, Meta policy
pages). Full integration notes: SUBSCRIPTION_TRAINING.md (repo root).
Strategy entries derived from the same research live in
app/strategy_library.py as SUB-* (active) and SUB-DNA* (DO-NOT-APPLY).

EVIDENCE DISCIPLINE (read before trusting any line below):
- The Meta Ad Library itself returned HTTP 403 to the research
  fetcher, so NO advertiser in this niche has a verified ad start
  date: longevity — the only legitimate winner signal — is UNMEASURED
  for this vertical. Nothing here calls any ad a proven winner.
- Patterns are included because they RECUR across many independent
  sellers and countries (labelled OBSERVED in the report), not
  because any performance number supports them. The Ad Library
  publishes no CTR/CPC/spend for commercial ads and none is claimed.
- Prices quoted are prices sellers DISPLAY in their own posters and
  storefronts (their marketing copy), recorded as market context —
  never as benchmarks, targets or proof of demand.
- Seller claims (customer counts, years in business, discount
  percentages) are UNVERIFIED marketing claims, quarantined the same
  way as in SUB-DNA2.

This module is DATA + a tiny accessor. It changes no gate:
PRODUCT_ELIGIBILITY.yaml is untouched (every product still has
resale_permission_confirmed = false, so nothing here can launch),
AUTOMATION_MODE stays PROPOSE and DRY_RUN stays on.
"""

DATE_READ = "2026-11-20"
SOURCE_REPORT = ("~/workspace/research_notes/"
                 "subscription-meta-ads/report.md")

PROFILE = {
    "slug": "subscription-business",
    "name": "Subscription Business (Software Hub)",
    "date_read": DATE_READ,
    "source_report": SOURCE_REPORT,

    "business": {
        "what": "Resale of official coupon codes for AI and software "
                "subscriptions (Software Hub). The buyer activates "
                "on their own account; fulfilment is a code/claim, "
                "not a shared login.",
        "positioning": [
            "Official coupon codes only — guaranteed/official "
            "products, nothing grey-market",
            "50-90% off the official price, and the discount shown "
            "in an ad must match the real checkout price",
            "Activation on the buyer's own email/account",
            "Warranty that is actually honoured (replacement/refund "
            "terms stated up front)",
        ],
        "audiences": [
            "students", "freelancers", "creators and video editors",
            "developers", "small agencies", "resellers (B2B supply)",
        ],
        "funnel": "ad > WhatsApp chat or website product page > "
                  "order > code/claim delivery. WhatsApp is the "
                  "dominant conversion surface in every observed "
                  "market for this vertical; website checkout is "
                  "second; DM is third. No observed seller in the "
                  "research uses Meta Shop / Instagram Shop checkout.",
        "primary_objective_note": "Practitioner consensus for "
                  "messaging funnels: Leads objective for WhatsApp "
                  "destination; Sales only when conversion events "
                  "(Pixel + Conversions API) are wired. Labelled "
                  "practitioner guidance, not a Meta rule.",
    },

    # Product families: what the research actually found per family.
    # "market_notes" are observed seller activity, NOT ad results.
    "product_families": [
        {
            "family": "Canva Pro",
            "role": "Richest vein in the vertical — the largest "
                    "seller family on Instagram (~68 pages) and "
                    "priced storefronts in IN/PK/BD/ID/BR/NG/NP.",
            "hooks": ["% OFF official price, on your own email",
                      "Team invite activation — no shared password",
                      "Price-grid: duration x tier"],
            "cta": "WhatsApp first, website checkout second",
            "market_notes": "Cheapest displayed prices in "
                            "Indonesia; India storefronts display "
                            "Rs 49-99/mo and Rs 299/yr (seller "
                            "display prices, not benchmarks).",
        },
        {
            "family": "ChatGPT Plus",
            "role": "Second core family; shared-vs-private tiering "
                    "is the standard creative structure.",
            "hooks": ["No international card needed — pay local",
                      "Shared vs private tier ladder in one grid",
                      "Delivery in minutes on WhatsApp"],
            "cta": "WhatsApp",
            "market_notes": "Pakistan shows the fullest tier ladder "
                            "(shared / semi-private / private).",
        },
        {
            "family": "Gemini AI Pro (Google AI Pro)",
            "role": "Newest, thinnest family — several markets "
                    "show catalogue mentions only.",
            "hooks": ["Duration anchor: the 18-month offer",
                      "One long plan vs monthly official price"],
            "cta": "WhatsApp (IN), website (NG/BD)",
            "market_notes": "18-month framing observed in IN, BD "
                            "and NG seller copy.",
        },
        {
            "family": "CapCut Pro",
            "role": "Creator-led family; Pakistan is the densest "
                    "observed market.",
            "hooks": ["Private account on your email, no watermark",
                      "Made for Reels/creators",
                      "Bundled free with Canva Pro (Indonesia)"],
            "cta": "WhatsApp (PK/ID/IN), PIX/card checkout (BR)",
            "market_notes": "No seller evidence found for BD/NG/"
                            "NP/UAE via the search index — a gap, "
                            "not a negative.",
        },
        {
            "family": "Netflix / OTT bundles",
            "role": "Most mature family in every country — and "
                    "the only family with paid-ad traces (one "
                    "Bangladeshi storefront's Facebook paid UTM; "
                    "press-reported Instagram ads for Rs 299 "
                    "bundles in India, reported as scam circulation).",
            "hooks": ["3-in-1 combo at one combo price",
                      "1 screen / 1 profile, 4K",
                      "Day-rate micro-duration (Indonesia)"],
            "cta": "WhatsApp; UAE sells via classifieds, not stores",
            "market_notes": "Treat OTT creative with extra care: "
                            "the visible ad activity in this family "
                            "is scam-associated in press reports.",
        },
        {
            "family": "Spotify Premium",
            "role": "Almost never sold solo — rides inside "
                    "multi-tool stores and bundle pricelists.",
            "hooks": ["Line item inside the bundle grid",
                      "Individual vs family plan split (Indonesia)"],
            "cta": "WhatsApp / website (as part of a store)",
            "market_notes": "Official Spotify campaigns dominate "
                            "keyword searches — filter by Page in "
                            "any Ad Library pass.",
        },
        {
            "family": "Telegram Premium",
            "role": "Empty row on Facebook: reselling runs "
                    "through Fragment/crypto gifting and "
                    "Telegram-native bots, not FB storefronts.",
            "hooks": [],
            "cta": "Telegram-native (outside Meta ads)",
            "market_notes": "No country-specific Facebook seller "
                            "evidence in any of the 8 countries "
                            "checked. Do not plan Meta creative for "
                            "this family on this evidence.",
        },
    ],

    # Creative pattern taxonomy T1-T10 from the report (section 6).
    # Recurrence across sellers/countries is the inclusion bar.
    "creative_patterns": [
        {"id": "T1", "name": "Price-grid poster",
         "structure": "Product x duration x shared/private x "
                      "warranty x price, as one table-poster"},
        {"id": "T2", "name": "Official-vs-ours strike-through",
         "structure": "Struck-through official price -> our price "
                      "+ % OFF headline. RULE for this business: "
                      "the discount must match the real checkout "
                      "price and the official price must be the "
                      "real one — proof on file before use"},
        {"id": "T3", "name": "Single-product price bomb",
         "structure": "One product, one giant price, badge, "
                      "3-4 trust bullets"},
        {"id": "T4", "name": "Bundle hero",
         "structure": "Combo of products at one combo price "
                      "(3-in-1 OTT; annual tool packs)"},
        {"id": "T5", "name": "Duration-anchor offer",
         "structure": "One long duration as the hook (18-month, "
                      "3-year, annual pack) vs monthly official"},
        {"id": "T6", "name": "Own-email activation",
         "structure": "'Activated on YOUR email/account' as the "
                      "quality claim that separates official-code "
                      "supply from shared-login offers"},
        {"id": "T7", "name": "Warranty shield",
         "structure": "Replacement warranty + refund terms "
                      "printed on the creative. Only claims the "
                      "business actually honours"},
        {"id": "T8", "name": "Local-payment hook",
         "structure": "'No international card needed' + local "
                      "rails (UPI, JazzCash/EasyPaisa, bKash, "
                      "PIX, eSewa/Khalti)"},
        {"id": "T9", "name": "Instant-delivery claim",
         "structure": "'Instant activation / delivery in "
                      "minutes' — only where fulfilment really "
                      "is that fast"},
        {"id": "T10", "name": "Catalogue grid",
         "structure": "Many product logos in one poster, 'all "
                      "premium tools in one place'"},
    ],

    "copy_rules": [
        "Price in the first line; local currency always; "
        "duration always stated",
        "One CTA per ad",
        "Language follows the market: English base, Hinglish for "
        "India, Urdu for Pakistan, Bahasa for Indonesia, "
        "Portuguese for Brazil",
        "Support language = buyer's language",
    ],

    # The daily Growth Loop, specialised for this business.
    "growth_loop_for_this_business": [
        "1. Competitor discovery: scan the Competitor Research "
        "Board seeds for this vertical (poster sellers + "
        "storefronts), then the Ad Library by Page — most of this "
        "niche does NOT advertise, so organic poster/storefront "
        "movement is a first-class signal here",
        "2. Creative: build from patterns T1-T10 with this "
        "business's real prices; every discount claim checked "
        "against checkout before the brief is approved",
        "3. Compliance gate: eligibility first (no product with "
        "resale_permission_confirmed = false may be advertised, "
        "whatever this pack says), then the policy checker + "
        "the subscription do/don't list below",
        "4. Launch in PROPOSE mode: drafts only, owner approves "
        "every campaign (DRY_RUN stays on until the owner wires "
        "a live account)",
        "5. Monitor: judge by recorded results in this system "
        "only. No Library longevity data exists for this niche "
        "yet — the first live Ad Library pass must record real "
        "start dates before any creative is called a winner",
        "6. Refresh: rotate the price-grid/bundle creatives on "
        "the loop's normal fatigue cycle; retire any creative "
        "whose price no longer matches checkout",
    ],

    "compliance_do": [
        "Advertise only products whose resale permission is "
        "confirmed in PRODUCT_ELIGIBILITY.yaml",
        "Show discounts that are real and match the checkout "
        "price exactly",
        "State duration, activation method (own account) and "
        "warranty terms plainly",
        "Use the brand names to describe what the code is for — "
        "never to imply official affiliation or endorsement",
    ],
    "compliance_dont": [
        "No guaranteed-income or earnings claims, ever",
        "No fake official affiliation ('official partner', "
        "brand logos as endorsement)",
        "No shared-login / shared-credential offers — this "
        "business sells codes, not logins (also blocked by the "
        "software_digital compliance pack)",
        "No fake urgency or scarcity ('ends tonight' on a "
        "standing offer, invented stock counts)",
        "No discount in the creative that differs from checkout "
        "(a named Meta Prohibited Commercial Practices trigger)",
        "No Facebook Marketplace listings for subscriptions — "
        "the category is prohibited there (Meta Commerce "
        "Policies); Pages/Groups posts are the surface, "
        "Marketplace is not",
        "No seller marketing numbers (customer counts, % OFF "
        "headlines, years in business) reused as our claims or "
        "benchmarks",
    ],

    "coverage_limits": [
        "Ad Library direct read returned HTTP 403 in the "
        "2026-11-20 research; all advertiser findings are "
        "search-index grade",
        "Longevity unmeasured for every advertiser in this "
        "niche — no winner claims until a live pass records "
        "start dates",
        "Bangla ad creative and UAE reseller ads are the "
        "thinnest evidence cells — gaps, not negatives",
    ],
}


def load():
    """The Subscription Business Profile as a plain dict."""
    import copy
    return copy.deepcopy(PROFILE)


def product_family(name):
    """One product-family entry by (case-insensitive) name, or None."""
    for fam in PROFILE["product_families"]:
        if fam["family"].lower() == str(name).lower():
            import copy
            return copy.deepcopy(fam)
    return None


def creative_pattern(pattern_id):
    """One creative-pattern entry (T1-T10) by id, or None."""
    for pat in PROFILE["creative_patterns"]:
        if pat["id"] == pattern_id:
            import copy
            return copy.deepcopy(pat)
    return None
