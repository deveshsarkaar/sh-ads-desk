"""Strategy Library — SH Ads Desk (industry-agnostic build).

Playbook seed data the Growth Loop and the roles draw on. Two research
reports feed it (both read in full on 2026-11-16):

1. Damini Tripathi / Marketian strategy extraction — 35 strategies
   (S1–S35), ~/workspace/research_notes/damini-strategies-20261116/report.md
   Label on every entry: source="Damini Tripathi / Marketian
   (practitioner)". Her course-page performance numbers (ROAS/CTR
   claims) are her UNVERIFIED marketing claims — they are NOT seeded
   anywhere as benchmarks or defaults.
2. Meta Ads practitioner knowledge base — 21 practitioner entries
   (P1–P21) + 4 book-derived entries (B1–B4) + 9 DO-NOT-APPLY entries
   (D1–D9), ~/workspace/research_notes/meta-ads-knowledge-20261116/report.md
   OFFICIAL entries (O1–O10) live in the Meta Knowledge register
   (app/trends.py), not here.
3. Winner-patterns research — 14 winner habits (report §B, seeded as
   W1–W14) + 9 viral creative patterns (report §C, seeded as V1–V9),
   labelled PRACTITIONER/CASE,
   ~/workspace/research_notes/meta-ads-winner-patterns-20261116/report.md
   That report's section F earnings/case claims are quarantined as
   UNVERIFIED and are NOT seeded anywhere as facts or benchmarks.

COMPLIANCE SCREENING: every entry was screened against the system's
policy/compliance rules (core banned claims, industry packs, and the
knowledge base's own Section 4) before seeding. Anything conflicting is
seeded ONLY as a DO_NOT_APPLY entry with the reason — never as an active
tactic. Practitioner numbers (budgets, %, day counts) are the author's
own settings: they belong in owner-editable settings, never hardcoded.

This module is DATA + tiny accessors. New research entries can be added
as data later without code changes: append dicts to ENTRIES (or load
owner-added rows from the DB table strategy_entries when present).
"""

DATE_READ = "2026-11-16"
DAMINI = "Damini Tripathi / Marketian (practitioner)"
BLOG = "https://www.marketian.io/blog/"
KB = "Meta Ads knowledge base (practitioner research, 2026-11-16)"


def _e(id_, title, source, url, stage, summary, status="ACTIVE", note=""):
    return {"id": id_, "title": title, "source": source, "source_url": url,
            "date_read": DATE_READ, "stage": stage, "summary": summary,
            "status": status, "screening_note": note}


# ------------------------------------------------------------- Damini S1–S35
DAMINI_ENTRIES = [
    _e("S1", "Fight ad fatigue: frequency control + constant creative rotation",
       DAMINI, BLOG + "my-learnings-after-spending-crores-on-facebook-ads",
       "monitoring",
       "Watch frequency (roughly one exposure per person per week as her "
       "rule of thumb); when frequency climbs, rotate fresh creatives in "
       "instead of pushing the same ad. Maps to the optimiser's fatigue "
       "detection + the loop's refresh stage."),
    _e("S2", "Segment audiences; each segment gets its own creative",
       DAMINI, BLOG + "my-learnings-after-spending-crores-on-facebook-ads",
       "structure",
       "Website visitors, product viewers and cart abandoners get separate "
       "retargeting ads with different creatives/copy per segment — the "
       "same ad to everyone reads as spam and kills conversion."),
    _e("S3", "Earn broad targeting: build custom/local audiences first",
       DAMINI, BLOG + "my-learnings-after-spending-crores-on-facebook-ads",
       "structure",
       "Do not jump blindly to broad. Build custom and local audiences "
       "first, mix and match, then widen to broad — scaling gets easier "
       "once the system has first-party signal."),
    _e("S4", "Learning-phase discipline: no edits, judge after ~50 conversions",
       DAMINI, BLOG + "my-learnings-after-spending-crores-on-facebook-ads",
       "optimisation",
       "Never edit during learning (every significant edit restarts it). "
       "Her threshold: let a new ad collect ~50 conversions, exit "
       "learning, then judge. The 50 figure is an owner-editable "
       "threshold in this system, consistent with PRACTICES.md."),
    _e("S5", "Free value first: emotional connection before selling",
       DAMINI, BLOG + "my-learnings-after-spending-crores-on-facebook-ads",
       "funnel",
       "Give free educational/entertaining value so the audience builds "
       "trust before any pitch; long-run this creates recurring, happy "
       "customers instead of one-off leads."),
    _e("S6", "Test creatives in volume, systematically",
       DAMINI, BLOG + "my-learnings-after-spending-crores-on-facebook-ads",
       "creative",
       "Most marketers launch one creative and never test another. Test a "
       "bunch of creatives cost-effectively and let the data pick winners "
       "(her cited example tested 50 in a month — volume is the owner's "
       "setting, not a system default)."),
    _e("S7", "Never neglect the landing page — optimise it, mobile-first",
       DAMINI, BLOG + "my-learnings-after-spending-crores-on-facebook-ads",
       "go_live",
       "Great ads die on a bad landing page. Optimise the destination "
       "mobile-first before scaling traffic to it — this is why the "
       "destination gate exists in this system."),
    _e("S8", "Manage ad comments like a storefront",
       DAMINI, BLOG + "my-learnings-after-spending-crores-on-facebook-ads",
       "monitoring",
       "Monitor comments on live ads: visible 'spammy/expensive' comments "
       "scare off new buyers. Address or hide negative feedback, fix the "
       "underlying issue, keep refreshing ads.",
       note="Screened: hiding/addressing comments is normal page "
            "moderation. Fabricating positive comments or engagement is "
            "DO-NOT-APPLY (see D1/D8)."),
    _e("S9", "Funnel first: awareness/engagement, then sell (cold, warm, hot)",
       DAMINI, BLOG + "my-learnings-after-spending-crores-on-facebook-ads",
       "funnel",
       "Launching a creative straight into a sales objective 'is not a "
       "strategy'. Default funnel: awareness/engagement, then move cold "
       "to warm to hot, then convert. (Small-budget exception = S13.)"),
    _e("S10", "Study competitors in the Ad Library: copy the concept, never the ad",
       DAMINI, BLOG + "how-to-run-meta-ads-for-small-budgets",
       "competitor_research",
       "Ads a competitor has run continuously for 3–6 months are the "
       "proven-winner signal (longevity). Take the concept/format, add "
       "your own twist.",
       note="Screened and narrowed: in this system this is CONCEPT-level "
            "inspiration ONLY — never copy an ad verbatim, never reuse "
            "another advertiser's assets or text (standing system rule)."),
    _e("S11", "Small budget: push ONE hero product (best-seller with margin)",
       DAMINI, BLOG + "how-to-run-meta-ads-for-small-budgets",
       "structure",
       "Splitting a small budget across many products/ad sets starves "
       "every test. Pick the best-selling offering with margin, keep few "
       "ad sets, test vigorously; aim for profit or break-even first."),
    _e("S12", "Use Meta's AI (Advantage+) on small budgets, then scale the winner",
       DAMINI, BLOG + "how-to-run-meta-ads-for-small-budgets",
       "scaling",
       "Let Advantage+/Advantage budget optimisation handle placement "
       "and budget on small budgets; once an ad performs, scale by "
       "raising its budget (inside the owner's caps and "
       "MAX_BUDGET_CHANGE_PCT in this system)."),
    _e("S13", "Tiny budget exception: skip awareness, spend on the conversion goal",
       DAMINI, BLOG + "how-to-run-meta-ads-for-small-budgets",
       "funnel",
       "Counterpoint to S9, explicitly budget-dependent: with very "
       "little money, awareness spend is wasted — focus the whole budget "
       "on the conversion goal. In this system this is an explicit "
       "per-profile setting, never a silent default."),
    _e("S14", "Let a launched ad run at least a week untouched",
       DAMINI, BLOG + "how-to-run-meta-ads-for-small-budgets",
       "optimisation",
       "Few conversions in 3 days risks 'learning limited'; once out of "
       "learning, never change targeting/placement mid-flight. Run at "
       "least a week, collect data, then close or optimise."),
    _e("S15", "One creative, one specific audience, one specific CTA",
       DAMINI, BLOG + "how-to-run-meta-ads-for-small-budgets",
       "creative",
       "Beat generic competitor messages with a creative pitched to a "
       "single niche and a single specific call to action. Encoded as a "
       "planner rule in this system."),
    _e("S16", "Lookalike audiences from existing customer data",
       DAMINI, BLOG + "how-to-run-meta-ads-for-small-budgets",
       "scaling",
       "If you already know your customers, build lookalikes to reach "
       "measured, right-fit audiences without spending much on testing. "
       "Surfaces in this system as a scaling proposal type."),
    _e("S17", "Manual first, AI second: feed Andromeda data before trusting it",
       DAMINI, BLOG + "meta-andromeda-era-where-creatives-rule-and-targeting-dies",
       "structure",
       "A new account has no data: start with manual campaigns, test "
       "audiences/creatives/placements at grassroots level, learn who "
       "clicks and converts — then let Andromeda/Advantage+ scale it. "
       "Never blind-trust AI; AI cannot fix a bad creative."),
    _e("S18", "Run a manual + AI mix; keep backup audiences ready",
       DAMINI, BLOG + "ai-vs-manual-facebook-campaigns-which-facebook-ads-strategy-works-best-in-2025",
       "scaling",
       "Manual finds winners, AI scales them. Keep experimenting while "
       "scaling so a backup audience is ready before the winning one "
       "saturates."),
    _e("S19", "No-spend diagnosis checklist (6 causes)",
       DAMINI, BLOG + "why-facebook-ads-not-spending-money",
       "monitoring",
       "When an ad does not spend, check in order: (1) account spending "
       "limit, (2) learning limited (audience/budget/duplicate ad sets), "
       "(3) payment issues, (4) Meta-side glitches, (5) too many "
       "creatives in one ad set (3–5 winners per ad set), (6) policy "
       "violation — including on the landing page. Encoded in the "
       "Account Health Monitor role."),
    _e("S20", "RTO-reduction stack for Indian e-commerce (ops side)",
       DAMINI, BLOG + "how-to-reduce-rto-in-ecommerce-in-india",
       "funnel",
       "Exclude high-RTO pincodes from targeting; verify COD orders "
       "(OTP confirmation, partial COD) to filter fake orders; build the "
       "trust layer (clear checkout, organic content) that makes buyers "
       "prepay. Guidance for the E-commerce preset.",
       note="Screened: the 'reverse discount' price-display component of "
            "her stack is EXCLUDED here and seeded separately as "
            "DO-NOT-APPLY (S20-DNA)."),
    _e("S20-DNA", "DO NOT APPLY: 'Reverse discount' inflated-price display",
       DAMINI, BLOG + "how-to-reduce-rto-in-ecommerce-in-india",
       "creative",
       "Displaying a product at an inflated price (e.g. ₹1,499) it does "
       "not genuinely sell at, then showing a prepaid 'discount' off "
       "that anchor.",
       status="DO_NOT_APPLY",
       note="Conflicts with the system's unverified-discount / was-now "
            "price gate and the knowledge base's D4 (fake scarcity and "
            "misleading price framing). A genuine discount on the REAL "
            "selling price is a normal owner pricing decision — the "
            "inflated anchor is what is banned."),
    _e("S21", "3-second rule + Hook, Body, CTA anatomy (with angles)",
       DAMINI, "https://www.marketian.io/courses/Ad-Creative-Course-6aab8da8372ab22b2a4927a4",
       "creative",
       "You get three seconds, not thirty: the hook must land inside 3 "
       "seconds. Every ad is built as Hook (typed frameworks), Body "
       "(frameworks), CTA — and an Angle, which is distinct from the "
       "hook. Encoded as creative-brief fields in this system."),
    _e("S22", "22-format creative library: rotate formats, don't repeat one",
       DAMINI, "https://www.marketian.io/courses/Ad-Creative-Course-6aab8da8372ab22b2a4927a4",
       "creative",
       "Format taxonomy for inspiration briefs: UGC, Value-Based, "
       "Quirky/Meme, Educational, AI Ads, Us vs Them, Before vs After, "
       "Statistics, Ugly Ads, Founder, Testimonial, Podcast, Street "
       "Interview, Mini Drama, Calling-Out, First Person, In-Office, Ad "
       "Review, AMA, Storytelling, Mini Vlog, Screen Recording.",
       note="Screened: 'Before vs After' is EXCLUDED for health/wellness "
            "profiles (industry compliance pack blocks it) and 'Us vs "
            "Them' must never use a competitor's name/logo (see D6)."),
    _e("S23", "Creative diversification: one product, dozens of creatives",
       DAMINI, "https://www.marketian.io/courses/Ad-Creative-Course-6aab8da8372ab22b2a4927a4",
       "creative",
       "Angle expansion is the method: pull many distinct creatives out "
       "of a single offering by varying angle, persona and format — the "
       "production engine behind the loop's refresh stage."),
    _e("S24", "Never start from a blank page: frameworks, checklists, swipe files",
       DAMINI, "https://www.marketian.io/courses/Ad-Creative-Course-6aab8da8372ab22b2a4927a4",
       "creative",
       "Run every ad through a pre-launch creative checklist; keep hook "
       "templates and a swipe file of ads that worked (study the "
       "structure, then apply it — inspiration only); use AI prompts "
       "for hooks/scripts/ideas."),
    _e("S25", "The three creative anti-patterns",
       DAMINI, "https://www.marketian.io/courses/Ad-Creative-Course-6aab8da8372ab22b2a4927a4",
       "creative",
       "Why ads die: (1) skipped in 3 seconds — hook too late; "
       "(2) ignored — corporate voice, zero personality; (3) testing on "
       "vibes — random new creatives, nothing learned. Encoded as "
       "creative quality-check failures."),
    _e("S26", "Fix the creative before touching the budget",
       DAMINI, "https://www.marketian.io/courses/Ad-Creative-Course-6aab8da8372ab22b2a4927a4",
       "optimisation",
       "'Your product is fine. Your creative isn't.' Before any budget "
       "increase, check hook, voice and testing discipline (S25). The "
       "optimiser's first diagnosis in this system.",
       note="Her course-page before/after numbers (ROAS 1.2x to 4.8x, "
            "3.1% CTR) are her UNVERIFIED marketing claims — deliberately "
            "NOT imported as benchmarks or defaults anywhere."),
    _e("S27", "AI ad-production workflow: LLM writes, AI video renders, Ads Manager launches",
       DAMINI, "https://www.marketian.io/courses/Facebook-Ada--Video-Course-675d7f5ab3427a142bcfb60b",
       "creative",
       "Her live workflow: offer in, Claude writes hooks/angles/copy, "
       "Higgsfield renders video ads, Ads Manager launches. Mirrors "
       "this system's API Providers pipeline (Text, Video, then the "
       "approval-gated launch). Tool picks are her preference, not a "
       "system endorsement."),
    _e("S28", "Retargeting as a set of distinct strategies (7 slots)",
       DAMINI, "https://www.marketian.io/courses/Facebook-Ada--Video-Course-675d7f5ab3427a142bcfb60b",
       "funnel",
       "Retargeting is not one ad set: maintain a set of distinct "
       "retargeting strategies per profile (the 7 individual strategies "
       "are inside her paid course — only the structure is public, so "
       "only the structure is seeded)."),
    _e("S29", "Scaling as a system: ABO + CBO + lookalikes",
       DAMINI, "https://www.marketian.io/courses/Facebook-Ada--Video-Course-675d7f5ab3427a142bcfb60b",
       "scaling",
       "Scaling is taught as a system — ABO scaling, CBO scaling and "
       "lookalike scaling, with learning-phase discipline — instead of "
       "one big budget jump. In this system all scaling stays inside "
       "MAX_BUDGET_CHANGE_PCT and the caps."),
    _e("S30", "Competitor intelligence as a reporting habit",
       DAMINI, "https://www.marketian.io/courses/Facebook-Ada--Video-Course-675d7f5ab3427a142bcfb60b",
       "competitor_research",
       "Analysis + automated rules + competitor watching as ONE regular "
       "routine in reporting — not a one-off task. The loop's weekly "
       "cycle carries a competitor check for this reason."),
    _e("S31", "Tracking + account health as foundations",
       DAMINI, "https://www.marketian.io/courses/Facebook-Ada--Video-Course-675d7f5ab3427a142bcfb60b",
       "measurement",
       "Pixel AND CAPI together for accurate tracking; business "
       "verification done; a dedicated discipline for why ad accounts "
       "get banned — protect the account, stay compliant, recover fast."),
    _e("S32", "Monthly knowledge updates as an operating cadence",
       DAMINI, "https://www.marketian.io/",
       "knowledge",
       "Meta changes every month, so the playbook ships updates like "
       "software (her courses: 12 curriculum updates a year). This "
       "system mirrors it: the Meta Knowledge register is reviewed by "
       "the weekly job; strategy changes stay proposals."),
    _e("S33", "Simplify ruthlessly, in the audience's own language",
       DAMINI, "https://www.marketian.io/",
       "creative",
       "Explain so simply 'even your nani could run a campaign': "
       "everyday Hindi + English, zero jargon. Encoded as the copy "
       "style rule for Hinglish profiles in this system."),
    _e("S34", "Funnel architecture: free content, free community, low-ticket, bundle, agency",
       DAMINI, "https://www.marketian.io/",
       "funnel",
       "Observable funnel pattern: free weekly lessons, free WhatsApp "
       "community, low-ticket course, bundles, high-end agency. A "
       "reference funnel shape for education/services profiles."),
    _e("S35", "Offer architecture: lifetime access + updates + transparent pricing + tool bonuses",
       DAMINI, "https://www.marketian.io/courses/Meta-Ads--Ecommerce--AI-Masterclass--Ad-Creative-Mastery--WhatsApp-Blueprint-6ab4f68974bffa54d223a3c6",
       "funnel",
       "One-time price, lifetime access, no hidden charges, bonuses "
       "that are working tools (checklist, templates, swipe file).",
       note="Screened: trust copy may use ONLY real, verifiable numbers. "
            "Invented proof figures are DO-NOT-APPLY (see D8)."),
]

# ------------------------------------------- Practitioner playbook P1–P21
_KB_SRC = "https://summarize.ing/video-487977-The-Complete-Playbook-To-Running-Meta-Ads-in-2025"
PRACTITIONER_ENTRIES = [
    _e("P1", "Consolidate into Advantage+ and let the machine learn — Ben Heath",
       "Ben Heath (practitioner)", _KB_SRC, "structure",
       "Merge fragmented campaigns by objective, use Advantage+ with "
       "campaign-level budget, broad audiences + automatic placements, "
       "concentrate conversions so each ad set reaches meaningful "
       "weekly volume (~50 optimisation events/week is Meta's "
       "learning-phase guidance as commonly cited — a setting, not a "
       "hard rule)."),
    _e("P2", "Combine cold and warm audiences in one campaign — Ben Heath",
       "Ben Heath (practitioner)", _KB_SRC, "structure",
       "Put cold + warm in the same Advantage+ structure and "
       "differentiate by CREATIVE, not audience splits; watch warm "
       "frequency separately.",
       note="Contested practitioner choice — other respected "
            "practitioners still separate prospecting/retargeting. "
            "Per-profile choice, not consensus."),
    _e("P3", "Hook-swap variations to extend a winner's life — Ben Heath",
       "Ben Heath (practitioner)", _KB_SRC, "fatigue_refresh",
       "Keep the winning video's body, produce versions with a new "
       "first ~3 seconds, launch as new ads, retire the most fatigued "
       "original. Iteration (life extension), not diversification — "
       "pair with genuinely new concepts (P17/O3)."),
    _e("P4", "Test creative by duplicating — never edit a live ad — Ben Heath",
       "Ben Heath (practitioner)",
       "https://summarize.ing/video-73075-How-To-Test-New-Facebook-Ad-Creative-The-RIGHT-Way-",
       "creative",
       "Never edit a running ad (corrupts history, can restart "
       "learning). Duplicate and change the creative in the copy; judge "
       "on cost per result. His older framework's ad-count/day numbers "
       "are his settings, not rules."),
    _e("P5", "Separate testing ad set + weekly decision cadence — Smart Marketer / Ben Heath",
       "Smart Marketer playbook (practitioner)",
       "https://smartmarketer-data.s3.us-east-1.amazonaws.com/The+Smart+Marketer+Show/Season+02/Episode+11/EP+11+The+New+Meta+Ads+Playbook_+What+Changed,+What's+Working+&+What+To+Do+Next.pdf",
       "creative",
       "Test new creative in a SEPARATE ad set (new ads in a proven ad "
       "set often get no spend), run tests at least 7 full days, "
       "graduate winners, make changes on one fixed day per week.",
       note="Directly contradicts P21 (no separate testing campaign). "
            "Both are live 2026 practitioner positions — exposed as a "
            "per-profile choice; the system does not pick a side."),
    _e("P6", "'More ads' is not a strategy: distinctly different or don't bother — Jon Loomer",
       "Jon Loomer (practitioner)", "https://madgicx.com/blog/meta-andromeda",
       "creative",
       "Audit distinct CONCEPTS vs cosmetic variants before adding "
       "volume; Loomer reports 25–50 ads per ad set gave no clear "
       "benefit without variety. Start with a few meaningful "
       "variations."),
    _e("P7", "Don't blame Andromeda — diagnose in order — Jon Loomer",
       "Jon Loomer (practitioner)", "https://ppc.land/andromeda/",
       "optimisation",
       "On any sudden drop, check in order: (1) tracking/signal "
       "health, (2) budget changes, (3) the offer, (4) landing page, "
       "(5) creative age/fatigue — only then (6) platform changes."),
    _e("P8", "One CBO per product per country; scale ~20%/day — Nick Theriot",
       "Nick Theriot (practitioner)", "https://www.youtube.com/watch?v=msb8NgH-Kxk",
       "scaling",
       "One CBO campaign per product per country; scale in ~20% daily "
       "steps while CPA holds (in this system the % is the owner's "
       "MAX_BUDGET_CHANGE_PCT); expand proven campaigns to new "
       "countries."),
    _e("P9", "Bottleneck diagnosis: CPC / CVR / AOV — Nick Theriot",
       "Nick Theriot (practitioner)",
       "https://youtubetotranscript.com/transcript?v=kbh5i-yqLag",
       "optimisation",
       "High CPC = creative problem (fix creative first). Low "
       "landing-page CVR = page/offer match. Low AOV = upsells/"
       "bundles. A test creative at multiples of average CPC is a "
       "creative failure, not a budget problem."),
    _e("P10", "Angles exhausted? Change the MESSAGE/persona, not the volume — Nick Theriot",
       "Nick Theriot (practitioner)",
       "https://youtubetotranscript.com/transcript?v=CbhA6yk8RNo",
       "research",
       "If 10–15 creatives/week produce no net-new winners, the "
       "message is exhausted: find a new persona/repositioning. His "
       "dip rule of thumb: let a tanking result run ~72 hours before "
       "intervening. (His case revenue figures are self-reported and "
       "are NOT imported.)"),
    _e("P11", "Hook craft: pattern-break in the first 2–3 seconds — Nick Theriot",
       "Nick Theriot (practitioner)", "https://threadreaderapp.com/user/nicktheriot_",
       "creative",
       "Design what is SEEN and SAID in the first ~3 seconds; apply a "
       "pattern break; rotate hook frameworks (question, bold "
       "statement, scenario, customer words) per angle.",
       note="Compliance flag from the knowledge base: his 'If you're "
            "[demographic]…' framework can collide with Meta's "
            "personal-attributes standard — see DO-NOT-APPLY D2 for "
            "the safe rewrite pattern."),
    _e("P12", "Roadmap creative volume FROM the budget — Dara Denney",
       "Dara Denney (practitioner)",
       "https://www.omgcommerce.com/ecommerce-evolution-podcast/crafting-ad-creative-that-converts-combining-data-boldness",
       "creative",
       "Start from monthly spend to set the creative-test cadence "
       "(her example ratio: ~$100K/month ≈ 3–4 tests/week). Too few "
       "tests starve a big account; too many waste a small one. Ratio "
       "is a planning setting, not a default."),
    _e("P13", "Proven low-cost formats: benefit callouts, us-vs-them, 'ugly' ads, one-take video — Dara Denney",
       "Dara Denney (practitioner)",
       "https://youtubetotranscript.com/transcript?v=NsHk8o3jVvM",
       "creative",
       "Benefit-callout statics, us-vs-them comparisons, 'ugly' ads "
       "(e.g. post-it note), one-take phone-shot video — iPhone "
       "content routinely beats studio setups in her testing.",
       note="Compliance flag: us-vs-them with a competitor's name/logo "
            "carries trademark/defamation risk — see DO-NOT-APPLY D6. "
            "Feature/price comparisons must be publicly verifiable."),
    _e("P14", "Tag everything; iterate / reskin / rethink buckets — Dara Denney",
       "Dara Denney (practitioner)", "https://www.daradenney.com/",
       "optimisation",
       "Tag every ad by persona, angle, motivation, format; index "
       "performance to the target KPI (spend-weighted). Buckets: "
       "ITERATE (winners to variations), RESKIN (good idea, tired "
       "execution to new briefs), RETHINK (losers to stop). Balance "
       "iteration with periodic bold swings."),
    _e("P15", "Crazy Method: scale by duplicating the winner with NEW creatives — Konstantinos Doulgeridis",
       "Konstantinos Doulgeridis (practitioner)",
       "https://www.facebookads-master.com/mentorship-1", "scaling",
       "Keep the winner's structure/audience, duplicate the campaign "
       "loaded with 3–4 DIFFERENT new creatives, scale spend across "
       "duplicates. Duplicating with the SAME creatives fails "
       "(fatigue) — the new creatives are the mechanism."),
    _e("P16", "Micro-scaling rule: small daily % while CPA holds, guarded by caps — Konstantinos Doulgeridis",
       "Konstantinos Doulgeridis (practitioner)",
       "https://www.summarize.tech/www.youtube.com/watch?v=EWSPDXmDQ64",
       "scaling",
       "If cost per result holds under target over a trailing window, "
       "nudge the daily budget up by a small % (his example: 2%/day), "
       "always under a maximum cap and a cost cap. In this system "
       "this maps to proposal-first automation inside owner caps — "
       "never an unbounded auto-rule. Parameters are approximate "
       "(AI-summary source)."),
    _e("P17", "Creative diversity IS the targeting now — Andrew Foxwell / Foxwell Digital",
       "Foxwell Digital (practitioner)",
       "https://www.foxwelldigital.com/blog/creative-diversity-in-meta-ads-the-golden-ticket-to-success",
       "creative",
       "Each distinct creative acts as an audience: Andromeda/GEM "
       "match ads to people by content; near-identical ads compete "
       "for the same small pool. Diversify formats AND statics; "
       "build around sub-avatars. (Concept counts cited in the "
       "community are heuristics, NOT Meta numbers — see O3.)"),
    _e("P18", "Watch the Creative Diversity metric; force-test fresh ads — Foxwell Digital",
       "Foxwell Digital (practitioner)",
       "https://www.foxwelldigital.com/blog/is-detailed-targeting-dead-what-foxwell-members-are-seeing-post-andromeda",
       "optimisation",
       "Check Ads Manager's Creative Diversity metric; when fresh "
       "ads get no spend inside a live campaign, use Meta's Push "
       "Delivery (as reported by Foxwell) to force a test, then judge "
       "on the gated ladder (P20).",
       note="UNVERIFIED: Push Delivery's exact availability/eligibility "
            "was not confirmed from a Meta page in the research pass."),
    _e("P19", "CAPI lead-quality loop: optimise for the QUALIFIED stage — practitioner guides",
       "Practitioner guides synthesising Meta Conversion Leads guidance",
       "https://www.cutthelag.com/blog/meta-conversions-api-b2b-lead-generation",
       "measurement",
       "Track lead stages in a CRM; send Lead Created / Contacted / "
       "Sales Qualified / Converted back via CAPI (pixel + CAPI, same "
       "event_id, Event Match Quality target 8+); optimise for the "
       "QUALIFIED stage (reached by roughly a third to a half of "
       "leads), not the closed deal. Directly matches this system's "
       "cost-per-QUALIFIED-lead metric. (The ~19% cost figure guides "
       "cite is Meta's, via guides — not a system benchmark.)"),
    _e("P20", "Gated creative-testing ladder: concept, angle, hook, format — practitioner synthesis",
       "CapConvert / Convrt / The Performers (practitioner synthesis)",
       "https://www.capconvert.com/learn/blog/meta-ads-creative-testing-framework",
       "creative",
       "Test in variance order: CONCEPT, then ANGLE, then HOOK, then "
       "FORMAT. Judge through gates in order: hook rate, hold rate, "
       "CTR, landing-page conversion, and CPA/ROAS as the ONLY final "
       "verdict; diagnose by which gate failed. Prefer Meta's A/B "
       "test tool for clean splits. (Hook-rate zones cited are "
       "practitioner norms, not Meta thresholds.)"),
    _e("P21", "One CBO per product, ad sets as folders, no separate testing campaign — Brad / Scalability School",
       "Brad, Scalability School (practitioner)",
       "https://www.scalabilityschool.com/scalability-school-podcast/inside-the-ad-acount-how-to-do-creative-testing-in-2026",
       "structure",
       "Single CBO campaign per product; ad sets as organisational "
       "folders; stack new ads into the main campaign; validate with "
       "incrementality checks rather than last-click comparisons.",
       note="Directly contradicts P5 (separate testing ad set). Both "
            "are live 2026 practitioner positions — per-profile "
            "choice; the system does not pick a side."),
]

# ------------------------------------------------------ Book-derived B1–B4
BOOK_ENTRIES = [
    _e("B1", "Deep Funnel Marketing: build retargeting FIRST, sequence by awareness — Bob Regnerus",
       "Ultimate Guide to Facebook Advertising, 4th ed. (book, practitioner)",
       "https://bobregnerus.com/facebook-advertising/the-power-of-deep-funnel-marketing-in-your-facebook-advertising/",
       "funnel",
       "Map the Customer Awareness Timeline (unaware to most-aware). "
       "Build BOTTOM first (checkout/order-form abandoners: "
       "testimonials, objection-handling video), then MIDDLE "
       "(nurture viewers/visitors), then TOP (content ads that sort "
       "audiences by engagement). Reverse-engineer every stage from "
       "the final event. Andromeda-era note: implement stages as "
       "distinct creative sets inside consolidated structures (P1), "
       "not micro-targeted ad sets."),
    _e("B2", "Design what happens AFTER the click: 10 seconds, 10 minutes, days/weeks — Ultimate Guide (4th ed.)",
       "Ultimate Guide to Facebook Advertising, 4th ed. (book, practitioner)",
       "https://www.google.nl/books/edition/Ultimate_Guide_to_Facebook_Advertising/YdoBEAAAQBAJ",
       "optimisation",
       "Audit the first 10 seconds on the page (message match), the "
       "first 10 minutes (speed, form friction, follow-up), and the "
       "following days/weeks (email + retargeting sequence). Results "
       "are decided as much by the post-click chain as by the ad."),
    _e("B3", "Full-funnel completeness checklist + annual-update discipline — Brian Meert",
       "The Complete Guide to Facebook Advertising (book, practitioner)",
       "https://startupmindset.com/the-complete-guide-to-running-facebook-ads-in-2020-our-interview-with-advertisemint-ceo-brian-meert/",
       "structure",
       "Work a complete setup checklist (Business Manager, structure, "
       "funnel, creative, placements) and treat any printed playbook "
       "as perishable — re-verify against Meta's current docs each "
       "cycle. (The book's 2017–2020 platform mechanics are obsolete "
       "post-Andromeda; only the completeness/discipline layer is "
       "carried.)"),
    _e("B4", "Hypothesis testing: use paid ads as a laboratory — Brendan Kane",
       "One Million Followers (book, practitioner, via public summary)",
       "https://booksummary101.com/one-million-followers-summary/",
       "research",
       "Write the hypothesis first (audience + angle), run small-"
       "budget paid tests to measure real response, kill failures "
       "fast, move proven winners into full production; pair paid "
       "learning with organic posting.",
       note="Translate 'winning content' into the owner's business KPI "
            "(qualified leads/sales) before applying; ignore the "
            "30-day million-follower framing entirely (see D3)."),
]

# ------------------------------------------------------------ DO-NOT-APPLY
DO_NOT_APPLY_ENTRIES = [
    _e("D1", "DO NOT APPLY: Engagement bait",
       "Meta Advertising Standards (via knowledge base D1)",
       "https://transparency.meta.com/policies/ad-standards/", "creative",
       "'Comment YES', 'Tag a friend', 'Share to win', vote-with-"
       "reactions mechanics.",
       status="DO_NOT_APPLY",
       note="Meta treats engagement bait as low-quality/spammy content "
            "— distribution penalties and rejections. Earn engagement "
            "with the creative itself (P11)."),
    _e("D2", "DO NOT APPLY: Implying personal attributes in copy or hooks",
       "Meta Advertising Standards (via knowledge base D2)",
       "https://www.launchguarding.com/blog/meta-personal-attributes",
       "creative",
       "Copy asserting/implying the viewer HAS a trait ('Do you have "
       "diabetes?', 'Are you overpaying…?', 'If you're a [trait]…') "
       "for health, finance, age, religion, race, gender identity, "
       "disability and similar traits. Questions count as implying.",
       status="DO_NOT_APPLY",
       note="Meta's own pair: 'New diabetes treatment available' = "
            "allowed; 'Do you have diabetes?' = NOT allowed. Describe "
            "the product and its benefit, never the viewer's "
            "condition. The single most common 2026 rejection "
            "trigger."),
    _e("D3", "DO NOT APPLY: Guaranteed / unrealistic outcome claims",
       "Meta Advertising Standards (via knowledge base D3)",
       "https://transparency.meta.com/policies/ad-standards/", "creative",
       "'Ten-fold return', 'profitable from day one', '1 million "
       "followers in 30 days', guaranteed income/placement/returns, "
       "specific results in a set timeframe.",
       status="DO_NOT_APPLY",
       note="Misleading claims (fraud/deception) under Meta's "
            "standards; the owner's brief also bans invented results/"
            "ROI and guarantees. Verifiable product facts only, and "
            "only for eligibility-confirmed offerings."),
    _e("D4", "DO NOT APPLY: Cloaking, fake scarcity, landing-page mismatch",
       "Meta Advertising Standards (via knowledge base D4)",
       "https://transparency.meta.com/policies/ad-standards/", "go_live",
       "Showing reviewers a different page than users; countdown/"
       "scarcity that is not real; ads promising content the landing "
       "page does not deliver; curiosity-gap withholding.",
       status="DO_NOT_APPLY",
       note="Circumventing-systems + low-quality standards; an "
            "account-ban risk, not just a rejection. Ad promise must "
            "equal the landing-page headline; real deadlines only."),
    _e("D5", "DO NOT APPLY: Health-context clickbait and cure claims",
       "Meta Health and Wellness standards (via knowledge base D5)",
       "https://www.everyfriday.co/guides/meta-health-wellness-ad-policy",
       "creative",
       "Cure/heal claims for listed conditions, sensational "
       "before/after framing outside current rules, specific health "
       "outcomes in a set timeframe without disclaimers.",
       status="DO_NOT_APPLY",
       note="Cross-industry reminder; the Health & Wellness preset "
            "pack already blocks the specific patterns."),
    _e("D6", "DO NOT APPLY (without legal check + owner approval): competitor name/logo in comparison ads",
       "Knowledge base D6 (risk flagged by the practitioner herself)",
       "https://youtubetotranscript.com/transcript?v=NsHk8o3jVvM",
       "creative",
       "Us-vs-them ads executed with a real competitor's logo/name "
       "and unverified superiority claims.",
       status="DO_NOT_APPLY",
       note="Trademark/defamation/comparative-advertising risk. "
            "System rule: comparisons may use publicly verifiable "
            "FEATURES/PRICES only, never competitor logos, and need "
            "owner approval."),
    _e("D7", "DO NOT APPLY: Stripping AI disclosure / watermarks from generated creative",
       "Meta 2026 Ad Terms (via knowledge base D7/O10)",
       "https://transparency.meta.com/policies/ad-standards/", "creative",
       "Removing AI watermarks or authenticity metadata from "
       "Advantage+ or third-party AI-generated assets.",
       status="DO_NOT_APPLY",
       note="Meta's updated Ad Terms make the advertiser responsible "
            "for AI-generated content and prohibit removing AI "
            "authenticity data. Keep disclosures; keep the human "
            "visual check before the approval queue."),
    _e("D8", "DO NOT APPLY: Fake social proof",
       "Meta Advertising Standards (via knowledge base D8)",
       "https://transparency.meta.com/policies/ad-standards/", "creative",
       "Invented testimonials, purchased reviews, fabricated "
       "'someone just bought' notifications, rented/celebrity "
       "likenesses without rights.",
       status="DO_NOT_APPLY",
       note="Deceptive practices; celebrity/brand bait is explicitly "
            "prohibited. Also matches the owner's standing rule "
            "against fabricated purchase messages. Real proof with "
            "permission, or none."),
    _e("D9", "DO NOT APPLY: Cosmetic duplication to 'game' creative grouping",
       "Meta creative-diversification definition (via knowledge base D9/O3)",
       "https://riffkit.ai/blog/meta-andromeda-creative-diversity",
       "creative",
       "Near-identical uploads with trivial changes (CTA text swaps, "
       "background colour) presented as 'new creatives' to exploit "
       "rumoured similarity percentages ('under 40% similar', '60% "
       "suppresses delivery').",
       status="DO_NOT_APPLY",
       note="Meta has published NO similarity threshold; the practice "
            "contradicts Meta's diversification definition and wastes "
            "budget on shared learning. The system counts CONCEPTS "
            "honestly."),
]

# ------------------------------------- Winner habits + viral patterns
# From the winner-patterns research (report §B winner habits B1–B14 and
# §C viral creative patterns C1–C9, read 2026-11-16), seeded as
# PRACTITIONER/CASE entries (ids W*/V* here to avoid clashing with the
# book-derived B* ids above). Agency case numbers in that report are
# SELF-REPORTED by the agencies selling the service (report §F
# quarantine) — they are evidence the habits are practised, NOT proof
# of effect sizes, and are never imported as benchmarks or defaults.
WP = "winner-patterns report (2026-11-16)"
WINNER_HABIT_ENTRIES = [
    _e("W1", "Consolidated structure: few ad sets, each able to exit learning (report B1)",
       "Winner habit — PRACTITIONER/CASE", "https://lineardesign.com/blog/facebook-ad-mistakes/",
       "structure",
       "Fragmentation is the most-cited structural difference between "
       "winners and losers: size audiences/budgets so each ad set can "
       "plausibly reach the learning threshold weekly. (The report's "
       "47-to-8 ad sets CPL case is agency-reported — method only.)"),
    _e("W2", "Pixel + CAPI together, clean events, BEFORE spending (report B2)",
       "Winner habit — PRACTITIONER + CASE (self-reported)",
       "https://www.codecafelab.in/case-studies/meta-ads-roas-case-study",
       "measurement",
       "Tracking is a precondition, not an optimisation: Pixel + "
       "Conversions API with dedupe installed and verified before the "
       "first rupee of spend (matches Damini S31)."),
    _e("W3", "Protect the learning phase like an asset (report B3)",
       "Winner habit — PRACTITIONER", "https://www.relevantaudience.com/facebook-ads/how-to-scale-facebook-ads/",
       "optimisation",
       "No significant edits until the ad set exits learning; a "
       "launched ad runs at least a week untouched; decisions on "
       "7–14 day windows, not yesterday's numbers (Damini S4/S14)."),
    _e("W4", "Feed automation data first, then let it scale (report B4)",
       "Winner habit — PRACTITIONER", "https://www.marketian.io/blog/meta-andromeda-era-where-creatives-rule-and-targeting-dies",
       "scaling",
       "Manual campaigns test and teach who converts; then "
       "Advantage+/Andromeda scales. Run manual + AI as a mix, "
       "backups ready before the winner saturates (Damini S12/S17/S18)."),
    _e("W5", "Test creative in volume, as a system (report B5)",
       "Winner habit — PRACTITIONER", BLOG + "my-learnings-after-spending-crores-on-facebook-ads",
       "creative",
       "Frameworks, checklists, swipe files — never a blank page. "
       "Creative is the first diagnosis when results dip: fix the "
       "creative before touching the budget (Damini S6/S24/S26)."),
    _e("W6", "Diversify creative: one product, dozens of genuinely different ads (report B6)",
       "Winner habit — PRACTITIONER + OFFICIAL mechanic", BLOG + "meta-andromeda-era-where-creatives-rule-and-targeting-dies",
       "creative",
       "Angle expansion across concepts/formats/hooks — Meta groups "
       "similar ads as one retrieval candidate, so real diversity "
       "expands delivery, not file count (Damini S22/S23; register O3)."),
    _e("W7", "Lookalikes from real customer data, not guessed interests (report B7)",
       "Winner habit — PRACTITIONER", BLOG + "how-to-run-meta-ads-for-small-budgets",
       "scaling",
       "Build lookalikes from actual customers so spend goes to "
       "measured right-fit audiences; lookalikes also power scaling "
       "alongside ABO/CBO (Damini S16/S29)."),
    _e("W8", "Funnel: cold to warm to hot, per-segment creative (report B8)",
       "Winner habit — PRACTITIONER + CASE", "https://www.growthroom.co/en/blog-posts/growth-room-meta-ads-results-a-summary-of-our-client-case-studies",
       "funnel",
       "Awareness/engagement first, then segmented retargeting — "
       "visitors, viewers and abandoners each get different creative "
       "and copy (Damini S9/S2)."),
    _e("W9", "The landing page is part of the ad (report B9)",
       "Winner habit — PRACTITIONER + CASE (self-reported)",
       "https://www.codecafelab.in/case-studies/meta-ads-roas-case-study",
       "go_live",
       "Mobile-first page whose headline/offer matches the ad "
       "exactly; a below-average conversion-rate ranking is a "
       "page/offer problem, not a creative problem (Damini S7)."),
    _e("W10", "Manage ad comments like a storefront (report B10)",
       "Winner habit — PRACTITIONER (+ OFFICIAL quality mechanism)", BLOG + "my-learnings-after-spending-crores-on-facebook-ads",
       "monitoring",
       "Monitor live ads' comments; address/remove negative pile-ups "
       "and fix the root cause — visible negativity scares later "
       "viewers and negative feedback feeds ad quality (Damini S8)."),
    _e("W11", "Scale in small steps; keep a critical-CPA guardrail (report B11)",
       "Winner habit — PRACTITIONER", "https://www.olbuz.com/blog/scale-meta-ad-spend-without-killing-your-roas",
       "scaling",
       "Small vertical steps (practitioner rule of thumb ~+20% every "
       "3–5 days — an owner setting here, never a default) or "
       "horizontal duplication into fresh audiences; a predefined "
       "critical-CPA line pauses/rolls back the scale attempt."),
    _e("W12", "Small budgets concentrate on ONE hero product (report B12)",
       "Winner habit — PRACTITIONER", BLOG + "how-to-run-meta-ads-for-small-budgets",
       "structure",
       "Best-seller with margin, a few ad sets, tested vigorously — "
       "instead of splitting a small budget across the catalogue so "
       "nothing exits learning (Damini S11/S13)."),
    _e("W13", "Fix attribution plumbing before blaming creative (report B13)",
       "Winner habit — CASE (self-reported, client anonymised)",
       "https://rockpapermarketing.io/case-studies/video-teleprompter-editor-app",
       "measurement",
       "Measurement routing (web-to-app attribution links) can be "
       "the whole win — check tracking/attribution before any "
       "creative verdict. (Case figures self-reported; method only.)"),
    _e("W14", "When creative is the problem, change ONLY the creative (report B14)",
       "Winner habit — CASE (self-reported)", "https://sweatpantsagency.com/facebook-marketing-case-study",
       "creative",
       "Single-variable discipline at the strategy level: a "
       "creative-strategy overhaul with targeting untouched proved "
       "the diagnosis. (Case figures self-reported; method only.)"),
]

VIRAL_PATTERN_ENTRIES = [
    _e("V1", "Hook in 1–3 seconds: interrupt + promise + qualification (report C1)",
       "Viral creative pattern — PRACTITIONER", "https://www.adsights.ai/resources/guides/video-ad-hook-optimization-guide",
       "creative",
       "Interrupt the scroll, promise a payoff, qualify the viewer — "
       "in under 3 seconds. Failure modes: logo slates, slow pans, "
       "context before tension."),
    _e("V2", "Winning hooks skew negative and declarative (report C2)",
       "Viral creative pattern — PRACTITIONER", "https://www.adside.ai/blog/ad-hooks-first-three-seconds",
       "creative",
       "In the cited analysis of 550+ winning video ads, most opened "
       "with something negative (warning/mistake/problem) and as a "
       "statement rather than a question. (Source's analysis — a "
       "pattern to test, not a rule.)"),
    _e("V3", "Hook rate is the early-warning metric (report C3)",
       "Viral creative pattern — PRACTITIONER", "https://www.adside.ai/blog/ad-hooks-first-three-seconds",
       "creative",
       "Hook rate = 3-sec views / impressions; hold rate confirms "
       "the body keeps the attention. Working ranges in the sources "
       "are practitioner ranges — in this system the floor is the "
       "owner's HOOK_RATE_FLOOR_PCT setting, never a default."),
    _e("V4", "Native/UGC grammar beats studio polish (report C4)",
       "Viral creative pattern — PRACTITIONER", "https://www.adside.ai/blog/ad-hooks-first-three-seconds",
       "creative",
       "Selfie-style talking head, face-to-camera in the first "
       "frames, no logo intro. Corporate voice is a death pattern "
       "(Damini S25); UGC/Founder/First-Person formats are in the "
       "S22 taxonomy."),
    _e("V5", "Platform-native formulas: comment-reply and curiosity-gap listicle (report C5)",
       "Viral creative pattern — PRACTITIONER", "https://videoai.me/blog/video-ad-hooks-tested-scroll-stopping-formulas",
       "creative",
       "Answer a sceptical comment on camera (native UI signals "
       "'content, not ad'), or open a numbered curiosity gap the "
       "full video closes. (Test-set figures are the source's.)"),
    _e("V6", "Demo-first: the product does the thing in frame one (report C6)",
       "Viral creative pattern — PRACTITIONER", "https://www.adsights.ai/resources/guides/video-ad-hook-optimization-guide",
       "creative",
       "Product visibly working in the first second, before "
       "narration; the hook must also land muted — bold on-screen "
       "text and high contrast in frame one (feed autoplay is "
       "sound-off)."),
    _e("V7", "One concept, many hooks: 3–5 hook variants per body (report C7)",
       "Viral creative pattern — PRACTITIONER", "https://www.adside.ai/blog/ad-hooks-first-three-seconds",
       "creative",
       "Test hooks against an identical body so the hook is the only "
       "variable; judge on early retention first, CPA second — a "
       "hook can win attention and still lose if the promise "
       "mismatches the video."),
    _e("V8", "Freshness is a distribution strategy: rotate on a 1–4 week cadence (report C8)",
       "Viral creative pattern — PRACTITIONER", "https://www.palmador.ai/en/blog/video-ad-hooks",
       "fatigue_refresh",
       "Creative half-life at aggressive spend is short "
       "(practitioner reports: 7–14 days); rotating hook variants "
       "every 1–4 weeks is the standing defence (Damini S1)."),
    _e("V9", "Specificity beats breadth in the message (report C9)",
       "Viral creative pattern — PRACTITIONER", BLOG + "how-to-run-meta-ads-for-small-budgets",
       "creative",
       "One creative, one specific audience, one specific CTA "
       "(Damini S15); Hinglish pain-point headline and old-way vs "
       "new-way contrast are her demonstrated shapes."),
]

ENTRIES = (DAMINI_ENTRIES + PRACTITIONER_ENTRIES + BOOK_ENTRIES
           + WINNER_HABIT_ENTRIES + VIRAL_PATTERN_ENTRIES
           + DO_NOT_APPLY_ENTRIES)

# Creative format taxonomy (Damini S22, screened) — used by inspiration
# briefs. "Before vs After" is excluded for health profiles at brief
# time (the health compliance pack blocks the copy anyway).
FORMAT_TAXONOMY = [
    "UGC", "Value-Based", "Quirky/Meme", "Educational", "AI Ads",
    "Us vs Them", "Before vs After", "Statistics", "Ugly Ads",
    "Founder", "Testimonial", "Podcast", "Street Interview",
    "Mini Drama", "Calling-Out", "First Person", "In-Office",
    "Ad Review", "Ask-Me-Anything", "Storytelling", "Mini Vlog",
    "Screen Recording",
]


def all_entries(conn=None):
    """Seed entries + any owner-added DB rows (table strategy_entries,
    created by the web UI later — data-only extension point)."""
    entries = [dict(e) for e in ENTRIES]
    if conn is not None:
        try:
            rows = conn.execute("SELECT * FROM strategy_entries").fetchall()
        except Exception:
            rows = []
        import json as _json
        for r in rows:
            try:
                entries.append(_json.loads(r["entry_json"]))
            except (ValueError, KeyError, TypeError):
                continue
    return entries


def active_entries(conn=None):
    return [e for e in all_entries(conn) if e.get("status") == "ACTIVE"]


def do_not_apply_entries(conn=None):
    return [e for e in all_entries(conn) if e.get("status") == "DO_NOT_APPLY"]


def entries_for_stage(stage, conn=None):
    return [e for e in active_entries(conn) if e.get("stage") == stage]


def get_entry(entry_id, conn=None):
    for e in all_entries(conn):
        if e.get("id") == entry_id:
            return e
    return None
