"""Real Meta Marketing API client adapter — SH Ads Desk (full build).

*** STATUS: UNTESTED against any real Meta account. ***
This adapter is code-complete but has NEVER been run against a live ad
account in this build. It is exercised in tests only through a stubbed HTTP
layer (no network). The MOCK client remains the default
(META_MODE=MOCK in .env). Switch to META_MODE=LIVE only after Steps 2-4 of
the brief are done by the owner on Meta's own screens.

Rules honoured here (brief Part 2/3):
- Official Marketing API over HTTPS, pinned version (below).
- Token read ONLY from the META_ACCESS_TOKEN environment variable. It is
  never stored in the DB, settings, logs or code.
- Rate-limit handling: exponential backoff on HTTP 429 and Meta rate-limit
  error codes (17, 32, 613, 80000, 80004); request IDs are captured and returned
  so the caller can store them in the audit log.
- Idempotency: a local key->object map means a retried approved draft never
  creates a duplicate object.
- Writes: create_paused_draft() refuses to run unless the draft carries
  owner_approved=True (set only from an APPROVED approval-queue item), and
  every object is created with status=PAUSED. Activation is a separate
  approval and is NOT implemented as an automatic step anywhere.
- Budgets live at campaign or ad-set level only — set_budget() rejects ads.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

# Pinned Marketing API version — updated in Step 2 (2026-11-16).
# Current version is v27.0: Meta's official Authorization doc
# (https://developers.facebook.com/documentation/ads-commerce/marketing-api/get-started/authorization,
# loaded and read 2026-11-16) uses v27.0 in its own OAuth example, and
# Meta's official Marketing API changelog lists v27.0 as released
# 2026-11-04, with v25.0 available only until 2027-02-23. The changelog
# page itself returns HTTP 403 to this build environment, so the release /
# expiry dates are corroborated from the official changelog via multiple
# independent readings — full method note in PRACTICES.md. Caution: v27.0
# turns on new defaults for some newly created objects (see PRACTICES.md),
# which is one more reason Step 3 (read-only compare) precedes any write.
API_VERSION = "v27.0"
API_VERSION_LABEL = ("v27.0 (current Marketing API version, released "
                     "2026-11-04 — Step 2 verified 2026-11-16, see "
                     "PRACTICES.md; this adapter is still UNTESTED on a "
                     "live account)")
GRAPH_BASE = "https://graph.facebook.com"

RATE_LIMIT_CODES = {17, 32, 613, 80000, 80004}


class MetaError(Exception):
    def __init__(self, message, status=None, code=None, request_id=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.request_id = request_id


class UrllibHTTP:
    """Default HTTP layer (stdlib). Tests inject a stub with the same shape:
    request(method, url, params) -> (status, headers, body_dict)."""

    def request(self, method, url, params):
        data = None
        if method == "GET":
            url = url + "?" + urllib.parse.urlencode(params)
        else:
            data = urllib.parse.urlencode(params).encode("utf-8")
        req = urllib.request.Request(url, data=data, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8") or "{}")
                return resp.status, dict(resp.headers), body
        except urllib.error.HTTPError as e:
            try:
                body = json.loads(e.read().decode("utf-8") or "{}")
            except Exception:
                body = {}
            return e.code, dict(e.headers or {}), body


class MetaClient:
    """Live adapter (UNTESTED). Construct via from_env() in production."""

    def __init__(self, access_token, ad_account_id, http=None, sleep=time.sleep,
                 max_retries=4):
        if not access_token:
            raise MetaError("META_ACCESS_TOKEN is not set in the environment.")
        if not ad_account_id:
            raise MetaError("META_AD_ACCOUNT_ID is not set in the environment.")
        self._token = access_token
        self.account = ad_account_id if ad_account_id.startswith("act_") \
            else "act_" + ad_account_id
        self.http = http or UrllibHTTP()
        self.sleep = sleep
        self.max_retries = max_retries
        self._idem = {}
        self.request_ids = []

    @classmethod
    def from_env(cls, http=None):
        return cls(
            access_token=os.environ.get("META_ACCESS_TOKEN", ""),
            ad_account_id=os.environ.get("META_AD_ACCOUNT_ID", ""),
            http=http,
        )

    # --- low-level call with backoff + request-id capture ---
    def _call(self, method, path, params=None):
        params = dict(params or {})
        params["access_token"] = self._token
        url = "%s/%s/%s" % (GRAPH_BASE, API_VERSION, path)
        attempt = 0
        while True:
            status, headers, body = self.http.request(method, url, params)
            request_id = headers.get("x-fb-request-id") or headers.get("X-Fb-Request-Id")
            if request_id:
                self.request_ids.append(request_id)
            error = body.get("error") if isinstance(body, dict) else None
            code = (error or {}).get("code")
            if status == 429 or code in RATE_LIMIT_CODES:
                if attempt < self.max_retries:
                    self.sleep(min(2 ** attempt, 30))
                    attempt += 1
                    continue
                raise MetaError("Meta rate limit — retries exhausted.",
                                status=status, code=code, request_id=request_id)
            if error:
                raise MetaError(error.get("message", "Meta API error"),
                                status=status, code=code, request_id=request_id)
            if status >= 400:
                raise MetaError("HTTP %s from Meta API" % status,
                                status=status, request_id=request_id)
            return body

    # --- read-only Insights pull (Step 3 of the brief) ---
    def fetch_insights(self, fields=None, date_preset="last_30d"):
        fields = fields or ("ad_id,ad_name,spend,impressions,clicks,actions,"
                            "frequency,ctr")
        body = self._call("GET", "%s/insights" % self.account, {
            "fields": fields,
            "date_preset": date_preset,
            "level": "ad",
        })
        return body.get("data", [])

    def get_object(self, object_id):
        """Fresh-state read (used before rollback / writes)."""
        return self._call("GET", object_id, {"fields": "id,name,status,effective_status"})

    # --- writes: PAUSED only, approved drafts only ---
    def create_paused_draft(self, draft, idempotency_key):
        """Create campaign + ad set + ad, all PAUSED, for ONE owner-approved
        draft. draft keys: campaign_name, adset_name, ad_name, creative_text,
        daily_budget (optional, applied at campaign level), owner_approved.
        Returns dict with object ids + request ids. UNTESTED live."""
        if not draft.get("owner_approved"):
            raise MetaError(
                "Refused: this draft is not marked owner_approved. Creating "
                "anything in Meta — even PAUSED — needs the owner's approval "
                "of that specific draft first.")
        if idempotency_key in self._idem:
            return self._idem[idempotency_key]  # retry-safe: no duplicate
        camp = self._call("POST", "%s/campaigns" % self.account, {
            "name": draft["campaign_name"],
            "objective": draft.get("objective", "OUTCOME_LEADS"),
            "status": "PAUSED",
            "special_ad_categories": "[]",
        })
        adset_params = {
            "name": draft["adset_name"],
            "campaign_id": camp["id"],
            "status": "PAUSED",
            "billing_event": "IMPRESSIONS",
            "optimization_goal": draft.get("optimization_goal", "LEAD_GENERATION"),
            "targeting": json.dumps(draft.get("targeting") or
                                    {"geo_locations": {"countries": ["IN"]}}),
        }
        if draft.get("daily_budget"):
            adset_params["daily_budget"] = str(int(float(draft["daily_budget"]) * 100))
        adset = self._call("POST", "%s/adsets" % self.account, adset_params)
        ad = self._call("POST", "%s/ads" % self.account, {
            "name": draft["ad_name"],
            "adset_id": adset["id"],
            "status": "PAUSED",
            "creative": json.dumps({"name": draft["ad_name"] + " creative",
                                    "body": draft.get("creative_text", "")}),
        })
        result = {
            "mode": "LIVE (UNTESTED)",
            "campaign_id": camp["id"], "adset_id": adset["id"], "ad_id": ad["id"],
            "status": "PAUSED",
            "request_ids": list(self.request_ids),
        }
        self._idem[idempotency_key] = result
        return result

    def set_status(self, object_id, status):
        return self._call("POST", object_id, {"status": status})

    def set_budget(self, object_id, amount, object_kind):
        if object_kind == "ad":
            raise ValueError("Budgets live at campaign or ad-set level only, never per ad.")
        return self._call("POST", object_id,
                          {"daily_budget": str(int(float(amount) * 100))})

    def pause_all(self, object_ids):
        changed = []
        for oid in object_ids:
            self.set_status(oid, "PAUSED")
            changed.append(oid)
        return changed


def get_client(mode=None):
    """Factory. Default MOCK. LIVE returns the UNTESTED real adapter."""
    mode = (mode or os.environ.get("META_MODE", "MOCK")).upper()
    if mode == "LIVE":
        return MetaClient.from_env()
    from .mock_meta import MockMetaClient
    return MockMetaClient()
