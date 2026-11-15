"""Policies Register — SH Ads Desk.

Seeded from the Meta policies digest
(~/workspace/research_notes/meta-ads-winner-patterns-20261116/
meta-policies-digest.md, accessed 2026-11-16). Flags are preserved
EXACTLY as the digest recorded them:

- "OFFICIAL (via secondary — flagged)": official content that could NOT
  be opened on a Meta domain in the research environment
  (facebook.com/business and Help Center pages return 403 there) and
  was verified through secondary sources quoting Meta. Re-verify from
  a normal browser before quoting externally. These flags must NOT be
  upgraded without that re-check.
- §9 (2026 Ad Terms) is stored as CONTESTED / DISPUTED: one tracker
  reports the update was paused on 5 Nov 2026 with no new date, while
  other sources write as if the 30 Oct terms are in force.
- §4 personal attributes: the Transparency Center list and the Help
  Center list do NOT perfectly match — this register (and the policy
  checker) enforces the UNION of both lists.
- §10 is Indian law/industry guidance, NOT Meta policy.

This digest is a working summary, not legal advice. Policies change;
each entry carries its last-checked date.
"""

DATE_CHECKED = "2026-11-16"
FLAGGED = "OFFICIAL (via secondary — flagged)"


def _p(id_, title, category, rule, url, status=FLAGGED, note=""):
    return {"id": id_, "title": title, "category": category, "rule": rule,
            "source_url": url, "date_checked": DATE_CHECKED,
            "status": status, "note": note}


POLICIES = [
    _p("PR1", "Advertising Standards — structure",
       "framework",
       "Meta ke ad rules Meta Advertising Standards (Transparency "
       "Center) me hain — Community Standards aur Commerce Policies ke "
       "saath. Chaar principles: unsafe/discriminatory practices se "
       "bachav, fraud/scams rokna, positive user experience, ad "
       "transparency. Enforcement sabse aggressive wahin hota hai: "
       "deception, personal-attribute targeting, discrimination, "
       "identity verification.",
       "https://adsuploader.com/blog/meta-ad-guidelines"),
    _p("PR2", "Prohibited content (kabhi allowed nahi)",
       "prohibited",
       "Illegal products/services (target jurisdiction me); "
       "discriminatory practices; tobacco/drugs/weapons/adult content "
       "(narrow age-gated exceptions kuch sub-categories me); "
       "misleading/false content — deceptive claims, unrealistic "
       "results, miracle framing, fake scarcity/clickbait, review ko "
       "circumvent karna; personal-data violations; sensational/"
       "violent content; third-party rights infringement.",
       "https://adsuploader.com/blog/meta-ad-guidelines"),
    _p("PR3", "Restricted content (conditions ke saath allowed)",
       "restricted",
       "Alcohol (legal + age targeting); financial products (18+, "
       "90-din-se-kam full-repayment loans banned, discriminatory "
       "lending targeting banned); health & wellness — July 2026 "
       "update: general cosmetic before/after images ab 18+ targeting "
       "ke saath allowed, appearance insults aur disease-cure claims "
       "ab bhi banned; gambling/crypto/weight-management/dating — "
       "har ek ki apni permission/age/geo conditions, kuch par Meta "
       "ki prior written permission chahiye.",
       "https://www.relevantaudience.com/facebook-ads/facebook-ad-banned-words-meta-policy/",
       note="Health note: ye system apne Health preset me before/after "
            "ko ab bhi block karta hai (owner ki sakht pasand) — Meta "
            "ki July 2026 relaxation register me note hai, gate "
            "owner hi badlega."),
    _p("PR4", "Personal attributes rule (Privacy Violations and Personal Attributes)",
       "prohibited",
       "Ads private information share/maang nahi sakte, aur viewer ke "
       "paas koi personal attribute hai — ye ASSERT ya IMPLY nahi kar "
       "sakte, sawal poochh kar bhi nahi. Ye ek COPY rule hai, "
       "targeting rule nahi: product describe karo, viewer ko "
       "diagnose mat karo. Register dono official lists ka UNION "
       "enforce karta hai (neeche PERSONAL_ATTRIBUTES_UNION). Broad "
       "references jo list me nahi (jaise 'American') allowed; gender/"
       "age-group ka passing reference allowed, lekin kisi ki exact "
       "age imply karna (jaise 'just turned 62') violation hai.",
       "https://meta-ads.si/personal-attributes-ad-policy/"),
    _p("PR5", "Special Ad Categories (creation par declare karna mandatory)",
       "process",
       "Har campaign par Special Ad Category value (incl. NONE) "
       "lagti hai: HOUSING, EMPLOYMENT, FINANCIAL_PRODUCTS_SERVICES "
       "(Oct 2024 me aaya; 14 Jan 2025 ko purane CREDIT ko replace "
       "kiya; US-based/US-audience advertisers ke liye 21 Jan 2025 "
       "se required), ISSUES_ELECTIONS_POLITICS. Housing/Employment/"
       "Financial declare karne par targeting forcibly restricted: "
       "age 18–65+, gender all, koi ZIP targeting/location "
       "exclusions nahi, koi lookalikes nahi, detailed targeting "
       "pre-approved set tak. Bina declare kiye covered ad = reject.",
       "https://www.adflint.com/blog/special-ad-categories-setup"),
    _p("PR6", "Ad review process",
       "process",
       "Review primarily automated, aam taur par 24 ghante me; "
       "restricted categories me zyada time. Meta koi banned-words "
       "list publish NAHI karta — poora ad (image, video, text, "
       "targeting AUR landing page) Standards ke against dekha jata "
       "hai. Rejected ad ko edit karke resubmit ya re-review request "
       "ho sakta hai; rejected ad DELETE mat karo (re-review ka "
       "mauka ja sakta hai); har ad ko ek re-review, ~48 ghante me "
       "faisla; overturned rejection violation nahi ginti. Review "
       "pass hona local law ki guarantee nahi hai.",
       "https://www.relevantaudience.com/facebook-ads/facebook-ad-banned-words-meta-policy/"),
    _p("PR7", "Account Quality, restrictions aur consequences",
       "process",
       "Enforcement chaar asset levels par: personal profile, Page, "
       "business portfolio, ad account (Account Quality / Business "
       "Support Home me dikhta hai). Restriction = limited "
       "capability; Disabled = account/ads off, purana balance "
       "payable rehta hai; policy-disabled account 6 mahine "
       "ineligible rahe to reinstatement band. Grounds: severe/"
       "repeated violations; review/enforcement ko evade karna "
       "(naye accounts, cloaking, review se bachne wali "
       "misspellings — severe); inauthentic accounts; payment "
       "issues. COST CONSEQUENCE: baar-baar policy-violating ya "
       "low-quality ads par Meta Page/domain/account ke SAARE ads "
       "ko lower quality manne lagta hai — ban se pehle hi sab "
       "mehnga. Reviews limited, faisla final; pehle cause fix "
       "karo, replacement accounts mat kholo.",
       "https://adadvisor.ai/blog/facebook-ad-account-banned"),
    _p("PR8", "AI-generated content — labelling aur disclosure",
       "process",
       "AI images/AI-assisted creative jahan ads allowed hain wahan "
       "allowed; labelling primarily Meta ka kaam: Meta apne "
       "generative tools ya detected third-party tools (Photoshop, "
       "DALL·E) se bane/significantly edited content ko C2PA jaise "
       "signals se automatically label karta hai — label advertiser "
       "hata nahi sakta. Photorealistic AI human par label Sponsored "
       "ke paas; minor edits par koi label nahi. 1 June 2026 se "
       "detection third-party tools tak badha; optional "
       "self-disclosure bhi hai. Mandatory advertiser duty: social "
       "issues/elections/politics ads me AI se bana photorealistic "
       "person/realistic audio/event disclose karna (11 Jan 2024 "
       "se) — bina disclosure ke ad remove ho sakta hai.",
       "https://www.showfolk.ai/blog/ai-generated-images-facebook-ads-rules"),
    _p("PR9", "2026 Ad Terms — AI/automation ki zimmedari advertiser par",
       "terms",
       "Updated Commercial Terms + Self-Serve Ad Terms (announced "
       "8 Oct 2026; originally effective 30 Oct 2026): (1) har ad ki "
       "zimmedari advertiser ki — 'even when you use our automated "
       "features'; Meta ka tool galat claim likhe to bhi ad "
       "tumhara hai. (2) AI features galti kar sakte hain; risk "
       "advertiser ka. (3) AI watermarks/authenticity metadata "
       "alter/remove karna mana hai. (4) Tumhare connected "
       "third-party software/services (API tools, AI agents) ki "
       "zimmedari bhi tumhari. (5) Meta ke tests me tumhara "
       "creative shamil ho sakta hai; crawling rights badhe. "
       "(6) Prepaid credits par 3-year window; results/reporting "
       "accuracy ki koi promise nahi. (7) Ad-creative AI inputs par "
       "Meta ko perpetual royalty-free licence.",
       "https://monolithdesign.agency/insights/meta-ad-terms-october-30-2026-ai-changes",
       status="CONTESTED",
       note="DISPUTED: ek tracker (adtestbench) kehta hai update "
            "30 Oct se 20 Nov 2026 par gaya aur phir 5 Nov 2026 ko "
            "bina nayi date ke PAUSE ho gaya; dusre sources 30 Oct "
            "terms ko in-force likhte hain. Register entry: "
            "'announced; in-force date disputed/paused — Meta ki "
            "terms pages par re-verify kiye bina rely mat karo.' "
            "Points 1–4 ke principles purane terms/Generative AI "
            "Terms (6 May 2024 se in force) se bhi overlap karte "
            "hain — operational guidance (AI ads ka human review; "
            "watermarks kabhi mat hatao) date se bina jude safe hai."),
    _p("PR10", "Jurisdiction layer — India (Meta policy NAHI)",
       "jurisdiction",
       "Platform approval ≠ local legality. India-targeted ads par: "
       "IT Rules 2021 amendments (notified 10 Feb 2026, in force "
       "20 Feb 2026) — AI generation platforms ko permitted "
       "synthetic content par non-removable provenance labels "
       "chahiye; Ads Manager me India-targeting par AI-disclosure "
       "options ki reporting. ASCI guidelines (29 Sep 2026, "
       "effective ~late Dec 2026) — synthetic content jo purchase "
       "decision influence kare aur bina label ke mislead kare, "
       "wahan label expected ('Audio/Video created using AI' / "
       "'enhanced using AI').",
       "https://www.digimartinfotech.in/ai-ads-labelling-rules-india-meta-google-asci-guide.php",
       status="Secondary reporting (Indian law/industry — not Meta policy)",
       note="Counsel se verify kiye bina rely mat karo."),
]

# Union of the Transparency Center list and the Help Center list (PR4).
# The two official lists do not perfectly match — enforce the union.
PERSONAL_ATTRIBUTES_UNION = [
    "race", "color", "ethnicity", "national origin", "religion",
    "beliefs", "age", "sex", "sexual orientation or practices",
    "gender identity", "disability", "physical health",
    "mental health", "medical conditions", "medical or genetic condition",
    "vulnerable financial status", "voting status",
    "trade union membership", "criminal record", "name",
    "family status",
]


def register_status():
    return {
        "total": len(POLICIES),
        "flagged": sum(1 for p in POLICIES if "flagged" in p["status"]),
        "contested": sum(1 for p in POLICIES if p["status"] == "CONTESTED"),
        "date_checked": DATE_CHECKED,
        "note": "Saari entries %s ko check hui. 'OFFICIAL (via "
                "secondary — flagged)' wali entries Meta ki pages is "
                "environment me 403 deti hain isliye secondary sources "
                "se verify hain — normal browser se re-verify kiye "
                "bina externally quote mat karo. PR9 (2026 Ad Terms) "
                "DISPUTED hai." % DATE_CHECKED,
    }
