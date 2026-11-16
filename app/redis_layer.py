"""Redis layer — SH Ads Desk (advanced upgrade).

A minimal Redis client written on the Python standard library only
(raw RESP protocol over a socket), so the system keeps its
zero-pip-dependency promise while gaining a real Redis fast lane:

  * job queue backing (see job_queue.py)
  * short-lived cache for insights/report fragments
  * worker heartbeat + distributed "already running" lock

Redis is OPTIONAL. If REDIS_URL is not set or the server is
unreachable, every caller falls back to the built-in SQLite path —
the system never stops working because Redis is down. That fallback
is deliberate: no single component is a hard dependency.

Config (env only, never in the repo):
  REDIS_URL=redis://localhost:6379/0   (password via URL if needed)

Only the commands the system actually uses are implemented:
PING, SET (EX/NX), GET, DEL, LPUSH, RPOP, LLEN, INCR, EXPIRE.
"""
import os
import socket
from urllib.parse import urlparse


def _encode_command(*parts):
    out = [("*%d\r\n" % len(parts)).encode()]
    for part in parts:
        if isinstance(part, str):
            part = part.encode("utf-8")
        out.append(("$%d\r\n" % len(part)).encode() + part + b"\r\n")
    return b"".join(out)


class _RESPReader:
    """Tiny RESP reply parser (simple strings, errors, integers,
    bulk strings, arrays) — enough for the commands above."""

    def __init__(self, sock):
        self._buf = b""
        self._sock = sock

    def _read(self, n):
        while len(self._buf) < n:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise ConnectionError("redis connection closed")
            self._buf += chunk
        data, self._buf = self._buf[:n], self._buf[n:]
        return data

    def _line(self):
        while b"\r\n" not in self._buf:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise ConnectionError("redis connection closed")
            self._buf += chunk
        line, self._buf = self._buf.split(b"\r\n", 1)
        return line

    def read_reply(self):
        prefix = self._read(1)
        if prefix == b"+":
            return self._line().decode("utf-8", "replace")
        if prefix == b"-":
            raise RuntimeError("redis error: " +
                               self._line().decode("utf-8", "replace"))
        if prefix == b":":
            return int(self._line())
        if prefix == b"$":
            size = int(self._line())
            if size == -1:
                return None
            data = self._read(size)
            self._read(2)  # trailing CRLF
            return data.decode("utf-8", "replace")
        if prefix == b"*":
            count = int(self._line())
            if count == -1:
                return None
            return [self.read_reply() for _ in range(count)]
        raise RuntimeError("unexpected RESP prefix %r" % prefix)


class RedisClient:
    """One short-lived connection per operation batch — simple and
    robust for this system's low request rate."""

    def __init__(self, url):
        parsed = urlparse(url)
        self.host = parsed.hostname or "localhost"
        self.port = parsed.port or 6379
        self.password = parsed.password
        db = (parsed.path or "/0").strip("/") or "0"
        self.db = int(db) if db.isdigit() else 0
        self._sock = None
        self._reader = None

    def _connect(self):
        self._sock = socket.create_connection((self.host, self.port),
                                              timeout=5)
        self._reader = _RESPReader(self._sock)
        if self.password:
            self._command("AUTH", self.password)
        if self.db:
            self._command("SELECT", str(self.db))

    def _command(self, *parts):
        if self._sock is None:
            self._connect()
        self._sock.sendall(_encode_command(*parts))
        return self._reader.read_reply()

    def close(self):
        try:
            if self._sock is not None:
                self._sock.close()
        finally:
            self._sock = None
            self._reader = None

    # -- the small command surface the system uses -------------------
    def ping(self):
        return self._command("PING") == "PONG"

    def set(self, key, value, ex=None, nx=False):
        parts = ["SET", key, value]
        if ex:
            parts += ["EX", str(int(ex))]
        if nx:
            parts.append("NX")
        return self._command(*parts)

    def get(self, key):
        return self._command("GET", key)

    def delete(self, key):
        return self._command("DEL", key)

    def lpush(self, key, value):
        return self._command("LPUSH", key, value)

    def rpop(self, key):
        return self._command("RPOP", key)

    def llen(self, key):
        return self._command("LLEN", key)

    def lrange(self, key, start=0, stop=-1):
        return self._command("LRANGE", key, str(start), str(stop)) or []

    def incr(self, key):
        return self._command("INCR", key)


def get_client():
    """Return a connected RedisClient, or None when Redis is not
    configured / not reachable. Callers MUST handle None by using
    the SQLite fallback — Redis is an accelerator, never a single
    point of failure."""
    url = os.environ.get("REDIS_URL", "").strip()
    if not url:
        return None
    client = RedisClient(url)
    try:
        if client.ping():
            return client
    except Exception:
        pass
    client.close()
    return None


def redis_available():
    client = get_client()
    if client is None:
        return False
    client.close()
    return True
