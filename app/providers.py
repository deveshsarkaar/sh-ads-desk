"""API Providers — SH Ads Desk (owner-connected generation APIs).

The owner plugs in HIS OWN APIs — e.g. OpenAI/ChatGPT or Claude for text,
an image API for posters/carousels, Higgsfield/Kling-style APIs for video —
by picking a preset and pasting an API key. Well-known presets come
PRE-FILLED with the provider's standard base URL and a sensible default
model (sources noted per preset), so for them the owner only pastes the
key. The base URL stays editable as an advanced override and is mandatory
only for the "Custom" preset.

*** STATUS: UNTESTED against real provider accounts. ***
No real key was available while building this, and NO real provider API
was called. Everything here is exercised only through a stubbed HTTP layer
in tests (see tests/test_providers.py). Preset paths/field names are the
providers' documented shapes as of the build date — the owner can edit
every one of them on the API Providers page if a provider differs.

Secret handling (hard rules):
- API keys live ONLY in data/secrets.env (chmod 0600, git-ignored) or in
  environment variables (SH_ADS_TEXT_API_KEY / SH_ADS_IMAGE_API_KEY /
  SH_ADS_VIDEO_API_KEY — env wins over the file).
- Keys are NEVER written to settings.json, provider_config.json, SQLite,
  logs or the audit log, and are NEVER echoed back to the UI (the UI shows
  only "Key set / not set"). Every loaded key is registered with
  common.register_secret() so common.redact() scrubs it from any log line.
- A provider call is a read/generate action only. It can never trigger a
  Meta write (execution lives in execute.py and never imports this file).
"""
import base64
import json
import os
import time
import urllib.error
import urllib.request
import uuid

from . import common
from .common import redact, register_secret

CAPABILITIES = ("text", "image", "video")

ENV_KEY_NAMES = {
    "text": "SH_ADS_TEXT_API_KEY",
    "image": "SH_ADS_IMAGE_API_KEY",
    "video": "SH_ADS_VIDEO_API_KEY",
}

COST_NOTE = "unknown — provider billing"

# --------------------------------------------------------------------------
# Presets. base_url + default model are PRE-FILLED for well-known providers.
# base_url_source says where the endpoint came from; anything not read from
# the provider's own docs in this build is labelled "verify in provider
# docs" and stays fully editable.
# --------------------------------------------------------------------------
_COMMON = {
    "provider_name": "", "base_url": "", "model": "", "auth_style": "bearer",
    "auth_header": "Authorization", "auth_prefix": "", "extra_headers": "",
    "test_path": "", "payload_format": "openai",
}

_TEXT_OPENAI = dict(_COMMON, **{
    "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini",
    "chat_path": "/chat/completions", "test_path": "/models",
})
_TEXT_ANTHROPIC = dict(_COMMON, **{
    "base_url": "https://api.anthropic.com", "model": "claude-sonnet-4-5",
    "auth_style": "x-api-key", "auth_header": "x-api-key",
    "extra_headers": '{"anthropic-version": "2023-06-01"}',
    "chat_path": "/v1/messages", "test_path": "/v1/models",
    "payload_format": "anthropic",
})
_TEXT_CUSTOM = dict(_COMMON, **{"chat_path": "/chat/completions"})

_IMAGE_OPENAI = dict(_COMMON, **{
    "base_url": "https://api.openai.com/v1", "model": "gpt-image-1",
    "image_path": "/images/generations", "test_path": "/models",
    "prompt_field": "prompt", "model_field": "model", "size_field": "size",
    "size": "1024x1024", "response_url_path": "data.0.url",
    "response_b64_path": "data.0.b64_json",
})
_IMAGE_CUSTOM = dict(_IMAGE_OPENAI, **{"base_url": "", "model": ""})

_VIDEO_KLING = dict(_COMMON, **{
    "base_url": "https://api.klingai.com", "model": "kling-v1-6",
    "submit_path": "/v1/videos/text2video",
    "poll_path": "/v1/videos/text2video/{id}",
    "prompt_field": "prompt", "model_field": "model_name",
    "image_field": "image", "duration_field": "duration",
    "aspect_field": "aspect_ratio", "job_id_path": "data.task_id",
    "status_path": "data.task_status", "done_values": "succeed",
    "fail_values": "failed", "result_url_path": "data.task_result.videos.0.url",
    "poll_interval_sec": 10, "max_wait_sec": 600,
})
_VIDEO_HIGGSFIELD = dict(_COMMON, **{
    "base_url": "https://api.higgsfield.ai", "model": "",
    "auth_style": "custom", "auth_header": "Authorization",
    "auth_prefix": "Key ",
    "submit_path": "/kling-video/v3.0/std/text-to-video",
    "poll_path": "/requests/{id}/status",
    "prompt_field": "prompt", "model_field": "",
    "image_field": "image_url", "duration_field": "duration",
    "aspect_field": "aspect_ratio", "job_id_path": "request_id",
    "status_path": "status", "done_values": "completed",
    "fail_values": "failed,error,cancelled",
    "result_url_path": "output.url",
    "poll_interval_sec": 5, "max_wait_sec": 600,
})
_VIDEO_CUSTOM = dict(_VIDEO_KLING, **{
    "base_url": "", "model": "", "submit_path": "/v1/generations",
    "poll_path": "/v1/generations/{id}", "model_field": "model",
    "job_id_path": "id", "status_path": "status",
    "done_values": "completed,done,succeeded", "result_url_path": "result.url",
})

PRESETS = {
    "text": {
        "openai_compatible": {
            "label": "OpenAI (ChatGPT models)",
            "base_url_source": "Official — api.openai.com/v1 (OpenAI API docs)",
            "defaults": _TEXT_OPENAI,
        },
        "anthropic": {
            "label": "Anthropic Claude",
            "base_url_source": "Official — api.anthropic.com (Anthropic API docs)",
            "defaults": _TEXT_ANTHROPIC,
        },
        "custom": {
            "label": "Custom (apna base URL)",
            "base_url_source": "Owner-entered — base URL mandatory hai",
            "defaults": _TEXT_CUSTOM,
        },
    },
    "image": {
        "openai_compatible": {
            "label": "OpenAI-compatible (images)",
            "base_url_source": "Official — api.openai.com/v1 (OpenAI API docs); "
                               "dusre OpenAI-compatible image APIs par bhi base URL badal sakte ho",
            "defaults": _IMAGE_OPENAI,
        },
        "custom": {
            "label": "Custom (apna base URL + field mapping)",
            "base_url_source": "Owner-entered — base URL mandatory hai",
            "defaults": _IMAGE_CUSTOM,
        },
    },
    "video": {
        "kling_style": {
            "label": "Kling (official API shape)",
            "base_url_source": "Official docs shape — api.klingai.com, "
                               "/v1/videos/text2video (Kling open platform docs). "
                               "Note: Kling ka official auth JWT (Access Key + Secret Key se banta hai) "
                               "hai — simple key sirf Kling-compatible gateways par chalegi; paths/fields "
                               "provider docs se verify karo",
            "defaults": _VIDEO_KLING,
        },
        "higgsfield_style": {
            "label": "Higgsfield",
            "base_url_source": "Official — docs.higgsfield.ai: Base URL https://api.higgsfield.ai, "
                               "auth 'Authorization: Key KEY_ID:KEY_SECRET' (key wale khane me "
                               "KEY_ID:KEY_SECRET ek saath paste karo), status /requests/{id}/status. "
                               "Submit path ek model workflow ka hai — apne model ke hisaab se badlo",
            "defaults": _VIDEO_HIGGSFIELD,
        },
        "custom": {
            "label": "Custom (async submit + poll, apna base URL)",
            "base_url_source": "Owner-entered — base URL mandatory hai",
            "defaults": _VIDEO_CUSTOM,
        },
    },
}

DEFAULT_PRESET = {"text": "openai_compatible", "image": "openai_compatible",
                  "video": "kling_style"}

# Fields the owner may save per capability (all optional except Custom's
# base URL). api_key is deliberately NOT in this list — keys never touch
# the config file.
_COMMON_FIELDS = ("preset", "provider_name", "base_url", "model",
                  "auth_style", "auth_header", "auth_prefix",
                  "extra_headers", "test_path", "payload_format")
CONFIG_FIELDS = {
    "text": _COMMON_FIELDS + ("chat_path",),
    "image": _COMMON_FIELDS + ("image_path", "prompt_field", "model_field",
                               "size_field", "size", "response_url_path",
                               "response_b64_path"),
    "video": _COMMON_FIELDS + ("submit_path", "poll_path", "prompt_field",
                               "model_field", "image_field", "duration_field",
                               "aspect_field", "job_id_path", "status_path",
                               "done_values", "fail_values", "result_url_path",
                               "poll_interval_sec", "max_wait_sec"),
}


class ProviderError(Exception):
    def __init__(self, message, status=None):
        super().__init__(redact(message))
        self.status = status


class NotConfigured(ProviderError):
    pass


# --------------------------------------------------------------------------
# Locations (resolved dynamically so tests/hosts can redirect the data dir)
# --------------------------------------------------------------------------
def data_dir():
    return os.environ.get("SH_ADS_DATA_DIR") or common.DATA_DIR


def config_path(data_dir_override=None):
    return os.path.join(data_dir_override or data_dir(), "provider_config.json")


def secrets_path(data_dir_override=None):
    return os.path.join(data_dir_override or data_dir(), "secrets.env")


def generated_dir(data_dir_override=None):
    return os.path.join(data_dir_override or data_dir(), "generated")


# --------------------------------------------------------------------------
# Secrets: env var wins; otherwise data/secrets.env (chmod 0600).
# --------------------------------------------------------------------------
def _read_secrets_file(data_dir_override=None):
    path = secrets_path(data_dir_override)
    out = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                out[k.strip()] = v.strip()
    return out


def _write_secrets_file(values, data_dir_override=None):
    folder = data_dir_override or data_dir()
    os.makedirs(folder, exist_ok=True)
    path = secrets_path(data_dir_override)
    kept = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    if stripped.split("=", 1)[0].strip() in ENV_KEY_NAMES.values():
                        continue  # managed below
                kept.append(line.rstrip("\n"))
    lines = [l for l in kept if l.strip()]
    lines.append("# SH Ads Desk provider API keys — SERVER SECRET. Never commit/share.")
    for name in ENV_KEY_NAMES.values():
        if values.get(name):
            lines.append("%s=%s" % (name, values[name]))
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def get_api_key(cap, data_dir_override=None):
    """Env var first, then the secrets file. Registers the value for log
    redaction as a side effect. Returns '' when no key is set."""
    env_val = os.environ.get(ENV_KEY_NAMES[cap], "")
    if env_val:
        register_secret(env_val)
        return env_val
    val = _read_secrets_file(data_dir_override).get(ENV_KEY_NAMES[cap], "")
    if val:
        register_secret(val)
    return val


def key_source(cap, data_dir_override=None):
    if os.environ.get(ENV_KEY_NAMES[cap]):
        return "env"
    if _read_secrets_file(data_dir_override).get(ENV_KEY_NAMES[cap]):
        return "file"
    return None


def set_api_key(cap, key, data_dir_override=None):
    values = _read_secrets_file(data_dir_override)
    values[ENV_KEY_NAMES[cap]] = key.strip()
    _write_secrets_file(values, data_dir_override)
    register_secret(key.strip())


def remove_api_key(cap, data_dir_override=None):
    values = _read_secrets_file(data_dir_override)
    values.pop(ENV_KEY_NAMES[cap], None)
    _write_secrets_file(values, data_dir_override)


# --------------------------------------------------------------------------
# Non-secret config (provider_config.json in the data dir)
# --------------------------------------------------------------------------
def _load_config_file(data_dir_override=None):
    path = config_path(data_dir_override)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        return {}


def _save_config_file(all_cfg, data_dir_override=None):
    folder = data_dir_override or data_dir()
    os.makedirs(folder, exist_ok=True)
    with open(config_path(data_dir_override), "w", encoding="utf-8") as f:
        json.dump(all_cfg, f, ensure_ascii=False, indent=2, sort_keys=True)


def preset_defaults(cap, preset):
    return dict(PRESETS[cap][preset]["defaults"])


def get_config(cap, data_dir_override=None):
    """Resolved config: preset defaults, overridden by any non-blank saved
    value. A blank saved base_url/model/path therefore falls back to the
    preset's pre-filled value — for known presets the owner never has to
    type a base URL."""
    saved_all = _load_config_file(data_dir_override)
    saved = saved_all.get(cap, {}) if isinstance(saved_all.get(cap, {}), dict) else {}
    preset = saved.get("preset") or DEFAULT_PRESET[cap]
    if preset not in PRESETS[cap]:
        preset = DEFAULT_PRESET[cap]
    cfg = preset_defaults(cap, preset)
    cfg["preset"] = preset
    for key, val in saved.items():
        if key == "preset" or val is None:
            continue
        if isinstance(val, str) and val.strip() == "":
            continue
        cfg[key] = val
    return cfg


def save_connection(cap, fields, api_key=None, data_dir_override=None):
    """Persist one capability's non-secret fields (+ key when a non-blank
    api_key is given; a blank/None api_key KEEPS the existing key).
    Returns the resolved config. Raises ValueError on invalid input."""
    fields = fields or {}
    preset = fields.get("preset") or DEFAULT_PRESET[cap]
    if preset not in PRESETS[cap]:
        raise ValueError("Unknown preset: %s" % preset)
    clean = {"preset": preset}
    for key in CONFIG_FIELDS[cap]:
        if key == "preset" or key not in fields:
            continue
        val = fields[key]
        if isinstance(val, str):
            val = val.strip()
        clean[key] = val
    # numeric guards for video polling
    for num_key, lo, hi in (("poll_interval_sec", 1, 60), ("max_wait_sec", 10, 1800)):
        if num_key in clean and clean[num_key] not in ("", None):
            try:
                clean[num_key] = max(lo, min(hi, int(float(clean[num_key]))))
            except (TypeError, ValueError):
                raise ValueError("%s number hona chahiye" % num_key)
    extra = clean.get("extra_headers") or ""
    if extra:
        try:
            parsed = json.loads(extra)
        except ValueError:
            raise ValueError("Extra headers valid JSON object hona chahiye")
        if not isinstance(parsed, dict):
            raise ValueError("Extra headers JSON object hona chahiye")
        clean["extra_headers"] = json.dumps(parsed, ensure_ascii=False)
    base = clean.get("base_url") or ""
    if base and not base.startswith(("http://", "https://")):
        raise ValueError("Base URL http:// ya https:// se shuru hona chahiye")
    resolved = dict(preset_defaults(cap, preset))
    resolved.update({k: v for k, v in clean.items()
                     if not (isinstance(v, str) and v == "")})
    if preset == "custom" and not (resolved.get("base_url") or "").strip():
        raise ValueError("Custom preset ke liye Base URL zaroori hai — "
                         "bina base URL ke adapter kaam nahi karega")
    all_cfg = _load_config_file(data_dir_override)
    all_cfg[cap] = clean
    _save_config_file(all_cfg, data_dir_override)
    if api_key is not None and str(api_key).strip():
        set_api_key(cap, str(api_key), data_dir_override)
    return get_config(cap, data_dir_override)


def apply_preset(cap, preset, data_dir_override=None):
    """Switch preset and clear the owner's overrides for paths/base/model,
    so the new preset's pre-filled defaults apply. The API key is kept."""
    if preset not in PRESETS[cap]:
        raise ValueError("Unknown preset: %s" % preset)
    all_cfg = _load_config_file(data_dir_override)
    all_cfg[cap] = {"preset": preset}
    _save_config_file(all_cfg, data_dir_override)
    return get_config(cap, data_dir_override)


def is_configured(cap, data_dir_override=None):
    cfg = get_config(cap, data_dir_override)
    return bool((cfg.get("base_url") or "").strip()
                and get_api_key(cap, data_dir_override))


def connection_status(cap, data_dir_override=None):
    cfg = get_config(cap, data_dir_override)
    src = key_source(cap, data_dir_override)
    return {
        "capability": cap, "preset": cfg["preset"],
        "provider_name": cfg.get("provider_name") or PRESETS[cap][cfg["preset"]]["label"],
        "base_url": cfg.get("base_url") or "", "model": cfg.get("model") or "",
        "key_set": bool(src), "key_source": src,
        "configured": bool((cfg.get("base_url") or "").strip() and src),
    }


# --------------------------------------------------------------------------
# HTTP layer (stdlib). Tests inject a stub with the same shape:
#   request(method, url, headers=None, json_body=None, timeout=60)
#       -> (status, headers_dict, body)   body = parsed JSON when possible
#   fetch_bytes(url, timeout=60) -> (status, bytes)
# --------------------------------------------------------------------------
class UrllibHTTP:
    def request(self, method, url, headers=None, json_body=None, timeout=60):
        data = None
        hdrs = dict(headers or {})
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return resp.status, dict(resp.headers), _parse_body(raw)
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            return e.code, dict(e.headers or {}), _parse_body(raw)
        except urllib.error.URLError as e:
            raise ProviderError("Network error: %s" % redact(str(e.reason)))

    def fetch_bytes(self, url, timeout=60):
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except urllib.error.URLError as e:
            raise ProviderError("Download failed: %s" % redact(str(e.reason)))


def _parse_body(raw):
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return raw


def dig(obj, path):
    """Read a dotted path like 'data.0.url' out of nested dicts/lists."""
    if not path:
        return None
    cur = obj
    for part in str(path).split("."):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(cur, dict):
            if part not in cur:
                return None
            cur = cur[part]
        else:
            return None
    return cur


def _request_id(headers, body):
    for name in ("x-request-id", "request-id", "x-fb-request-id"):
        for k, v in (headers or {}).items():
            if k.lower() == name and v:
                return str(v)
    if isinstance(body, dict):
        for path in ("request_id", "id"):
            val = body.get(path)
            if val:
                return str(val)
    return "local-" + uuid.uuid4().hex[:12]


def _extra_headers(cfg):
    raw = cfg.get("extra_headers") or ""
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return {str(k): str(v) for k, v in parsed.items()} if isinstance(parsed, dict) else {}
    except ValueError:
        return {}


def build_headers(cfg, key):
    headers = {}
    style = cfg.get("auth_style") or "bearer"
    if key:
        header_name = cfg.get("auth_header") or (
            "x-api-key" if style == "x-api-key" else "Authorization")
        prefix = cfg.get("auth_prefix")
        if prefix is None or prefix == "":
            prefix = "Bearer " if style == "bearer" else ""
        headers[header_name] = prefix + key
    headers.update(_extra_headers(cfg))
    return headers


def join_url(base, path):
    if not path:
        return (base or "").rstrip("/")
    return (base or "").rstrip("/") + "/" + str(path).lstrip("/")


class BaseAdapter:
    capability = None

    def __init__(self, cfg=None, api_key=None, http=None, data_dir_override=None):
        self.cfg = cfg or get_config(self.capability, data_dir_override)
        self.key = api_key if api_key is not None else get_api_key(
            self.capability, data_dir_override)
        if self.key:
            register_secret(self.key)
        self.http = http or UrllibHTTP()

    def require_ready(self):
        if not (self.cfg.get("base_url") or "").strip():
            raise NotConfigured(
                "%s provider ka Base URL set nahi hai — API Providers page par "
                "preset chuno ya Custom me base URL bharo." % self.capability)
        if not self.key:
            raise NotConfigured(
                "%s provider ki API key set nahi hai — API Providers page par "
                "key paste karo." % self.capability)

    def call(self, method, path, json_body=None, timeout=60):
        self.require_ready()
        url = join_url(self.cfg["base_url"], path)
        status, headers, body = self.http.request(
            method, url, headers=build_headers(self.cfg, self.key),
            json_body=json_body, timeout=timeout)
        rid = _request_id(headers, body)
        if status >= 400:
            msg = None
            if isinstance(body, dict):
                msg = dig(body, "error.message") or body.get("message")
            raise ProviderError(
                "Provider error (HTTP %s)%s" % (
                    status, (": " + str(msg)[:200]) if msg else ""),
                status=status)
        return body, rid


def test_connection(cap, http=None, data_dir_override=None):
    """Smallest safe check: GET the preset's test path (e.g. /models) when
    one is defined, otherwise GET the base URL itself. NEVER a generation
    request. A green result only means the endpoint responded — it does
    NOT guarantee generation will work."""
    cfg = get_config(cap, data_dir_override)
    key = get_api_key(cap, data_dir_override)
    if not (cfg.get("base_url") or "").strip():
        return {"ok": False, "status": None,
                "detail": "Base URL set nahi hai (Custom preset me zaroori hai)."}
    if not key:
        return {"ok": False, "status": None,
                "detail": "API key set nahi hai — pehle key paste karke save karo."}
    register_secret(key)
    http = http or UrllibHTTP()
    url = join_url(cfg["base_url"], cfg.get("test_path") or "")
    try:
        status, _headers, _body = http.request(
            "GET", url, headers=build_headers(cfg, key), timeout=30)
    except ProviderError as e:
        return {"ok": False, "status": e.status, "detail": str(e)[:200]}
    if status < 400:
        return {"ok": True, "status": status,
                "detail": "Endpoint ne jawab diya (HTTP %s). Ye sirf connectivity "
                          "hai — generation ki guarantee nahi." % status}
    hint = " — key reject hui lagti hai, key dobara check karo" if status in (401, 403) else ""
    return {"ok": False, "status": status,
            "detail": "Endpoint ne HTTP %s diya%s." % (status, hint)}


# --------------------------------------------------------------------------
# Text / LLM adapter
# --------------------------------------------------------------------------
class TextAdapter(BaseAdapter):
    capability = "text"

    def generate(self, prompt, system=None):
        if (self.cfg.get("payload_format") or "openai") == "anthropic":
            body = {"model": self.cfg.get("model") or "",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}]}
            if system:
                body["system"] = system
            data, rid = self.call("POST", self.cfg.get("chat_path") or "/v1/messages",
                                  json_body=body)
            text = ""
            if isinstance(data, dict):
                for block in data.get("content") or []:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text += block.get("text", "")
            if not text:
                raise ProviderError("Anthropic response me text nahi mila "
                                    "(shape alag ho sakta hai — UNTESTED adapter).")
            return {"text": text, "request_id": rid,
                    "provider": self.cfg.get("provider_name") or self.cfg["preset"],
                    "model": self.cfg.get("model") or ""}
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        body = {"model": self.cfg.get("model") or "", "messages": messages}
        data, rid = self.call("POST", self.cfg.get("chat_path") or "/chat/completions",
                              json_body=body)
        text = None
        if isinstance(data, dict):
            text = dig(data, "choices.0.message.content")
        if not text:
            raise ProviderError("Chat response me content nahi mila "
                                "(shape alag ho sakta hai — UNTESTED adapter).")
        return {"text": text, "request_id": rid,
                "provider": self.cfg.get("provider_name") or self.cfg["preset"],
                "model": self.cfg.get("model") or ""}


# --------------------------------------------------------------------------
# Image adapter
# --------------------------------------------------------------------------
class ImageAdapter(BaseAdapter):
    capability = "image"

    def generate(self, prompt):
        cfg = self.cfg
        body = {}
        if cfg.get("prompt_field"):
            body[cfg["prompt_field"]] = prompt
        if cfg.get("model_field") and cfg.get("model"):
            body[cfg["model_field"]] = cfg["model"]
        if cfg.get("size_field") and cfg.get("size"):
            body[cfg["size_field"]] = cfg["size"]
        data, rid = self.call("POST", cfg.get("image_path") or "/images/generations",
                              json_body=body, timeout=180)
        url = dig(data, cfg.get("response_url_path") or "")
        if url:
            return {"kind": "url", "value": str(url), "request_id": rid,
                    "provider": cfg.get("provider_name") or cfg["preset"],
                    "model": cfg.get("model") or ""}
        b64 = dig(data, cfg.get("response_b64_path") or "")
        if b64:
            return {"kind": "b64", "value": str(b64), "request_id": rid,
                    "provider": cfg.get("provider_name") or cfg["preset"],
                    "model": cfg.get("model") or ""}
        raise ProviderError(
            "Image response me URL/b64 nahi mila — response field paths "
            "(%s / %s) provider ke docs se match karke API Providers page par badlo."
            % (cfg.get("response_url_path"), cfg.get("response_b64_path")))


# --------------------------------------------------------------------------
# Video adapter — generic async submit + poll
# --------------------------------------------------------------------------
class VideoAdapter(BaseAdapter):
    capability = "video"

    def submit(self, prompt, image_url=None, duration=None, aspect=None):
        cfg = self.cfg
        body = {}
        if cfg.get("prompt_field"):
            body[cfg["prompt_field"]] = prompt
        if cfg.get("model_field") and cfg.get("model"):
            body[cfg["model_field"]] = cfg["model"]
        if image_url and cfg.get("image_field"):
            body[cfg["image_field"]] = image_url
        if duration and cfg.get("duration_field"):
            body[cfg["duration_field"]] = duration
        if aspect and cfg.get("aspect_field"):
            body[cfg["aspect_field"]] = aspect
        data, rid = self.call("POST", cfg.get("submit_path") or "",
                              json_body=body, timeout=120)
        job_id = dig(data, cfg.get("job_id_path") or "")
        if not job_id:
            raise ProviderError(
                "Submit response me job id nahi mila — job_id_path (%s) provider "
                "docs se match karke badlo." % cfg.get("job_id_path"))
        return {"job_id": str(job_id), "request_id": rid,
                "provider": cfg.get("provider_name") or cfg["preset"],
                "model": cfg.get("model") or ""}

    def poll_once(self, job_id):
        cfg = self.cfg
        path = (cfg.get("poll_path") or "").replace("{id}", str(job_id))
        data, rid = self.call("GET", path, timeout=60)
        raw_status = dig(data, cfg.get("status_path") or "")
        state = "pending"
        result_url = None
        if raw_status is not None:
            low = str(raw_status).strip().lower()
            done = {s.strip().lower() for s in (cfg.get("done_values") or "").split(",") if s.strip()}
            fail = {s.strip().lower() for s in (cfg.get("fail_values") or "").split(",") if s.strip()}
            if low in done:
                state = "done"
                val = dig(data, cfg.get("result_url_path") or "")
                result_url = str(val) if val else None
            elif low in fail:
                state = "failed"
        return {"state": state, "raw_status": raw_status,
                "result_url": result_url, "request_id": rid}

    def wait_for(self, job_id, sleep=time.sleep):
        cfg = self.cfg
        try:
            interval = int(cfg.get("poll_interval_sec") or 5)
            max_wait = int(cfg.get("max_wait_sec") or 300)
        except (TypeError, ValueError):
            interval, max_wait = 5, 300
        waited = 0
        last = None
        while True:
            last = self.poll_once(job_id)
            if last["state"] in ("done", "failed"):
                return last
            if waited >= max_wait:
                return dict(last, state="timeout")
            sleep(interval)
            waited += interval


def text_adapter(http=None, data_dir_override=None):
    return TextAdapter(http=http, data_dir_override=data_dir_override)


def image_adapter(http=None, data_dir_override=None):
    return ImageAdapter(http=http, data_dir_override=data_dir_override)


def video_adapter(http=None, data_dir_override=None):
    return VideoAdapter(http=http, data_dir_override=data_dir_override)


def save_generated_file(content_bytes, ext, data_dir_override=None):
    folder = generated_dir(data_dir_override)
    os.makedirs(folder, exist_ok=True)
    name = "%s-%s.%s" % (time.strftime("%Y%m%d%H%M%S"), uuid.uuid4().hex[:8],
                         (ext or "bin").lstrip("."))
    with open(os.path.join(folder, name), "wb") as f:
        f.write(content_bytes)
    return name


def fetch_result_file(url, http=None, timeout=120, data_dir_override=None):
    """Download a provider result URL → (filename, ext). Raises ProviderError."""
    http = http or UrllibHTTP()
    status, raw = http.fetch_bytes(url, timeout=timeout)
    if status >= 400:
        raise ProviderError("Result download failed (HTTP %s)" % status, status=status)
    ext = "bin"
    tail = url.split("?")[0].rsplit(".", 1)
    if len(tail) == 2 and len(tail[1]) <= 5:
        ext = tail[1].lower()
    return save_generated_file(raw, ext, data_dir_override), ext
