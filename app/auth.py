"""Single-owner authentication — SH Ads Desk (full build).

- Password is NEVER hardcoded and never stored in plain text.
- The owner sets it either on the first-run /setup page (stored as a
  PBKDF2-HMAC-SHA256 hash in the local SQLite DB) or via the
  OWNER_PASSWORD_HASH environment variable (which takes precedence and is
  never written anywhere by the app).
- Generate an env hash with:  python -m app.auth hash
- Sessions are random tokens in the DB; the cookie is HttpOnly + SameSite=Lax
  (Secure when COOKIE_SECURE=1 in .env, e.g. behind HTTPS).
"""
import hashlib
import hmac
import os
import secrets
import sys

from .common import _now, audit, get_db

_ITERATIONS = 240_000


def hash_password(password):
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return "pbkdf2$%d$%s$%s" % (_ITERATIONS, salt.hex(), dk.hex())


def verify_password(password, stored):
    try:
        scheme, iters, salt_hex, hash_hex = stored.split("$")
        if scheme != "pbkdf2":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


def owner_exists(conn=None):
    if os.environ.get("OWNER_PASSWORD_HASH"):
        return True
    conn = conn or get_db()
    row = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
    return row["n"] > 0


def create_owner(password, conn=None):
    conn = conn or get_db()
    if owner_exists(conn):
        raise ValueError("Owner already exists — setup is locked.")
    if len(password or "") < 10:
        raise ValueError("Password must be at least 10 characters.")
    conn.execute(
        "INSERT INTO users (username, password_hash, created_at) VALUES ('owner', ?, ?)",
        (hash_password(password), _now()),
    )
    conn.commit()
    audit(conn, "owner_created", "Single owner account created via first-run setup.")
    return True


def check_login(password, conn=None):
    """Returns True only for the correct owner password."""
    env_hash = os.environ.get("OWNER_PASSWORD_HASH")
    if env_hash:
        return verify_password(password or "", env_hash)
    conn = conn or get_db()
    row = conn.execute(
        "SELECT password_hash FROM users WHERE username = 'owner'").fetchone()
    if row is None:
        return False
    return verify_password(password or "", row["password_hash"])


def create_session(conn=None):
    conn = conn or get_db()
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(24)
    conn.execute(
        "INSERT INTO sessions (token, username, csrf, created_at) VALUES (?, 'owner', ?, ?)",
        (token, csrf, _now()),
    )
    conn.commit()
    return token, csrf


def get_session(token, conn=None):
    if not token:
        return None
    conn = conn or get_db()
    return conn.execute("SELECT * FROM sessions WHERE token = ?", (token,)).fetchone()


def destroy_session(token, conn=None):
    conn = conn or get_db()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "hash":
        import getpass
        pw = getpass.getpass("Owner password (min 10 chars): ")
        if len(pw) < 10:
            print("Too short.")
            sys.exit(1)
        print("Put this line in your .env file (never share it):")
        print("OWNER_PASSWORD_HASH=" + hash_password(pw))
    else:
        print("Usage: python -m app.auth hash")
