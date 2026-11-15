"""Business Profiles — SH Ads Desk (industry-agnostic build).

The desk serves ANY business, not just Software Hub. A profile holds one
business: name, industry (preset key or free text), description, website,
target customers, geography, languages, currency, sales model, its own
offerings catalog, its own competitors, and per-profile settings
overrides (merged over the global settings file — overrides win).

Profile #1 is seeded as "Software Hub" by migrating
PRODUCT_ELIGIBILITY.yaml LOSSLESSLY: every product becomes an offering
with the same supplier / permission flag / proof note / terms date.
The YAML file itself is never modified by the migration and stays as the
legacy source; the DB catalog is the live one afterwards.

Gate strength is unchanged: an offering whose permission flag is not
confirmed can NOT be advertised (policy_checker, fails closed).
"""
import json
import re

from . import competitor_seeds, industries
from .common import _now, audit, get_db, load_eligibility

SOFTWARE_HUB_SLUG = "software-hub"


def slugify(name):
    slug = re.sub(r"[^a-z0-9]+", "-", str(name or "").strip().lower()).strip("-")
    return slug or "business"


def _row_to_profile(row):
    if row is None:
        return None
    p = dict(row)
    try:
        p["settings_overrides"] = json.loads(p.get("settings_overrides") or "{}")
    except ValueError:
        p["settings_overrides"] = {}
    if not isinstance(p["settings_overrides"], dict):
        p["settings_overrides"] = {}
    return p


def list_profiles(conn=None):
    conn = conn or get_db()
    rows = conn.execute("SELECT * FROM profiles ORDER BY id").fetchall()
    return [_row_to_profile(r) for r in rows]


def get_profile(profile_id, conn=None):
    conn = conn or get_db()
    row = conn.execute("SELECT * FROM profiles WHERE id = ?",
                       (profile_id,)).fetchone()
    return _row_to_profile(row)


def get_profile_by_slug(slug, conn=None):
    conn = conn or get_db()
    row = conn.execute("SELECT * FROM profiles WHERE slug = ?",
                       (slug,)).fetchone()
    return _row_to_profile(row)


def active_profile_id(conn=None):
    conn = conn or get_db()
    row = conn.execute("SELECT value FROM kv WHERE key = 'active_profile_id'").fetchone()
    if row:
        try:
            pid = int(row["value"])
            if get_profile(pid, conn):
                return pid
        except (TypeError, ValueError):
            pass
    profiles = list_profiles(conn)
    return profiles[0]["id"] if profiles else None


def get_active_profile(conn=None):
    conn = conn or get_db()
    ensure_seeded(conn)
    pid = active_profile_id(conn)
    return get_profile(pid, conn) if pid else None


def set_active_profile(profile_id, conn=None):
    conn = conn or get_db()
    profile = get_profile(profile_id, conn)
    if profile is None:
        raise KeyError("profile %s not found" % profile_id)
    conn.execute("INSERT OR REPLACE INTO kv (key, value) VALUES ('active_profile_id', ?)",
                 (str(profile_id),))
    conn.commit()
    audit(conn, "profile_activated", "profile=%s (%s)" % (profile["slug"], profile["name"]))
    return profile


# ---------------------------------------------------------------- seeding
def ensure_seeded(conn=None):
    """Create the Software Hub profile (with the lossless YAML migration
    and the competitor seeds) when no profile exists yet. Idempotent."""
    conn = conn or get_db()
    existing = conn.execute("SELECT COUNT(*) AS n FROM profiles").fetchone()["n"]
    if existing:
        pid = active_profile_id(conn)
        return get_profile(pid, conn) if pid else None
    preset = industries.get_preset("software_digital")
    overrides = dict(preset["funnel_defaults"])
    overrides["LEAD_STAGES"] = list(preset["funnel_defaults"].get("LEAD_STAGES", []))
    cur = conn.execute(
        "INSERT INTO profiles (slug, name, industry, industry_preset, description, "
        "website, target_type, target_text, geography, languages, currency, "
        "sales_model, permission_label, settings_overrides, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (SOFTWARE_HUB_SLUG, "Software Hub", preset["label"], "software_digital",
         "Premium AI/software tools and annual collections, sold globally "
         "via softwarehub.tech (official coupon codes, manual fulfilment).",
         "https://softwarehub.tech", "both",
         "Customers: students, freelancers, creators, IT professionals and "
         "companies. Resellers: bot owners and agencies (separate campaigns).",
         "Global", "Hinglish, English", "INR",
         preset["sales_model"], preset["permission_label"],
         json.dumps(overrides), _now()))
    conn.commit()
    profile_id = cur.lastrowid
    migrate_software_hub_catalog(conn, profile_id)
    for entry in competitor_seeds.seeded_for(SOFTWARE_HUB_SLUG):
        add_competitor(profile_id, {
            "name": entry.get("name", ""), "handle": entry.get("instagram_handle", ""),
            "url": entry.get("instagram_url", ""), "website": entry.get("website", ""),
            "niche": entry.get("niche", ""), "kind": entry.get("kind", ""),
            "source": entry.get("source", ""),
            "notes": entry.get("followers_note", ""),
        }, conn)
    conn.execute("INSERT OR REPLACE INTO kv (key, value) VALUES ('active_profile_id', ?)",
                 (str(profile_id),))
    conn.commit()
    audit(conn, "profile_seeded",
          "Software Hub profile created from PRODUCT_ELIGIBILITY.yaml migration")
    return get_profile(profile_id, conn)


def migrate_software_hub_catalog(conn, profile_id):
    """Import PRODUCT_ELIGIBILITY.yaml rows as offerings for a profile.
    Lossless: name, supplier, permission flag, proof note and terms date
    are copied exactly. Returns a proof dict comparing source vs stored."""
    source = load_eligibility()
    existing = conn.execute("SELECT COUNT(*) AS n FROM offerings WHERE profile_id = ?",
                            (profile_id,)).fetchone()["n"]
    if not existing:
        for item in source:
            conn.execute(
                "INSERT INTO offerings (profile_id, name, type, category, price, "
                "supplier, permission_confirmed, proof_note, terms_checked_date, "
                "destination_override, created_at) VALUES (?, ?, 'product', '', '', "
                "?, ?, ?, ?, '', ?)",
                (profile_id, item.get("product", ""), item.get("supplier", "") or "",
                 1 if item.get("resale_permission_confirmed") is True else 0,
                 item.get("proof_note", "") or "",
                 item.get("terms_checked_date", "") or "", _now()))
        conn.commit()
    return migration_proof(conn, profile_id, source)


def migration_proof(conn=None, profile_id=None, source=None):
    """Prove the Software Hub migration is lossless: same count, same name
    set, same supplier/proof/date per name, every flag false (as in YAML)."""
    conn = conn or get_db()
    if profile_id is None:
        profile = get_profile_by_slug(SOFTWARE_HUB_SLUG, conn)
        profile_id = profile["id"] if profile else None
    source = source if source is not None else load_eligibility()
    rows = list_offerings(profile_id, conn) if profile_id else []
    src = {str(i.get("product", "")): i for i in source}
    stored = {r["name"]: r for r in rows}
    mismatches = []
    for name, item in src.items():
        row = stored.get(name)
        if row is None:
            mismatches.append("missing: %s" % name)
            continue
        if (row["supplier"] or "") != (item.get("supplier", "") or ""):
            mismatches.append("supplier differs: %s" % name)
        if (row["proof_note"] or "") != (item.get("proof_note", "") or ""):
            mismatches.append("proof_note differs: %s" % name)
        if (row["terms_checked_date"] or "") != (item.get("terms_checked_date", "") or ""):
            mismatches.append("terms_checked_date differs: %s" % name)
        if bool(row["permission_confirmed"]) != (item.get("resale_permission_confirmed") is True):
            mismatches.append("permission flag differs: %s" % name)
    extra = [n for n in stored if n not in src]
    return {
        "source_count": len(source), "stored_count": len(rows),
        "names_match": set(src) == set(stored),
        "all_unconfirmed": all(not r["permission_confirmed"] for r in rows),
        "mismatches": mismatches, "extra": extra,
        "lossless": len(source) == len(rows) and set(src) == set(stored)
                    and not mismatches and not extra,
    }


# ------------------------------------------------------------------- CRUD
def create_profile(data, conn=None):
    """Create a profile. data keys: name, industry_preset (key) or
    industry (free text), description, website, target_type, target_text,
    geography, languages, currency, sales_model. A preset seeds funnel/KPI
    defaults + lead stages into settings overrides (editable afterwards)
    and its permission wording onto the profile."""
    conn = conn or get_db()
    name = (data.get("name") or "").strip()
    if not name:
        raise ValueError("Profile name is required")
    preset_key = data.get("industry_preset") or "generic"
    if preset_key not in industries.PRESETS:
        preset_key = industries.preset_key_for_label(preset_key) or "generic"
    preset = industries.get_preset(preset_key)
    industry_text = (data.get("industry") or "").strip() or preset["label"]
    slug = slugify(name)
    base, n = slug, 2
    while get_profile_by_slug(slug, conn):
        slug = "%s-%d" % (base, n)
        n += 1
    overrides = dict(preset["funnel_defaults"])
    if isinstance(overrides.get("LEAD_STAGES"), list):
        overrides["LEAD_STAGES"] = list(overrides["LEAD_STAGES"])
    if (data.get("website") or "").strip():
        overrides["DESTINATION_URL"] = data["website"].strip()
    cur = conn.execute(
        "INSERT INTO profiles (slug, name, industry, industry_preset, description, "
        "website, target_type, target_text, geography, languages, currency, "
        "sales_model, permission_label, settings_overrides, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (slug, name, industry_text, preset_key,
         (data.get("description") or "").strip(),
         (data.get("website") or "").strip(),
         data.get("target_type") or "both",
         (data.get("target_text") or "").strip(),
         (data.get("geography") or "").strip(),
         (data.get("languages") or "").strip(),
         (data.get("currency") or "").strip(),
         data.get("sales_model") or preset["sales_model"],
         preset["permission_label"], json.dumps(overrides), _now()))
    conn.commit()
    profile = get_profile(cur.lastrowid, conn)
    audit(conn, "profile_created", "profile=%s name=%s industry=%s preset=%s"
          % (profile["slug"], name, industry_text, preset_key))
    return profile


def update_profile(profile_id, data, conn=None):
    conn = conn or get_db()
    profile = get_profile(profile_id, conn)
    if profile is None:
        raise KeyError("profile %s not found" % profile_id)
    fields = ("name", "industry", "description", "website", "target_type",
              "target_text", "geography", "languages", "currency", "sales_model")
    updates = {k: data[k] for k in fields if k in data}
    if "industry_preset" in data and data["industry_preset"] in industries.PRESETS:
        updates["industry_preset"] = data["industry_preset"]
        updates["permission_label"] = industries.get_preset(
            data["industry_preset"])["permission_label"]
    if "settings_overrides" in data and isinstance(data["settings_overrides"], dict):
        merged = dict(profile["settings_overrides"])
        merged.update(data["settings_overrides"])
        updates["settings_overrides"] = json.dumps(merged)
    if not updates:
        return profile
    sets = ", ".join("%s = ?" % k for k in updates)
    conn.execute("UPDATE profiles SET %s WHERE id = ?" % sets,
                 list(updates.values()) + [profile_id])
    conn.commit()
    audit(conn, "profile_updated", "profile=%s fields=%s"
          % (profile["slug"], ",".join(updates)))
    return get_profile(profile_id, conn)


def duplicate_profile(profile_id, conn=None):
    conn = conn or get_db()
    src = get_profile(profile_id, conn)
    if src is None:
        raise KeyError("profile %s not found" % profile_id)
    data = {k: src.get(k) for k in ("industry_preset", "industry", "description",
                                     "website", "target_type", "target_text",
                                     "geography", "languages", "currency",
                                     "sales_model")}
    data["name"] = src["name"] + " (copy)"
    clone = create_profile(data, conn)
    conn.execute(
        "UPDATE profiles SET settings_overrides = ? WHERE id = ?",
        (json.dumps(src["settings_overrides"]), clone["id"]))
    for off in list_offerings(profile_id, conn):
        add_offering(clone["id"], off, conn)
    for comp in list_competitors(profile_id, conn):
        add_competitor(clone["id"], comp, conn)
    conn.commit()
    audit(conn, "profile_duplicated", "from=%s to=%s" % (src["slug"], clone["slug"]))
    return get_profile(clone["id"], conn)


def delete_profile(profile_id, conn=None):
    conn = conn or get_db()
    profiles = list_profiles(conn)
    if len(profiles) <= 1:
        raise ValueError("Last profile cannot be deleted")
    profile = get_profile(profile_id, conn)
    if profile is None:
        raise KeyError("profile %s not found" % profile_id)
    was_active = active_profile_id(conn) == profile_id
    for table in ("offerings", "competitors", "loop_runs", "top_creatives"):
        conn.execute("DELETE FROM %s WHERE profile_id = ?" % table, (profile_id,))
    conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
    conn.commit()
    if was_active:
        remaining = list_profiles(conn)
        set_active_profile(remaining[0]["id"], conn)
    audit(conn, "profile_deleted", "profile=%s" % profile["slug"])
    return True


# --------------------------------------------------------------- offerings
def list_offerings(profile_id, conn=None):
    conn = conn or get_db()
    rows = conn.execute("SELECT * FROM offerings WHERE profile_id = ? ORDER BY id",
                        (profile_id,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["permission_confirmed"] = bool(d["permission_confirmed"])
        out.append(d)
    return out


def add_offering(profile_id, data, conn=None):
    conn = conn or get_db()
    name = (data.get("name") or data.get("product") or "").strip()
    if not name:
        raise ValueError("Offering name is required")
    confirmed = data.get("permission_confirmed")
    if confirmed is None:
        confirmed = data.get("resale_permission_confirmed")
    cur = conn.execute(
        "INSERT INTO offerings (profile_id, name, type, category, price, supplier, "
        "permission_confirmed, proof_note, terms_checked_date, destination_override, "
        "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (profile_id, name, data.get("type") or "product",
         data.get("category", "") or "", str(data.get("price", "") or ""),
         data.get("supplier", "") or "", 1 if confirmed is True else 0,
         data.get("proof_note", "") or "", data.get("terms_checked_date", "") or "",
         data.get("destination_override", "") or "", _now()))
    conn.commit()
    return cur.lastrowid


def update_offering(offering_id, data, conn=None):
    conn = conn or get_db()
    fields = ("name", "type", "category", "price", "supplier", "proof_note",
              "terms_checked_date", "destination_override")
    updates = {k: data[k] for k in fields if k in data}
    if "permission_confirmed" in data:
        updates["permission_confirmed"] = 1 if data["permission_confirmed"] is True else 0
    if not updates:
        return
    sets = ", ".join("%s = ?" % k for k in updates)
    conn.execute("UPDATE offerings SET %s WHERE id = ?" % sets,
                 list(updates.values()) + [offering_id])
    conn.commit()


def delete_offering(offering_id, conn=None):
    conn = conn or get_db()
    conn.execute("DELETE FROM offerings WHERE id = ?", (offering_id,))
    conn.commit()


def offerings_as_eligibility(profile_id, conn=None):
    """Eligibility-shaped view of a profile's catalog for policy_checker:
    generic entries carry permission_confirmed; the software profile's
    entries ALSO carry resale_permission_confirmed so the strict resale
    wording/reason is preserved for it."""
    conn = conn or get_db()
    profile = get_profile(profile_id, conn)
    out = []
    for off in list_offerings(profile_id, conn):
        entry = {
            "product": off["name"], "name": off["name"],
            "supplier": off["supplier"] or "",
            "permission_confirmed": bool(off["permission_confirmed"]),
            "proof_note": off["proof_note"] or "",
            "terms_checked_date": off["terms_checked_date"] or "",
            "type": off["type"], "category": off["category"] or "",
            "price": off["price"] or "",
            "destination_override": off["destination_override"] or "",
            "offering_id": off["id"],
        }
        if profile and profile.get("industry_preset") == "software_digital":
            entry["resale_permission_confirmed"] = bool(off["permission_confirmed"])
        out.append(entry)
    return out


# -------------------------------------------------------------- competitors
def list_competitors(profile_id, conn=None):
    conn = conn or get_db()
    rows = conn.execute("SELECT * FROM competitors WHERE profile_id = ? ORDER BY id",
                        (profile_id,)).fetchall()
    return [dict(r) for r in rows]


def add_competitor(profile_id, data, conn=None):
    conn = conn or get_db()
    name = (data.get("name") or "").strip()
    if not name:
        raise ValueError("Competitor name is required")
    cur = conn.execute(
        "INSERT INTO competitors (profile_id, name, handle, url, website, niche, "
        "kind, source, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (profile_id, name, data.get("handle", "") or "", data.get("url", "") or "",
         data.get("website", "") or "", data.get("niche", "") or "",
         data.get("kind", "") or "", data.get("source", "") or "",
         data.get("notes", "") or "", _now()))
    conn.commit()
    return cur.lastrowid


def delete_competitor(competitor_id, conn=None):
    conn = conn or get_db()
    conn.execute("DELETE FROM competitors WHERE id = ?", (competitor_id,))
    conn.commit()


# ---------------------------------------------------------------- settings
def effective_settings(global_settings, profile):
    """Global settings merged with the profile's overrides (overrides win).
    Funnel/KPI defaults seeded from a preset live in the overrides, so
    they are data the owner edits — never logic constants."""
    merged = dict(global_settings or {})
    if profile:
        for key, value in (profile.get("settings_overrides") or {}).items():
            merged[key] = value
    return merged


def compliance_patterns_for(profile):
    if not profile:
        return []
    return industries.compliance_patterns(profile.get("industry_preset"))
