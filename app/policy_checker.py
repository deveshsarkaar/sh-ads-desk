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


def check_claims(text):
    """Scan ad text for banned claims. Returns dict(allowed, reasons)."""
    reasons = []
    body = text or ""
    for pat, _cat, reason in _COMPILED:
        if pat.search(body):
            reasons.append(reason)
    return {"allowed": len(reasons) == 0, "reasons": reasons}


def check_product(product, eligibility=None):
    """Eligibility gate. Fails closed. Returns dict(allowed, reasons)."""
    if eligibility is None:
        eligibility = load_eligibility()
    reasons = []
    entry = None
    for item in eligibility:
        if str(item.get("product", "")).strip().lower() == str(product).strip().lower():
            entry = item
            break
    if entry is None:
        reasons.append(
            "Product '%s' is NOT listed in PRODUCT_ELIGIBILITY.yaml — fails closed, no ad allowed." % product
        )
        return {"allowed": False, "reasons": reasons}
    if entry.get("resale_permission_confirmed") is not True:
        reasons.append(
            "resale_permission_confirmed is not true for '%s' — no ad allowed until the owner "
            "verifies resale permission and records proof + terms-checked date." % product
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


def check_creative(product, text, settings=None, eligibility=None):
    """Full gate for one creative: eligibility + banned claims + destination.
    All three must pass. Returns dict(allowed, reasons)."""
    reasons = []
    reasons += check_product(product, eligibility)["reasons"]
    reasons += check_claims(text)["reasons"]
    reasons += check_destination(settings)["reasons"]
    return {"allowed": len(reasons) == 0, "reasons": reasons}
