"""Policy Checker — Role 10 of SH Ads Desk (Step 1, MOCK build).

Two gates, both FAIL CLOSED:
1. Eligibility gate: a product not listed in PRODUCT_ELIGIBILITY.yaml, or
   listed with resale_permission_confirmed != true, can NOT be advertised.
2. Banned-claims gate: ad text is scanned against a checklist built from the
   brief's compliance section (which in turn follows Meta Advertising
   Standards: no misleading claims, no result guarantees, no fake discounts,
   no fake reviews, no unauthorised-subscription promotion).
Plus the destination gate from the brief (rule 6).

No network calls. Returns clear pass/fail reasons.
"""
import re

from .common import load_eligibility, load_settings

# (pattern, category, reason) — built from the brief Part 1 rule 5 list.
BANNED_CLAIMS = [
    (r"\blifetime\b", "misleading_claim",
     "'lifetime' claim is banned (misleading unless proven; brief rule 5)"),
    (r"\bguarantee(d|s)?\b", "result_guarantee",
     "'guarantee/guaranteed' claim is banned — no result guarantees allowed"),
    (r"\bofficial\b", "unverified_official_claim",
     "'official' status claim is banned without proof recorded in PRODUCT_ELIGIBILITY.yaml"),
    (r"\bauthori[sz]ed\s+(reseller|dealer|partner)\b", "unverified_official_claim",
     "'authorised reseller/dealer/partner' claim is banned without recorded proof"),
    (r"\b\d{1,3}\s?%\s?off\b", "unverified_discount",
     "Discount-percentage claim cannot be verified in Step 1 (no verified price source in the repo) — fails closed"),
    (r"\b(was|rs\.?|inr|₹)\s?\d[\d,]*\s?(now|only)\b", "unverified_discount",
     "Was/now price claim cannot be verified in Step 1 — fails closed"),
    (r"\b\d[\d,]*\+?\s?(happy\s)?(customers|users|students)\s?(trust|love|use)\b", "fake_social_proof",
     "Customer-count/trust claim reads as unverified social proof — banned"),
    (r"\b(best|no\.?\s?1|number one|top rated|top-rated)\b", "unverified_superlative",
     "Superlative claim ('best', 'No. 1', 'top rated') is unverified — banned"),
    (r"\b(earn|make)\s?(₹|rs\.?|inr|\$)?\s?\d", "earnings_claim",
     "Earnings claim is banned — no income/result promises"),
    (r"\bdouble your (sales|income|money|profit)\b", "result_guarantee",
     "Result-multiplication claim is banned"),
    (r"\b100\s?%\s?(result|profit|success|working|genuine)\b", "result_guarantee",
     "'100% result/profit/success' claim is banned"),
    (r"\b(shared account|account sharing|cracked|modded|bypass|pirated)\b", "unauthorised_subscription",
     "Promoting shared/cracked/bypassed subscriptions is prohibited (Meta Ad Standards, brief rule 5)"),
    (r"\bonly \d+ (spots|seats|left)\b", "fake_urgency",
     "Scarcity claim ('only N left') is unverified — banned"),
    (r"\bprice will (double|increase|go up)\b", "fake_urgency",
     "Price-rise threat claim is unverified — banned"),
    (r"\b(risk[-\s]?free|no risk)\b", "result_guarantee",
     "'Risk-free / no risk' claim is banned"),
]

_COMPILED = [(re.compile(p, re.IGNORECASE), cat, reason) for p, cat, reason in BANNED_CLAIMS]

# Personal-attributes rule (Policies Register PR4): ads must not assert
# OR imply the viewer has a personal attribute — questions count. The
# checker enforces the UNION of Meta's Transparency Center list and
# Help Center list (the two official lists differ; see
# app/policies_register.py PERSONAL_ATTRIBUTES_UNION). Describe the
# product, never diagnose the viewer. Meta's own pair: "New diabetes
# treatment available" = allowed; "Do you have diabetes?" = NOT allowed.
PERSONAL_ATTRIBUTE_PATTERNS = [
    (r"\bdo you have (diabetes|cancer|depression|anxiety|pcod|pcos|thyroid|a loan|debt|obesity|high bp)\b",
     "personal_attribute", "Copy viewer ki health/financial condition imply karti hai ('Do you have ...?') — personal attributes rule violation (PR4)"),
    (r"\bare you (a |an )?(diabetic|cancer patient|single (mom|mother|dad|father)|bankrupt|pregnant|depressed|overweight)\b",
     "personal_attribute", "Copy viewer ko ek personal attribute se label karti hai — personal attributes rule violation (PR4)"),
    (r"\bare you (still )?(struggling|suffering|worried|tired) (with|about) your (weight|health|debt|finances|hair)\b",
     "personal_attribute", "Copy viewer ki condition par sawal/assertion karti hai — personal attributes rule violation (PR4)"),
    (r"\bjust turned \d{2}\b",
     "personal_attribute", "Exact age imply karna ('just turned 62' — Meta ki apni example) personal attributes violation hai (PR4)"),
    (r"\bfor (diabetics|patients|sufferers) like you\b",
     "personal_attribute", "'... like you' phrasing viewer ki condition imply karti hai — personal attributes rule violation (PR4)"),
    (r"\b(if you are|if you're) (a|an) (diabetic|patient|single|pregnant|bankrupt)\b",
     "personal_attribute", "Conditional attribute callout bhi viewer ki trait imply karta hai — personal attributes rule violation (PR4)"),
    (r"\bcomment (yes|below|your answer)\b.*\b(if|to)\b",
     "engagement_bait", "Engagement bait ('comment YES if...') Meta ke low-quality standards ke against hai"),
    (r"\btag (a|your) friend\b",
     "engagement_bait", "Engagement bait ('tag a friend') banned hai"),
    (r"\b(share|like) (this|it|if) .{0,30}\b(win|free|prize)\b",
     "engagement_bait", "Share/like-to-win mechanics engagement bait hai — banned"),
]

_COMPILED += [(re.compile(p, re.IGNORECASE), cat, reason)
              for p, cat, reason in PERSONAL_ATTRIBUTE_PATTERNS]


def check_claims(text, extra_patterns=None):
    """Scan ad text for banned claims: the universal core list PLUS an
    optional industry add-on pack (dicts with pattern/category/reason,
    from app/industries.py). Returns dict(allowed, reasons)."""
    reasons = []
    body = text or ""
    for pat, _cat, reason in _COMPILED:
        if pat.search(body):
            reasons.append(reason)
    for extra in (extra_patterns or []):
        try:
            if re.search(extra.get("pattern", ""), body, re.IGNORECASE):
                reasons.append(extra.get("reason", "Industry compliance pack hit"))
        except re.error:
            reasons.append("Industry compliance pack pattern is invalid — fails closed")
    return {"allowed": len(reasons) == 0, "reasons": reasons}


def _entry_name(item):
    return str(item.get("product") or item.get("name") or "")


def _entry_confirmed(item):
    """An entry is confirmed only when its permission flag is literally
    true. Generic catalog entries carry permission_confirmed; legacy
    YAML entries carry resale_permission_confirmed."""
    if "resale_permission_confirmed" in item:
        return item.get("resale_permission_confirmed") is True
    return item.get("permission_confirmed") is True


def check_product(product, eligibility=None):
    """Eligibility gate. Fails closed. Returns dict(allowed, reasons).
    Works for the legacy PRODUCT_ELIGIBILITY.yaml list and for any
    business profile's generic offerings catalog (same gate strength)."""
    if eligibility is None:
        eligibility = load_eligibility()
    reasons = []
    entry = None
    for item in eligibility:
        if _entry_name(item).strip().lower() == str(product).strip().lower():
            entry = item
            break
    if entry is None:
        reasons.append(
            "Product '%s' is NOT listed in the eligibility catalog — fails closed, no ad allowed." % product
        )
        return {"allowed": False, "reasons": reasons}
    if not _entry_confirmed(entry):
        if "resale_permission_confirmed" in entry:
            reasons.append(
                "resale_permission_confirmed is not true for '%s' — no ad allowed until the owner "
                "verifies resale permission and records proof + terms-checked date." % product
            )
        else:
            reasons.append(
                "eligibility permission confirmed is not true for '%s' — no ad allowed until the owner "
                "verifies eligibility permission and records proof + terms-checked date." % product
            )
    return {"allowed": len(reasons) == 0, "reasons": reasons}


def check_destination(settings=None):
    """Destination gate (brief rule 6): no ad runs until the owner sets
    DESTINATION_URL and DESTINATION_READY=true."""
    if settings is None:
        settings = load_settings()
    reasons = []
    if not settings.get("DESTINATION_URL"):
        reasons.append("DESTINATION_URL is empty — destination gate is closed.")
    if settings.get("DESTINATION_READY") is not True:
        reasons.append("DESTINATION_READY is not true — destination gate is closed.")
    return {"allowed": len(reasons) == 0, "reasons": reasons}


def check_creative(product, text, settings=None, eligibility=None, extra_patterns=None):
    """Full gate for one creative: eligibility + banned claims (core +
    industry add-on pack) + destination. All must pass. Fails closed.
    Returns dict(allowed, reasons)."""
    reasons = []
    reasons += check_product(product, eligibility)["reasons"]
    reasons += check_claims(text, extra_patterns=extra_patterns)["reasons"]
    reasons += check_destination(settings)["reasons"]
    return {"allowed": len(reasons) == 0, "reasons": reasons}
