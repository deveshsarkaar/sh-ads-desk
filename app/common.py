"""Shared helpers for SH Ads Desk (full build).

Plain stdlib only. Loads/saves settings, loads/saves product eligibility,
redacts secret/PII-looking strings, and provides the SQLite state + audit
log. No secrets, tokens or personal data are stored in code; the Meta token
is read from environment variables only (see meta_client.py) and is never
written to the database or logs.
"""
import json
import os
import re
import sqlite3
from datetime import datetime, timezone

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(PACKAGE_DIR)
DATA_DIR = os.environ.get("SH_ADS_DATA_DIR", os.path.join(PROJECT_DIR, "data"))

DEFAULT_SETTINGS_PATH = os.path.join(PROJECT_DIR, "settings.json")
DEFAULT_ELIGIBILITY_PATH = os.path.join(PROJECT_DIR, "PRODUCT_ELIGIBILITY.yaml")
DEFAULT_DB_PATH = os.path.join(DATA_DIR, "state.db")


def settings_path():
    override = os.environ.get("SH_ADS_SETTINGS_PATH")
    if override:
        return override
    local = os.path.join(DATA_DIR, "settings.json")
    return local if os.path.exists(local) else DEFAULT_SETTINGS_PATH


def eligibility_path():
    return os.environ.get("SH_ADS_ELIGIBILITY_PATH", DEFAULT_ELIGIBILITY_PATH)


def db_path():
    return os.environ.get("SH_ADS_DB_PATH", DEFAULT_DB_PATH)


def load_settings(path=None):
    with open(path or settings_path(), "r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


def save_settings(settings, path=None):
    """Persist owner-edited settings (never contains secrets — the Meta token
    lives only in environment variables, never in settings)."""
    path = path or os.path.join(DATA_DIR, "settings.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    clean = {k: v for k, v in settings.items() if not k.startswith("_")}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2, sort_keys=True)
    return path


def load_eligibility(path=None):
    """Load PRODUCT_ELIGIBILITY.yaml. Uses PyYAML when available; otherwise a
    tiny parser for the simple list-of-maps shape used in that file."""
    path = path or eligibility_path()
    try:
        import yaml  # optional; the fallback parser below covers stdlib-only hosts
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("products", [])
    except ImportError:
        pass
    products, current = [], None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s.startswith("- product:"):
                current = {"product": s.split(":", 1)[1].strip().strip('"')}
                products.append(current)
            elif current is not None and ":" in s:
                key, _, val = s.partition(":")
                val = val.strip().strip('"')
                if key.strip() == "resale_permission_confirmed":
                    current[key.strip()] = val.lower() == "true"
                else:
                    current[key.strip()] = val
    return products


def save_eligibility(products, path=None):
    """Write PRODUCT_ELIGIBILITY.yaml back in the same simple shape.
    Confirmation requires proof note + terms-checked date — enforced by the
    caller (web UI / tests), this function only persists what it is given."""
    path = path or eligibility_path()
    lines = [
        "# PRODUCT_ELIGIBILITY.yaml — SH Ads Desk",
        "# Gate rule (brief rule 5): if resale_permission_confirmed is not true,",
        "# NO ad may be created for that product. Fails closed.",
        "products:",
    ]
    for p in products:
        lines.append('  - product: "%s"' % str(p.get("product", "")).replace('"', "'"))
        lines.append('    supplier: "%s"' % str(p.get("supplier", "") or "").replace('"', "'"))
        lines.append("    resale_permission_confirmed: %s"
                     % ("true" if p.get("resale_permission_confirmed") is True else "false"))
        lines.append('    proof_note: "%s"' % str(p.get("proof_note", "") or "").replace('"', "'"))
        lines.append('    terms_checked_date: "%s"'
                     % str(p.get("terms_checked_date", "") or "").replace('"', "'"))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


# --- Redaction: secrets and personal data must never reach logs/audit. ---
# Literal registry: modules that handle a real secret value (e.g. API
# provider keys in providers.py, the Meta token) register it here so the
# exact value is scrubbed from anything logged, even when it does not match
# a known pattern. Values shorter than 6 chars are ignored (too generic).
_EXTRA_SECRETS = set()


def register_secret(value):
    if value and len(str(value)) >= 6:
        _EXTRA_SECRETS.add(str(value))


_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[REDACTED_EMAIL]"),
    (re.compile(r"\+?\d[\d\s-]{8,}\d"), "[REDACTED_PHONE]"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)(api[_-]?key|access[_-]?token|token|secret|password)\s*[:=]\s*\S+"),
     r"\1=[REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"), "[REDACTED_KEY]"),
    (re.compile(r"\b[A-Fa-f0-9]{32,}\b"), "[REDACTED_HEX]"),
]


def redact(text):
    if text is None:
        return ""
    out = str(text)
    for secret in _EXTRA_SECRETS:
        out = out.replace(secret, "[REDACTED]")
    for pat, repl in _PATTERNS:
        out = pat.sub(repl, out)
    return out


# --- SQLite state + audit log ---
_SCHEMA = """
CREATE TABLE IF NOT EXISTS role_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT, status TEXT, output TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT, payload TEXT, status TEXT DEFAULT 'PENDING',
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT, detail TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS kv (
    key TEXT PRIMARY KEY, value TEXT
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE, password_hash TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY, username TEXT, csrf TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS insight_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset TEXT, row_json TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS lead_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_ref TEXT, status TEXT, count INTEGER DEFAULT 1, created_at TEXT
);
CREATE TABLE IF NOT EXISTS creatives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT, segment TEXT, kind TEXT, content TEXT,
    policy_allowed INTEGER, policy_reasons TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT, kind TEXT, checklist TEXT, visual_check TEXT DEFAULT 'PENDING',
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT, language TEXT, body TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS meta_writes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER, mode TEXT, object_ids TEXT, request_ids TEXT,
    status TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT, message TEXT, created_at TEXT
);
"""


# Columns added when API-generated assets arrived (providers module).
# Applied as a migration so databases created by the earlier build keep
# working — CREATE TABLE IF NOT EXISTS alone would not add them.
_ASSET_EXTRA_COLUMNS = (
    ("source", "TEXT DEFAULT 'manual upload (owner)'"),
    ("provider", "TEXT"),
    ("model", "TEXT"),
    ("prompt", "TEXT"),
    ("cost_note", "TEXT"),
    ("remote_url", "TEXT"),
)


def _migrate(conn):
    existing = {r[1] for r in conn.execute("PRAGMA table_info(assets)").fetchall()}
    for name, decl in _ASSET_EXTRA_COLUMNS:
        if name not in existing:
            conn.execute("ALTER TABLE assets ADD COLUMN %s %s" % (name, decl))
    conn.commit()


def get_db(path=None):
    path = path or db_path()
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    conn.commit()
    _migrate(conn)
    return conn


def _now():
    return datetime.now(timezone.utc).isoformat()


def audit(conn, event, detail=""):
    conn.execute(
        "INSERT INTO audit_log (event, detail, created_at) VALUES (?, ?, ?)",
        (redact(event), redact(detail), _now()),
    )
    conn.commit()


def log_role_run(conn, role, status, output):
    conn.execute(
        "INSERT INTO role_runs (role, status, output, created_at) VALUES (?, ?, ?, ?)",
        (role, status, redact(json.dumps(output, ensure_ascii=False, default=str)), _now()),
    )
    conn.commit()


def log_error(conn, source, message):
    conn.execute(
        "INSERT INTO errors (source, message, created_at) VALUES (?, ?, ?)",
        (redact(source), redact(message), _now()),
    )
    conn.commit()
