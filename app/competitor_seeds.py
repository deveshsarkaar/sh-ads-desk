"""Seeded competitor / inspiration entries — per business profile.

These are EXAMPLE SEED DATA: people/brands the owner personally pointed at
and asked to track (tagged "owner-added"). They are research inputs for
Role 2 (Competitor Watch) and the Growth Loop's competitor-discovery stage —
public sources only (public profiles / public Meta Ad Library). Nothing
here was scraped or verified by the system: follower counts and other
figures are exactly as the owner shared them and are labelled as such.

When the profile-based competitor list (DB-backed, owner-editable) is in
use, these seeds are the starting rows for the named profile; the owner can
edit or remove them there like any other entry.
"""

# Keyed by profile slug. "software-hub" is the seeded default profile.
SEEDED_COMPETITORS = {
    "software-hub": [
        {
            "name": "Damini Tripathi",
            "instagram_handle": "@damini.creator",
            "instagram_url": "https://www.instagram.com/damini.creator",
            "website": "marketian.io",
            "niche": "marketing creator",
            "kind": "inspiration / tracked creator (marketing niche — "
                    "not a direct Software Hub competitor)",
            "followers_note": "~824,895 followers, verified account — "
                              "figure as shared by the owner, NOT "
                              "independently verified by this system",
            "source": "owner shared 2026-11-16",
            "tags": ["owner-added", "inspiration"],
        },
    ],
}


def seeded_for(profile_slug="software-hub"):
    """Seed entries for one profile (list of dicts; [] if none)."""
    return [dict(e) for e in SEEDED_COMPETITORS.get(profile_slug, [])]
