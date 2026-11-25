"""Subscription disclosure checker — SH Ads Desk V2.

Policy basis (retrieved 25 Nov 2026 via Meta's policy tool, title
"subscription services"): ads for subscription services must disclose
pricing and recurrent billing. Ads that prompt someone to enter
personally identifiable information are prohibited when any of these
is missing: an unchecked opt-in checkbox, clear language on how to
cancel, or a clear price + billing interval (not buried in fine
print). This checker fails closed on missing pieces. It checks the
owner's own offer copy/landing fields; it never approves an ad.
"""
import re

_INTERVAL = re.compile(r"\b(month|monthly|year|yearly|annual|per\s*month|/mo|mahina|saal)\b", re.I)
_AMOUNT = re.compile(r"(₹|rs\.?|inr|\$|usd)\s?\d|\d+\s?(₹|rs\.?|inr|\$|usd)", re.I)
_CANCEL = re.compile(r"\b(cancel|cancellation|band kar|rok sakte|unsubscribe)\b", re.I)


def check_disclosure(offer):
    """offer keys: price_text, cancellation_text, opt_in_unchecked (bool),
    collects_pii (bool). Returns {ok, issues}."""
    offer = offer or {}
    issues = []
    price_text = offer.get("price_text") or ""
    if not _AMOUNT.search(price_text):
        issues.append("Price amount saaf nahi dikh raha — subscription ad me price disclose karna zaroori hai.")
    if not _INTERVAL.search(price_text):
        issues.append("Billing interval (monthly/yearly) saaf nahi hai — recurrent billing disclose karo.")
    if not _CANCEL.search(offer.get("cancellation_text") or ""):
        issues.append("Cancellation ka clear language missing hai — cancel kaise karein, ye likho.")
    if offer.get("collects_pii") and offer.get("opt_in_unchecked") is not True:
        issues.append("PII manga ja raha hai lekin unchecked opt-in checkbox confirm nahi hai — fail closed.")
    return {"ok": not issues, "issues": issues,
            "policy": "subscription services (Meta policy tool, retrieved 2026-11-25)"}
