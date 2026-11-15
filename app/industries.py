"""Industry presets library — SH Ads Desk (industry-agnostic build).

A preset is an EDITABLE STARTING POINT for one industry: research
checklist, audience hints, starter angle templates, funnel/KPI defaults
and lead-quality stages (copied into the profile's settings overrides at
creation time — never hardcoded into logic), plus a compliance ADD-ON
pack of extra banned-claim patterns that sit ON TOP of the core checker
in policy_checker.py (Meta's universal banned claims stay in the core).

Presets are NOT legal advice and do not replace reading Meta's current
Advertising Standards or the laws of the owner's market. The owner can
edit everything a preset seeds.
"""

# Each compliance pack entry: (regex, category, reason). Patterns are
# deliberately narrow so ordinary copy is not blocked by accident.
def _pack(*entries):
    return [{"pattern": p, "category": c, "reason": r} for p, c, r in entries]


PRESETS = {
    "software_digital": {
        "label": "Software & Digital Products",
        "permission_label": "resale permission confirmed",
        "permission_note": "Software keeps the STRICT wording: an offering "
                           "may be advertised only when its resale "
                           "permission is confirmed with proof + terms date.",
        "sales_model": "checkout",
        "research_checklist": [
            "Supplier ke official terms me resale/share permission padho aur date ke saath record karo",
            "Competitor kaun se tools/bundles push kar rahe hain — public Ad Library me dekho",
            "Customer segment (students/freelancers/creators/agencies) ke hisaab se catalog group karo",
            "Har tool ki official price vs apni price ka proof rakho — bina proof discount claim nahi",
        ],
        "audience_hints": ["students", "freelancers", "creators", "bot owners", "agencies"],
        "angle_templates": [
            "Ek jagah saare kaam ke tools, taaki har tool ke liye alag jagah na bhatakna pade",
            "Apne workflow ke hisaab se AI toolkit ready rakho",
            "Apne catalog/bot ke liye software supply ki jaankari ek jagah",
        ],
        "funnel_defaults": {
            "FUNNEL_STAGES": "ad > enquiry > product page / order > paid order",
            "PRIMARY_KPI": "cost per qualified lead",
            "LEAD_STAGES": ["enquiry", "real_conversation", "reseller_application", "order", "junk"],
        },
        "compliance_pack": _pack(
            (r"\b(crack|keygen|nulled|mod apk)\b", "unauthorised_subscription",
             "Cracked/keygen/nulled software promotion is prohibited"),
            (r"\bshared\s+(login|credentials|password)\b", "unauthorised_subscription",
             "Promoting shared logins/credentials is prohibited"),
            (r"\ball\s+tools?\s+free\b", "misleading_claim",
             "'All tools free' is a misleading claim unless literally true and proven"),
        ),
    },
    "grocery_food": {
        "label": "Grocery & Food",
        "permission_label": "eligibility permission confirmed",
        "permission_note": "Confirm sourcing/FSSAI-type eligibility per local law before advertising.",
        "sales_model": "checkout",
        "research_checklist": [
            "Local competitors (kirana, quick-commerce, D2C brands) ki Ad Library presence dekho",
            "Delivery area, minimum order aur delivery time pehle fix karo — ad me wahi likho jo sach hai",
            "Seasonal/festival demand calendar banao",
            "Health/organic claims ke liye certificate/proof file rakho — bina proof claim nahi",
        ],
        "audience_hints": ["families", "working professionals", "hostel students", "bulk buyers (offices)"],
        "angle_templates": [
            "Roz ki grocery ek hi order me — bina market ghoome",
            "Fresh sabzi aur daily needs, time par delivery ke saath",
            "Mahine ka rashan ek baar me, list banao aur bhool jao",
        ],
        "funnel_defaults": {
            "FUNNEL_STAGES": "ad > store/menu view > order > repeat order",
            "PRIMARY_KPI": "cost per order",
            "LEAD_STAGES": ["enquiry", "first_order", "repeat_order", "junk"],
        },
        "compliance_pack": _pack(
            (r"\b100\s?%\s?organic\b", "unverified_health_claim",
             "'100% organic' claim needs certification proof — fails closed without it"),
            (r"\bno\s+chemicals?\b", "unverified_health_claim",
             "'No chemicals' is an unverifiable absolute claim — banned"),
            (r"\b(cures?|treats?|prevents?)\s+(diabetes|cancer|bp|blood pressure|disease)\b",
             "disease_claim", "Food products may not claim to cure/treat/prevent disease"),
            (r"\bdiabetes[-\s]?friendly\b", "unverified_health_claim",
             "Disease-linked food claims need proof — fails closed without it"),
        ),
    },
    "ecommerce": {
        "label": "E-commerce",
        "permission_label": "eligibility permission confirmed",
        "permission_note": "Confirm you may sell each listed product (brand/IP rights) before advertising.",
        "sales_model": "checkout",
        "research_checklist": [
            "Marketplace (Amazon/Flipkart/Meesho) par same category ke top sellers aur unke creatives dekho",
            "Apni price vs marketplace price ka sachha comparison rakho — shipping ke saath",
            "Return/replacement policy ad se pehle page par saaf likho",
            "Festival sale calendar aur category demand peaks note karo",
        ],
        "audience_hints": ["online shoppers", "deal seekers", "gift buyers", "repeat buyers"],
        "angle_templates": [
            "Jo chahiye wo ek hi store me — bina 10 jagah compare kiye",
            "Daily-use products par saaf pricing, koi hidden charge nahi",
            "Gift ho ya ghar ka saaman — curated collection dekho",
        ],
        "funnel_defaults": {
            "FUNNEL_STAGES": "ad > product view > add to cart > paid order",
            "PRIMARY_KPI": "cost per order",
            "LEAD_STAGES": ["view", "cart", "order", "junk"],
        },
        "compliance_pack": _pack(
            (r"\b100\s?%\s?(original|genuine|authentic)\b", "unverified_authenticity",
             "'100% original/genuine' authenticity claim needs proof — fails closed without it"),
            (r"\blowest\s+price\b", "unverified_superlative",
             "'Lowest price' is an unverifiable superlative — banned"),
            (r"\bbranded\s+at\s+local\s+price\b", "misleading_claim",
             "Brand-vs-local price framing is misleading without proof"),
        ),
    },
    "manufacturing_b2b": {
        "label": "Manufacturing & B2B",
        "permission_label": "eligibility permission confirmed",
        "permission_note": "Confirm product specs, certifications and export eligibility before advertising.",
        "sales_model": "lead_gen",
        "research_checklist": [
            "IndiaMART/TradeIndia aur Ad Library par direct competitors ki positioning dekho",
            "Buyer personas fix karo: purchase manager, dealer/distributor, exporter",
            "MOQ, lead time aur dispatch capacity pehle confirm karo — ad me wahi promise karo jo plant de sakta hai",
            "Certification (ISO/CE wagairah) ke asal documents file me rakho",
        ],
        "audience_hints": ["purchase managers", "dealers & distributors", "exporters", "OEM buyers"],
        "angle_templates": [
            "Factory se seedha supply — beech ke margin ke bina rate ki baat karo",
            "Bulk orders ke liye apni requirement bhejo, quotation pao",
            "Dealers ke liye regular supply aur saaf payment terms",
        ],
        "funnel_defaults": {
            "FUNNEL_STAGES": "ad > enquiry > quotation > sample/order > repeat order",
            "PRIMARY_KPI": "cost per qualified enquiry",
            "LEAD_STAGES": ["enquiry", "quotation_sent", "negotiation", "order", "junk"],
        },
        "compliance_pack": _pack(
            (r"\b(iso|ce|isi)\s?certified\b", "unverified_certification",
             "Certification claim (ISO/CE/ISI certified) needs the actual certificate on record — fails closed"),
            (r"\bzero\s?defect\b", "misleading_claim",
             "'Zero defect' is an absolute quality guarantee — banned"),
            (r"\bexport\s?quality\b", "misleading_claim",
             "'Export quality' is an unverifiable quality claim — banned without a defined standard"),
        ),
    },
    "social_media_marketing": {
        "label": "Social Media & Marketing Services",
        "permission_label": "eligibility permission confirmed",
        "permission_note": "Confirm each service can actually be delivered as described before advertising.",
        "sales_model": "lead_gen",
        "research_checklist": [
            "Competitor panels/agencies ke packages aur Ad Library creatives dekho",
            "Har platform (Instagram/YouTube/Telegram/X) ke liye alag service page aur saaf delivery time rakho",
            "Refill/replacement terms pehle likho — ad me wahi bolo jo policy me hai",
            "Fake-engagement wale shabdon se bacho — Meta inhe restrict karta hai",
        ],
        "audience_hints": ["creators", "small businesses", "agencies", "resellers"],
        "angle_templates": [
            "Apne page ki growth services ek hi panel me — platform ke hisaab se chuno",
            "Creators ke liye content reach badhane ki services, saaf rates ke saath",
            "Agencies ke liye wholesale rates par social services",
        ],
        "funnel_defaults": {
            "FUNNEL_STAGES": "ad > enquiry > panel signup > wallet top-up > order",
            "PRIMARY_KPI": "cost per qualified lead",
            "LEAD_STAGES": ["enquiry", "signup", "first_order", "repeat_order", "junk"],
        },
        "compliance_pack": _pack(
            (r"\b(real|genuine|organic)\s+(followers|likes|views|subscribers)\b",
             "unverified_engagement_claim",
             "'Real/genuine/organic followers' claims are unverifiable and restricted — banned"),
            (r"\bban[-\s]?proof\b", "misleading_claim",
             "'Ban-proof' is an unverifiable safety guarantee — banned"),
            (r"\bpermanent\s+(followers|growth|likes)\b", "result_guarantee",
             "'Permanent followers/growth' is a permanence guarantee — banned"),
        ),
    },
    "education_courses": {
        "label": "Education & Courses",
        "permission_label": "eligibility permission confirmed",
        "permission_note": "Confirm course content, faculty and any affiliation claims before advertising.",
        "sales_model": "lead_gen",
        "research_checklist": [
            "Competitor courses ke curriculum, fees aur Ad Library creatives compare karo",
            "Free demo/webinar funnel pehle decide karo — ad usi par bhejegaa",
            "Student results ke liye sirf asal, consent-wale testimonials use karo",
            "Course completion/certificate ki shartein page par saaf likho",
        ],
        "audience_hints": ["students", "working professionals", "parents", "career switchers"],
        "angle_templates": [
            "Roz thoda-thoda seekho — apne pace par, apni bhasha me",
            "Pehle free demo class dekho, phir decide karo",
            "Skill seekhne ka plan banao — syllabus aur roadmap pehle dekho",
        ],
        "funnel_defaults": {
            "FUNNEL_STAGES": "ad > demo/webinar signup > counselling call > enrolment",
            "PRIMARY_KPI": "cost per qualified lead",
            "LEAD_STAGES": ["enquiry", "demo_attended", "counselling", "enrolled", "junk"],
        },
        "compliance_pack": _pack(
            (r"\b100\s?%\s?placement\b", "placement_claim",
             "'100% placement' claim is banned — placement outcomes can never be promised in full"),
            (r"\bplacement\s+(assured|confirmed|pakka)\b", "placement_claim",
             "Assured/confirmed placement claims are banned"),
            (r"\bjob\s?pakka\b", "placement_claim",
             "'Job pakka' is a guaranteed-employment claim — banned"),
            (r"\b\d+\s?lpa\s+(package\s+)?(confirm|pakka|guaranteed)\b", "earnings_claim",
             "Confirmed salary-package claims are banned"),
        ),
    },
    "real_estate": {
        "label": "Real Estate",
        "permission_label": "eligibility permission confirmed",
        "permission_note": "Confirm project/property details and RERA status (where applicable) before advertising.",
        "sales_model": "lead_gen",
        "research_checklist": [
            "Same micro-market ke developers/brokers ke Ad Library creatives dekho",
            "Har project ki asal details verify karo: price, possession, approvals",
            "Site-visit funnel fix karo — ad, enquiry, visit, booking alag-alag track ho",
            "RERA registration number (agar applicable) creative/page par rakho",
        ],
        "audience_hints": ["home buyers", "investors", "renters", "channel partners / brokers"],
        "angle_templates": [
            "Apne budget aur area ke hisaab se options dekho — pehle jaankari, phir visit",
            "Site visit book karo aur khud dekh kar decide karo",
            "Brokers ke liye verified inventory ki jaankari ek jagah",
        ],
        "funnel_defaults": {
            "FUNNEL_STAGES": "ad > enquiry > site visit > booking",
            "PRIMARY_KPI": "cost per qualified lead",
            "LEAD_STAGES": ["enquiry", "visit_scheduled", "visit_done", "booking", "junk"],
        },
        "compliance_pack": _pack(
            (r"\bappreciation\s+(assured|confirmed|pakka)\b", "investment_claim",
             "Assured/confirmed appreciation claims are banned — property values cannot be promised"),
            (r"\b\d+\s?%\s?(annual\s+)?returns?\b", "investment_claim",
             "Percentage-return claims on property are banned without regulated proof — fails closed"),
            (r"\brera\s?approved\b", "unverified_certification",
             "'RERA approved' claim needs the actual registration on record — fails closed"),
        ),
    },
    "local_services": {
        "label": "Local Services",
        "permission_label": "eligibility permission confirmed",
        "permission_note": "Confirm service area, pricing basis and technician capacity before advertising.",
        "sales_model": "calls",
        "research_checklist": [
            "Same sheher ke competitor services ke rates aur Ad Library creatives dekho",
            "Service area (radius/areas) pehle fix karo — bahar ke leads waste hote hain",
            "Call/WhatsApp response time ka system banao — local leads turant jawab maangte hain",
            "Rate card page par saaf rakho — visit charge aur kaam ka charge alag-alag",
        ],
        "audience_hints": ["homeowners", "tenants", "shops & offices", "societies / RWAs"],
        "angle_templates": [
            "Ghar ka kaam, apne area ke verified service ke saath",
            "Pehle rate jaano, phir booking karo — koi surprise charge nahi",
            "Ek call par service book — apne sheher, apne time par",
        ],
        "funnel_defaults": {
            "FUNNEL_STAGES": "ad > call/WhatsApp > booking > job done > review/repeat",
            "PRIMARY_KPI": "cost per booking",
            "LEAD_STAGES": ["enquiry", "booking", "job_done", "junk"],
        },
        "compliance_pack": _pack(
            (r"\bcertified\s+(technicians?|experts?|mechanics?)\b", "unverified_certification",
             "'Certified technicians/experts' claim needs proof on record — fails closed"),
            (r"\bcheapest\s+in\s+(the\s+)?(city|town|area)\b", "unverified_superlative",
             "'Cheapest in the city' is an unverifiable superlative — banned"),
            (r"\bsame\s?day\s+(guarantee|guaranteed|fix\s+guaranteed)\b", "result_guarantee",
             "Same-day completion guarantees are banned unless operationally proven and recorded"),
        ),
    },
    "health_wellness": {
        "label": "Health & Wellness",
        "permission_label": "eligibility permission confirmed",
        "permission_note": "Confirm licences/qualifications and what may legally be claimed before advertising.",
        "sales_model": "lead_gen",
        "research_checklist": [
            "Competitor clinics/brands ke creatives dekho — unke claims apne liye copy mat karo",
            "Meta ki health rules padho: personal-attribute aur before/after restrictions khaas taur par",
            "Doctor/practitioner ki asal qualification page par rakho",
            "Testimonials ke liye consent aur asal results hi use karo",
        ],
        "audience_hints": ["patients (general)", "fitness seekers", "parents", "senior citizens"],
        "angle_templates": [
            "Apni health ke sawalon ke liye pehle sahi jaankari lo",
            "Consultation book karo — pehle samjho, phir decide karo",
            "Roz ki chhoti habits se wellness ka plan banao",
        ],
        "funnel_defaults": {
            "FUNNEL_STAGES": "ad > enquiry > consultation > treatment/plan start",
            "PRIMARY_KPI": "cost per qualified lead",
            "LEAD_STAGES": ["enquiry", "consultation_booked", "consultation_done", "started", "junk"],
        },
        "compliance_pack": _pack(
            (r"\bcures?\s+(diabetes|cancer|thyroid|pcod|pcos|hair\s?fall|obesity)\b",
             "cure_claim", "Cure claims for named conditions are banned"),
            (r"\bbefore\s?(and|&)\s?after\b", "before_after",
             "Before/after imagery and claims are restricted in health ads — banned in this system"),
            (r"\blose\s+\d+\s?(kg|kgs|pounds|lbs)\b", "weight_claim",
             "Specific weight-loss amount claims are banned"),
            (r"\bno\s+side\s?effects\b", "misleading_claim",
             "'No side effects' is an absolute safety claim — banned"),
            (r"\bpainless\s+(treatment|procedure|surgery)\b", "misleading_claim",
             "'Painless treatment' is an unverifiable outcome claim — banned"),
        ),
    },
    "finance_insurance": {
        "label": "Finance & Insurance",
        "permission_label": "eligibility permission confirmed",
        "permission_note": "Confirm licences (IRDAI/SEBI-type, as applicable) and regulated wording before advertising.",
        "sales_model": "lead_gen",
        "research_checklist": [
            "Competitor fintech/insurer creatives dekho — unke return wale shabdon se khaas bacho",
            "Apni licence/registration details page par rakho",
            "Har product ke risk disclosures pehle likho — ad me chhoti si jagah par bhi",
            "Lead quality yahan sabse important hai — junk leads par kharch rokne ka plan rakho",
        ],
        "audience_hints": ["salaried professionals", "business owners", "first-time investors", "families"],
        "angle_templates": [
            "Apne paiso ke liye pehle sahi jaankari — bina jaldbaazi ke plan banao",
            "Insurance ho ya investment, pehle terms samjho phir decide karo",
            "Ek call par apne sawalon ke jawab lo",
        ],
        "funnel_defaults": {
            "FUNNEL_STAGES": "ad > enquiry > advisor call > KYC/application > policy/investment",
            "PRIMARY_KPI": "cost per qualified lead",
            "LEAD_STAGES": ["enquiry", "call_done", "application", "converted", "junk"],
        },
        "compliance_pack": _pack(
            (r"\bassured\s+returns?\b", "return_claim",
             "'Assured returns' claims are banned for market-linked products"),
            (r"\bfixed\s+returns?\b", "return_claim",
             "'Fixed returns' claims are banned unless the product is genuinely fixed and licensed — fails closed"),
            (r"\b\d+\s?%\s?returns?\b", "return_claim",
             "Percentage-return claims are banned without regulated proof — fails closed"),
            (r"\bcrorepati\b", "earnings_claim",
             "'Crorepati' outcome claims are banned"),
            (r"\btax[-\s]?free\s+returns?\b", "return_claim",
             "'Tax-free returns' claims need regulated proof — fails closed"),
        ),
    },
    "generic": {
        "label": "Generic / Other",
        "permission_label": "eligibility permission confirmed",
        "permission_note": "Confirm you may legally sell/offer each item before advertising.",
        "sales_model": "lead_gen",
        "research_checklist": [
            "Apni category ke 3–5 direct competitors ki Ad Library presence dekho",
            "Apna offer ek line me saaf likho — kya, kiske liye, kitne me",
            "Destination page pehle ready karo — ad se pehle page",
            "Har claim ke liye proof file rakho — bina proof claim nahi",
        ],
        "audience_hints": ["general customers"],
        "angle_templates": [
            "Apne kaam ki cheez ek hi jagah — pehle dekho, phir decide karo",
            "Saaf jaankari, saaf rates — pehle samjho, phir aage badho",
            "Roz ki ek chhoti dikkat, ek seedha hal — bina jargon ke samjhaya",
            "Purana tareeka vs naya tareeka — farak khud dekho",
        ],
        "funnel_defaults": {
            "FUNNEL_STAGES": "ad > enquiry > conversation > order",
            "PRIMARY_KPI": "cost per qualified lead",
            "LEAD_STAGES": ["enquiry", "conversation", "order", "junk"],
        },
        "compliance_pack": _pack(),
    },
}

PRESET_ORDER = ["software_digital", "grocery_food", "ecommerce",
                "manufacturing_b2b", "social_media_marketing",
                "education_courses", "real_estate", "local_services",
                "health_wellness", "finance_insurance", "generic"]

SALES_MODELS = ("checkout", "lead_gen", "whatsapp", "calls", "footfall")
TARGET_TYPES = ("B2C", "B2B", "both")


def get_preset(key):
    """Preset dict or the generic preset. Never raises."""
    return PRESETS.get(key or "generic", PRESETS["generic"])


def preset_key_for_label(label):
    for key, preset in PRESETS.items():
        if preset["label"].lower() == str(label or "").strip().lower():
            return key
    return None


def compliance_patterns(preset_key):
    """Extra banned-claim patterns for one industry preset (list of dicts)."""
    return [dict(p) for p in get_preset(preset_key).get("compliance_pack", [])]
