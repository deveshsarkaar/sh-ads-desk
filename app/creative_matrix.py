"""Creative diversification planner — SH Ads Desk V2.

Research basis (25 Nov 2026): practitioner consensus across YouTube,
articles and social sources is that creative is now the main targeting
lever under Advantage+/Andromeda-style automation — genuinely distinct
angles, hooks, formats and personas beat near-duplicate variations.
This planner builds an angle x persona x format x hook matrix from the
industry preset's angle templates plus supplied offering facts. It
invents no claims: every brief carries only facts the owner supplied,
and missing facts are flagged, never filled in.
"""
import re

from .industries import get_preset

HOOK_TYPES = ("problem", "outcome", "audience_callout", "myth",
              "process", "proof", "objection", "seasonal")
FORMATS = ("reel_video", "static_image", "carousel", "ugc_style_video")


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def similarity(a, b):
    """Jaccard token overlap between two brief texts (0..1)."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def build_matrix(preset_key, offering_name, facts=None, personas=None,
                 max_briefs=12):
    """Build distinct creative briefs for one offering.

    facts: owner-supplied fact strings (price proof, features) — briefs
    may reference them; nothing else may be claimed.
    Returns {briefs, diversity_score, warnings}. Each brief:
    {angle, persona, format, hook_type, brief_text, facts_used}.
    """
    preset = get_preset(preset_key) or {}
    angles = list(preset.get("angle_templates") or [])
    if not angles:
        angles = [f"{offering_name} — explain its real benefit in plain words"]
    personas = list(personas or preset.get("audience_hints") or ["general buyer"])
    facts = list(facts or [])

    briefs = []
    combos = []
    for angle in angles:
        for persona in personas:
            combos.append((angle, persona))
    for i, (angle, persona) in enumerate(combos[:max_briefs]):
        fmt = FORMATS[i % len(FORMATS)]
        hook = HOOK_TYPES[i % len(HOOK_TYPES)]
        text = (f"{offering_name} — {angle} | Persona: {persona} | "
                f"Format: {fmt} | Hook: {hook}")
        briefs.append({"angle": angle, "persona": persona, "format": fmt,
                       "hook_type": hook, "brief_text": text,
                       "facts_used": facts})

    warnings = []
    if not facts:
        warnings.append("No verified facts supplied — do not add price or proof claims to these briefs.")
    for i in range(len(briefs)):
        for j in range(i + 1, len(briefs)):
            if similarity(briefs[i]["brief_text"], briefs[j]["brief_text"]) >= 0.8:
                warnings.append(
                    f"Brief {i + 1} aur {j + 1} look near-duplicate — change the angle or hook.")

    distinct_angles = len({b["angle"] for b in briefs})
    distinct_personas = len({b["persona"] for b in briefs})
    distinct_formats = len({b["format"] for b in briefs})
    distinct_hooks = len({b["hook_type"] for b in briefs})
    diversity = round(100 * (distinct_angles + distinct_personas +
                             distinct_formats + distinct_hooks) /
                      max(1, 4 * max(1, len(briefs))), 1) if briefs else 0.0
    return {"briefs": briefs, "diversity_score": diversity,
            "warnings": warnings,
            "note": "Briefs use owner-supplied facts only; no claim is invented."}
