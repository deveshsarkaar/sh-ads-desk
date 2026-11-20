"""Seeded competitor / inspiration entries — per business profile.

These are EXAMPLE SEED DATA: people/brands the owner personally pointed at
and asked to track (tagged "owner-added"), plus advertisers/sellers found
by the 2026-11-20 subscription-vertical research (tagged
"research-added" — see the honesty note inside that block: no Ad Library
record or ad start date was recoverable for any of them). They are research inputs for
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
        # --- Subscription vertical, seeded 2026-11-20 from
        # ~/workspace/research_notes/subscription-meta-ads/report.md
        # HONESTY: the Ad Library returned HTTP 403 to that
        # research and the search index held NO Library record for
        # any seller below — "longevity" is UNMEASURED for every
        # entry (no verified ad start date exists). The ad_library
        # URLs are the standard Library keyword-search pattern so
        # the owner can run the live check himself; country is IN
        # (switch it in the Library per market). Activity notes
        # are OBSERVED seller activity, not ad results.
        {
            "name": "Tradeello",
            "instagram_handle": "@tradeellodigital",
            "instagram_url": "https://www.instagram.com/tradeellodigital",
            "website": "tradeello.com",
            "niche": "subscription reseller (ChatGPT Plus, global)",
            "kind": "tracked competitor — subscription vertical "
                    "research 2026-11-20",
            "followers_note": "No Library record found via search "
                              "index (2026-11-20); longevity "
                              "UNMEASURED. OBSERVED organic "
                              "promotion only: identical 'ChatGPT "
                              "Plus $10.50, your own account' "
                              "creative posted 12-16 Nov 2026 "
                              "across 2 Facebook identities "
                              "('Trade Ello Digital', 'Tradeello "
                              "Store') and 4 Instagram handles — "
                              "not verified paid ads",
            "ad_library_url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&q=Tradeello&search_type=keyword_unordered",
            "source": "subscription vertical research 2026-11-20",
            "tags": ["research-added", "subscription-vertical"],
        },
        {
            "name": "OTT Services BD",
            "instagram_handle": "",
            "instagram_url": "",
            "website": "ottservicesbd (storefront, Bangladesh)",
            "niche": "OTT reseller (Netflix, Bangladesh)",
            "kind": "tracked competitor — subscription vertical "
                    "research 2026-11-20",
            "followers_note": "No Library record found via search "
                              "index (2026-11-20); longevity "
                              "UNMEASURED. OBSERVED paid trace: its "
                              "product-page URL carries "
                              "utm_source=fb&utm_medium=paid with "
                              "a Facebook campaign id — a real "
                              "paid campaign, but no Page name or "
                              "ad start date was recoverable",
            "ad_library_url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=BD&q=Netflix&search_type=keyword_unordered",
            "source": "subscription vertical research 2026-11-20",
            "tags": ["research-added", "subscription-vertical"],
        },
        {
            "name": "SubsHub",
            "instagram_handle": "",
            "instagram_url": "",
            "website": "subshub.in",
            "niche": "subscription storefront (Canva/ChatGPT/Gemini/OTT, India)",
            "kind": "tracked competitor — subscription vertical "
                    "research 2026-11-20",
            "followers_note": "No Library record found via search "
                              "index (2026-11-20); longevity "
                              "UNMEASURED. OBSERVED storefront: "
                              "display prices from Rs 45/mo, 'Pay "
                              "by UPI, delivered on WhatsApp', "
                              "replacement warranty — display "
                              "prices are the seller's own copy, "
                              "not benchmarks",
            "ad_library_url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&q=SubsHub&search_type=keyword_unordered",
            "source": "subscription vertical research 2026-11-20",
            "tags": ["research-added", "subscription-vertical"],
        },
        {
            "name": "AcademicTools",
            "instagram_handle": "",
            "instagram_url": "",
            "website": "academictools (storefront, India)",
            "niche": "subscription reseller (Canva/ChatGPT/Gemini, India, students)",
            "kind": "tracked competitor — subscription vertical "
                    "research 2026-11-20",
            "followers_note": "No Library record found via search "
                              "index (2026-11-20); longevity "
                              "UNMEASURED. OBSERVED storefront: "
                              "self-declared independent reseller, "
                              "UPI/card, WhatsApp support, "
                              "delivery-time claims are the "
                              "seller's own copy",
            "ad_library_url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&q=Canva%20Pro&search_type=keyword_unordered",
            "source": "subscription vertical research 2026-11-20",
            "tags": ["research-added", "subscription-vertical"],
        },
        {
            "name": "GroupAITools",
            "instagram_handle": "",
            "instagram_url": "",
            "website": "groupaitools.com",
            "niche": "group-buy tools storefront (170+ tools, India)",
            "kind": "tracked competitor — subscription vertical "
                    "research 2026-11-20",
            "followers_note": "No Library record found via search "
                              "index (2026-11-20); longevity "
                              "UNMEASURED. OBSERVED on its own "
                              "site (checked 2026-11-20): 'Save "
                              "over 90%' headline and customer "
                              "counts are the seller's own "
                              "UNVERIFIED marketing claims; CTA "
                              "is 'Request on WhatsApp'",
            "ad_library_url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&q=GroupAITools&search_type=keyword_unordered",
            "source": "subscription vertical research 2026-11-20",
            "tags": ["research-added", "subscription-vertical"],
        },
        {
            "name": "OTTSeller",
            "instagram_handle": "",
            "instagram_url": "",
            "website": "ottseller.com",
            "niche": "subscription storefront (OTT/AI/VPN, India origin, global)",
            "kind": "tracked competitor — subscription vertical "
                    "research 2026-11-20",
            "followers_note": "No Library record found via search "
                              "index (2026-11-20); longevity "
                              "UNMEASURED. OBSERVED on its own "
                              "site (checked 2026-11-20): origin "
                              "story is a WhatsApp group; checkout "
                              "on site + WhatsApp support; "
                              "activation/customer counters are "
                              "the seller's own UNVERIFIED claims",
            "ad_library_url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&q=OTTSeller&search_type=keyword_unordered",
            "source": "subscription vertical research 2026-11-20",
            "tags": ["research-added", "subscription-vertical"],
        },
    ],
}


def seeded_for(profile_slug="software-hub"):
    """Seed entries for one profile (list of dicts; [] if none)."""
    return [dict(e) for e in SEEDED_COMPETITORS.get(profile_slug, [])]
