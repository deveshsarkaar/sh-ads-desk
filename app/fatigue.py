"""Creative fatigue early-warning — SH Ads Desk V2.

Research basis (25 Nov 2026): creative-analytics tools (Motion,
Segwise) and practitioners watch hook rate, CTR, frequency and CPM
movement to catch fatigue before CPA collapses. This module scores
fatigue from supplied daily rows only and recommends a refresh; it
never pauses or edits an ad.
"""


def _pct_change(first, last):
    if first in (None, 0) or last is None:
        return None
    return (last - first) / abs(first) * 100.0


def fatigue_score(rows):
    """rows: [{ctr, frequency, cpm, hook_rate?}, ...] oldest first.
    Returns {score 0-100, band, signals, recommendation}."""
    rows = [r for r in (rows or []) if r]
    if len(rows) < 3:
        return {"score": 0, "band": "insufficient_data", "signals": [],
                "recommendation": "Kam se kam 3 din ka data chahiye; abhi fatigue judge mat karo."}
    first, last = rows[0], rows[-1]
    score, signals = 0, []

    ctr_ch = _pct_change(first.get("ctr"), last.get("ctr"))
    if ctr_ch is not None and ctr_ch <= -20:
        score += 35
        signals.append(f"CTR {abs(ctr_ch):.0f}% gira hai")
    elif ctr_ch is not None and ctr_ch <= -10:
        score += 15
        signals.append(f"CTR {abs(ctr_ch):.0f}% gira hai")

    freq = last.get("frequency")
    freq_ch = _pct_change(first.get("frequency"), freq)
    if freq is not None and freq >= 3.5:
        score += 25
        signals.append(f"Frequency {freq} tak pahunch gayi hai")
    elif freq_ch is not None and freq_ch >= 20:
        score += 15
        signals.append(f"Frequency {freq_ch:.0f}% badhi hai")

    cpm_ch = _pct_change(first.get("cpm"), last.get("cpm"))
    if cpm_ch is not None and cpm_ch >= 20:
        score += 20
        signals.append(f"CPM {cpm_ch:.0f}% badha hai")

    hook_ch = _pct_change(first.get("hook_rate"), last.get("hook_rate"))
    if hook_ch is not None and hook_ch <= -15:
        score += 20
        signals.append(f"Hook rate {abs(hook_ch):.0f}% gira hai")

    score = min(score, 100)
    if score >= 60:
        band = "fatigued"
        rec = "Creative refresh ka proposal banao — naya angle/hook, purana winner post-ID ke saath graduate karo."
    elif score >= 30:
        band = "watch"
        rec = "Fatigue ke early signals hain — agla creative batch ready rakho, abhi kill mat karo."
    else:
        band = "healthy"
        rec = "Fatigue signals nahi dikh rahe; current read jaari rakho."
    return {"score": score, "band": band, "signals": signals,
            "recommendation": rec,
            "note": "Score sirf supplied rows par hai; koi ad auto-pause nahi hota."}
