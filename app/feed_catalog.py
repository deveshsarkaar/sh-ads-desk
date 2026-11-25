"""Feed/catalog planner — SH Ads Desk V2.

Research basis (25 Nov 2026): feed/catalog automation is a proven
retailer pattern (Hunch/Smartly), but enterprise tools price it far
above SMB reach. This module keeps the useful part simple: map a
Sheets/CSV-style catalog into one clean shape, validate it, and
prepare dynamic price/offer layers plus image-to-video briefs.

Safety rules are unchanged and fail closed:
- Only owner-supplied catalog facts are used; nothing is invented.
- An item is ad-ready only when it is in stock, has a valid product
  link and image, has a price, and its eligibility permission is
  confirmed with proof + terms-checked date recorded.
- Price layers carry the owner's prices as data. Percentage-off
  wording is never generated here; discount claims still need the
  existing policy gates and verified price proof.
- Every output is a proposal for owner approval. No Meta write, no
  catalog upload, and no ad is touched by this module.
"""
import csv
import io
import re
from urllib.parse import urlparse

FIELD_ALIASES = {
    "id": ("id", "item_id", "product_id", "sku", "offering_id"),
    "title": ("title", "name", "product", "product_name", "offering_name"),
    "description": ("description", "desc", "details", "summary"),
    "price": ("price", "regular_price", "mrp", "list_price", "amount"),
    "sale_price": ("sale_price", "offer_price", "discounted_price",
                   "special_price"),
    "currency": ("currency", "currency_code", "curr"),
    "availability": ("availability", "stock", "stock_status", "status"),
    "image_url": ("image_url", "image", "image_link", "photo", "photo_url"),
    "link": ("link", "url", "product_url", "destination_url",
             "destination_override", "landing_page"),
    "brand": ("brand", "manufacturer", "supplier"),
    "category": ("category", "type", "product_type", "collection"),
    "permission_confirmed": ("permission_confirmed",
                             "eligibility_confirmed",
                             "resale_permission_confirmed",
                             "permission", "eligible"),
    "proof_note": ("proof_note", "proof", "proof_reference"),
    "terms_checked_date": ("terms_checked_date", "terms_date",
                           "terms_checked", "checked_date"),
}

_TRUE_VALUES = {"true", "yes", "y", "1", "confirmed", "ok"}
_IN_STOCK_VALUES = {"in stock", "in_stock", "instock", "available",
                    "active", "live", "yes", "true", "1"}
_OUT_OF_STOCK_VALUES = {"out of stock", "out_of_stock", "outofstock",
                        "sold out", "unavailable", "inactive", "paused",
                        "no", "false", "0"}


def _norm_key(key):
    return re.sub(r"[^a-z0-9]+", "_", str(key or "").strip().lower()).strip("_")


def _header_map(headers):
    normalized = {_norm_key(h): h for h in headers or []}
    mapping = {}
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[field] = normalized[alias]
                break
    return mapping


def parse_csv(text):
    """Parse CSV text into raw row dicts. Returns {rows, mapping, errors}."""
    raw = (text or "").lstrip("\ufeff")
    if not raw.strip():
        return {"rows": [], "mapping": {}, "errors": ["Catalog CSV is empty."]}
    try:
        reader = csv.DictReader(io.StringIO(raw))
        rows = [dict(r) for r in reader]
        mapping = _header_map(reader.fieldnames or [])
    except csv.Error as exc:
        return {"rows": [], "mapping": {},
                "errors": ["Catalog CSV could not be read: %s" % exc]}
    errors = []
    if "title" not in mapping:
        errors.append("Catalog CSV needs a title/name/product column.")
    return {"rows": rows, "mapping": mapping, "errors": errors}


def _parse_money(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^0-9.\-]", "", str(value).replace(",", ""))
    if cleaned in ("", "-", ".", "-."):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_bool(value):
    if value is True:
        return True
    return str(value or "").strip().lower() in _TRUE_VALUES


def _availability(value):
    text = str(value or "").strip().lower()
    if text in _IN_STOCK_VALUES:
        return "in_stock"
    if text in _OUT_OF_STOCK_VALUES:
        return "out_of_stock"
    return "unknown"


def _valid_url(value):
    parsed = urlparse(str(value or "").strip())
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _format_money(amount, currency):
    if amount is None:
        return ""
    code = (currency or "").strip().upper()
    value = ("%.2f" % amount).rstrip("0").rstrip(".")
    return ("%s %s" % (code, value)).strip()


def normalize_rows(rows, default_currency=""):
    """Map raw catalog rows (CSV or profile offerings) to clean items."""
    rows = list(rows or [])
    mapping = _header_map(rows[0].keys()) if rows else {}
    items = []
    for index, row in enumerate(rows, start=1):
        row = row or {}

        def pick(field):
            source = mapping.get(field)
            if source is not None:
                return row.get(source)
            return row.get(field)

        price = _parse_money(pick("price"))
        sale_price = _parse_money(pick("sale_price"))
        item = {
            "row": index,
            "id": str(pick("id") or "").strip(),
            "title": str(pick("title") or "").strip(),
            "description": str(pick("description") or "").strip(),
            "price": price,
            "sale_price": sale_price,
            "currency": str(pick("currency") or default_currency or "").strip().upper(),
            "availability": _availability(pick("availability")),
            "image_url": str(pick("image_url") or "").strip(),
            "link": str(pick("link") or "").strip(),
            "brand": str(pick("brand") or "").strip(),
            "category": str(pick("category") or "").strip(),
            "permission_confirmed": _parse_bool(pick("permission_confirmed")),
            "proof_note": str(pick("proof_note") or "").strip(),
            "terms_checked_date": str(pick("terms_checked_date") or "").strip(),
        }
        item["issues"] = validate_item(item)
        item["feed_ready"] = not any(
            issue.startswith("Feed:") for issue in item["issues"])
        item["ad_ready"] = item["feed_ready"] and not any(
            issue.startswith("Ad gate:") for issue in item["issues"])
        item["price_layers"] = build_price_layers(item) if item["ad_ready"] else []
        items.append(item)
    return items


def validate_item(item):
    """Return fail-closed issues. Feed issues block catalog use; ad-gate
    issues block ad preparation even when the feed row is readable."""
    issues = []
    if not item.get("id"):
        issues.append("Feed: item id/SKU is missing.")
    if not item.get("title"):
        issues.append("Feed: title is missing.")
    if not _valid_url(item.get("link")):
        issues.append("Feed: product link must be a valid http/https URL.")
    if not _valid_url(item.get("image_url")):
        issues.append("Feed: image URL must be a valid http/https URL.")
    if item.get("price") is None or item.get("price") < 0:
        issues.append("Feed: price is missing or invalid.")
    if not item.get("currency"):
        issues.append("Feed: currency is missing.")
    if (item.get("sale_price") is not None and item.get("price") is not None
            and item["sale_price"] > item["price"]):
        issues.append("Feed: sale price is higher than regular price.")
    if item.get("availability") != "in_stock":
        issues.append("Ad gate: availability is not confirmed in stock.")
    if item.get("permission_confirmed") is not True:
        issues.append("Ad gate: eligibility permission is not confirmed.")
    elif not item.get("proof_note") or not item.get("terms_checked_date"):
        issues.append(
            "Ad gate: confirmed items still need a proof note and "
            "terms-checked date.")
    return issues


def build_price_layers(item):
    """Dynamic overlay data for one ad-ready item. Prices are owner data;
    no discount-percentage claim is generated."""
    layers = []
    currency = item.get("currency") or ""
    price = item.get("price")
    sale_price = item.get("sale_price")
    if sale_price is not None and price is not None and sale_price < price:
        layers.append({
            "kind": "price",
            "text": _format_money(sale_price, currency),
            "regular_price_text": _format_money(price, currency),
            "note": "Owner-supplied sale price shown as data only; do not add percentage-off wording without verified price proof.",
        })
    elif price is not None:
        layers.append({"kind": "price", "text": _format_money(price, currency),
                       "regular_price_text": "", "note": "Owner-supplied price."})
    if item.get("availability") == "in_stock":
        layers.append({"kind": "availability", "text": "In stock",
                       "regular_price_text": "",
                       "note": "Owner-supplied availability."})
    if item.get("brand"):
        layers.append({"kind": "brand", "text": item["brand"],
                       "regular_price_text": "", "note": "Owner-supplied brand."})
    if item.get("category"):
        layers.append({"kind": "category", "text": item["category"],
                       "regular_price_text": "",
                       "note": "Owner-supplied category."})
    return layers


def build_video_briefs(items, max_briefs=6):
    """Image-to-video briefs for ad-ready items only."""
    briefs = []
    for item in items or []:
        if not item.get("ad_ready"):
            continue
        price_text = ""
        for layer in item.get("price_layers") or []:
            if layer.get("kind") == "price":
                price_text = layer.get("text") or ""
                break
        facts = [item["title"]]
        if price_text:
            facts.append(price_text)
        if item.get("brand"):
            facts.append(item["brand"])
        if item.get("category"):
            facts.append(item["category"])
        briefs.append({
            "item_id": item.get("id") or "",
            "title": item.get("title") or "",
            "image_url": item.get("image_url") or "",
            "link": item.get("link") or "",
            "scenes": [
                "Open on the catalog product image.",
                "Show the product name and price overlay from owner data.",
                "Close with a simple visit-the-product-page call to action.",
            ],
            "overlay_text": " | ".join(facts),
            "facts_used": facts,
            "note": "Brief only — owner approval and existing policy gates still apply before any creative is used.",
        })
        if len(briefs) >= max_briefs:
            break
    return briefs


def rows_from_offerings(offerings, profile=None):
    """Convert stored profile offerings into catalog rows. Missing feed
    fields stay missing and fail closed in validation."""
    profile = profile or {}
    rows = []
    for offering in offerings or []:
        rows.append({
            "id": offering.get("id") or "",
            "title": offering.get("name") or offering.get("product") or "",
            "description": offering.get("description") or "",
            "price": offering.get("price") or "",
            "currency": profile.get("currency") or "",
            "availability": offering.get("availability") or "",
            "image_url": offering.get("image_url") or "",
            "link": offering.get("destination_override") or profile.get("website") or "",
            "brand": offering.get("supplier") or "",
            "category": offering.get("category") or offering.get("type") or "",
            "permission_confirmed": offering.get("permission_confirmed") is True,
            "proof_note": offering.get("proof_note") or "",
            "terms_checked_date": offering.get("terms_checked_date") or "",
        })
    return rows


def analyze_catalog(rows=None, csv_text="", default_currency="",
                    source="catalog"):
    """Analyze catalog rows or CSV text. Returns counts, items, price
    layers (inside ad-ready items), video briefs, and warnings."""
    errors = []
    mapping = {}
    if csv_text:
        parsed = parse_csv(csv_text)
        rows = parsed["rows"]
        mapping = parsed["mapping"]
        errors.extend(parsed["errors"])
        source = "csv"
    items = normalize_rows(rows or [], default_currency=default_currency)
    feed_ready = [i for i in items if i["feed_ready"]]
    ad_ready = [i for i in items if i["ad_ready"]]
    warnings = list(errors)
    if not items:
        warnings.append("No catalog items found — add catalog rows or paste a CSV feed.")
    if items and not ad_ready:
        warnings.append(
            "No item is ad-ready yet. Feed data can be prepared, but ad layers stay blocked until eligibility, stock, image, link, and price checks pass.")
    return {
        "source": source,
        "mapping": mapping,
        "total_items": len(items),
        "feed_ready_count": len(feed_ready),
        "ad_ready_count": len(ad_ready),
        "blocked_count": len(items) - len(ad_ready),
        "items": items,
        "video_briefs": build_video_briefs(items),
        "warnings": warnings,
        "note": "Catalog outputs are proposals only. Existing eligibility, destination, banned-claim, and owner-approval gates still apply.",
    }


def analyze_inputs(inputs, offerings=None, profile=None):
    """Run the catalog analysis from V2 inputs: pasted CSV first, then
    explicit rows, then the active profile's stored offerings."""
    inputs = inputs or {}
    profile = profile or {}
    default_currency = profile.get("currency") or ""
    if inputs.get("catalog_csv_text"):
        return analyze_catalog(csv_text=inputs.get("catalog_csv_text") or "",
                               default_currency=default_currency)
    if inputs.get("catalog_rows"):
        return analyze_catalog(rows=inputs.get("catalog_rows") or [],
                               default_currency=default_currency,
                               source="rows")
    return analyze_catalog(
        rows=rows_from_offerings(offerings or [], profile),
        default_currency=default_currency, source="profile_catalog")
