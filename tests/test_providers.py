"""API Providers tests — SH Ads Desk.

Everything runs against a STUBBED HTTP layer: no network, no real provider
API is ever called, and every key used here is a fake test string.
Covers: preset pre-fill (base URL + default model), key-only save → working
adapter, secret storage rules (secrets.env only — never settings/config/DB),
blank-key-keeps-old, remove key, env precedence, redaction, test-connection,
text/image/video adapter shaping + parsing, creative fallback, web smoke,
and package hygiene for secrets.
"""
import base64
import json
import os
import re
import stat
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FAKE_KEY = "sk-test-FAKEKEY-1234567890abcdef"


class StubProviderHTTP:
    """Same shape as providers.UrllibHTTP. Records calls; serves canned or
    queued responses. No network."""

    def __init__(self, responses=None, queue=None, bytes_response=(200, b"FILEBYTES")):
        self.calls = []
        self.responses = responses or {}
        self.queue = list(queue or [])
        self.bytes_response = bytes_response

    def request(self, method, url, headers=None, json_body=None, timeout=60):
        self.calls.append({"method": method, "url": url,
                           "headers": dict(headers or {}), "json": json_body})
        if self.queue:
            return self.queue.pop(0)
        for (m, frag), resp in self.responses.items():
            if m == method and frag in url:
                return resp(method, url, json_body) if callable(resp) else resp
        return 200, {}, {}

    def fetch_bytes(self, url, timeout=60):
        self.calls.append({"method": "GETBYTES", "url": url})
        return self.bytes_response


class ProviderEnv(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._keys = ("SH_ADS_DATA_DIR", "SH_ADS_TEXT_API_KEY",
                      "SH_ADS_IMAGE_API_KEY", "SH_ADS_VIDEO_API_KEY",
                      "SH_ADS_DB_PATH", "SH_ADS_SETTINGS_PATH")
        self._old = {k: os.environ.get(k) for k in self._keys}
        os.environ["SH_ADS_DATA_DIR"] = self.tmp
        for k in ("SH_ADS_TEXT_API_KEY", "SH_ADS_IMAGE_API_KEY",
                  "SH_ADS_VIDEO_API_KEY"):
            os.environ.pop(k, None)

    def tearDown(self):
        for k, v in self._old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class TestPresetPrefill(ProviderEnv):
    def test_openai_preset_prefilled_base_and_model(self):
        from app import providers
        cfg = providers.get_config("text", self.tmp)
        self.assertEqual(cfg["base_url"], "https://api.openai.com/v1")
        self.assertEqual(cfg["model"], "gpt-4o-mini")
        self.assertEqual(cfg["chat_path"], "/chat/completions")

    def test_anthropic_preset_prefilled(self):
        from app import providers
        providers.apply_preset("text", "anthropic", self.tmp)
        cfg = providers.get_config("text", self.tmp)
        self.assertEqual(cfg["base_url"], "https://api.anthropic.com")
        self.assertEqual(cfg["chat_path"], "/v1/messages")
        self.assertEqual(cfg["auth_style"], "x-api-key")
        self.assertEqual(cfg["model"], "claude-sonnet-4-5")

    def test_higgsfield_preset_prefilled(self):
        from app import providers
        providers.apply_preset("video", "higgsfield_style", self.tmp)
        cfg = providers.get_config("video", self.tmp)
        self.assertEqual(cfg["base_url"], "https://api.higgsfield.ai")
        self.assertEqual(cfg["auth_prefix"], "Key ")
        self.assertEqual(cfg["poll_path"], "/requests/{id}/status")

    def test_kling_preset_prefilled(self):
        from app import providers
        cfg = providers.get_config("video", self.tmp)
        self.assertEqual(cfg["base_url"], "https://api.klingai.com")
        self.assertEqual(cfg["submit_path"], "/v1/videos/text2video")
        self.assertEqual(cfg["job_id_path"], "data.task_id")


class TestKeyOnlySave(ProviderEnv):
    def test_key_only_save_produces_working_adapter(self):
        """The refinement test: save a known preset with ONLY an API key
        (base URL untouched) → adapter must call the preset's standard
        endpoint with the default model."""
        from app import providers
        providers.save_connection("text", {"preset": "openai_compatible"},
                                  api_key=FAKE_KEY, data_dir_override=self.tmp)
        stub = StubProviderHTTP(responses={
            ("POST", "/chat/completions"): (
                200, {"x-request-id": "req-1"},
                {"choices": [{"message": {"content": "Namaste copy"}}]})})
        adapter = providers.text_adapter(http=stub, data_dir_override=self.tmp)
        out = adapter.generate("Write an ad")
        self.assertEqual(out["text"], "Namaste copy")
        call = stub.calls[0]
        self.assertEqual(call["url"], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(call["headers"]["Authorization"], "Bearer " + FAKE_KEY)
        self.assertEqual(call["json"]["model"], "gpt-4o-mini")
        self.assertEqual(call["json"]["messages"][-1]["content"], "Write an ad")

    def test_custom_preset_requires_base_url(self):
        from app import providers
        with self.assertRaises(ValueError):
            providers.save_connection("text", {"preset": "custom"},
                                      api_key=FAKE_KEY, data_dir_override=self.tmp)
        cfg = providers.save_connection(
            "text", {"preset": "custom", "base_url": "https://llm.example.com/v9"},
            api_key=FAKE_KEY, data_dir_override=self.tmp)
        self.assertEqual(cfg["base_url"], "https://llm.example.com/v9")

    def test_blank_key_keeps_existing_and_remove_works(self):
        from app import providers
        providers.save_connection("image", {"preset": "openai_compatible"},
                                  api_key=FAKE_KEY, data_dir_override=self.tmp)
        providers.save_connection("image", {"preset": "openai_compatible",
                                            "provider_name": "My Images"},
                                  api_key="", data_dir_override=self.tmp)
        self.assertEqual(providers.get_api_key("image", self.tmp), FAKE_KEY)
        providers.remove_api_key("image", self.tmp)
        self.assertEqual(providers.get_api_key("image", self.tmp), "")
        self.assertIsNone(providers.key_source("image", self.tmp))

    def test_env_key_wins_over_file(self):
        from app import providers
        providers.set_api_key("text", "sk-file-key-111111", self.tmp)
        os.environ["SH_ADS_TEXT_API_KEY"] = "sk-env-key-222222"
        self.assertEqual(providers.get_api_key("text", self.tmp), "sk-env-key-222222")
        self.assertEqual(providers.key_source("text", self.tmp), "env")

    def test_invalid_extra_headers_rejected(self):
        from app import providers
        with self.assertRaises(ValueError):
            providers.save_connection("text", {"preset": "openai_compatible",
                                               "extra_headers": "not-json"},
                                      data_dir_override=self.tmp)


class TestSecretStorage(ProviderEnv):
    def test_key_only_in_secrets_env_never_in_config_settings_db(self):
        from app import providers
        from app.common import audit, get_db, save_settings
        providers.save_connection("text", {"preset": "openai_compatible"},
                                  api_key=FAKE_KEY, data_dir_override=self.tmp)
        # config file: no key
        with open(providers.config_path(self.tmp), encoding="utf-8") as f:
            self.assertNotIn(FAKE_KEY, f.read())
        # secrets file: key present, permissions 0600
        spath = providers.secrets_path(self.tmp)
        with open(spath, encoding="utf-8") as f:
            self.assertIn(FAKE_KEY, f.read())
        self.assertEqual(stat.S_IMODE(os.stat(spath).st_mode), 0o600)
        # settings file: no key
        settings_file = os.path.join(self.tmp, "settings.json")
        save_settings({"AUTOMATION_MODE": "PROPOSE"}, settings_file)
        with open(settings_file, encoding="utf-8") as f:
            self.assertNotIn(FAKE_KEY, f.read())
        # SQLite DB raw bytes: no key, even after auditing an event that
        # mentions the key (redaction must scrub it first)
        db = os.path.join(self.tmp, "state.db")
        conn = get_db(db)
        audit(conn, "test_event", "mentioning %s here" % FAKE_KEY)
        conn.close()
        with open(db, "rb") as f:
            self.assertNotIn(FAKE_KEY.encode(), f.read())

    def test_redact_scrubs_registered_key(self):
        from app import providers
        from app.common import redact
        providers.set_api_key("video", FAKE_KEY, self.tmp)
        out = redact("call failed for key %s on server" % FAKE_KEY)
        self.assertNotIn(FAKE_KEY, out)
        self.assertIn("[REDACTED]", out)


class TestConnection(ProviderEnv):
    def setUp(self):
        super().setUp()
        from app import providers
        providers.save_connection("text", {"preset": "openai_compatible"},
                                  api_key=FAKE_KEY, data_dir_override=self.tmp)

    def test_connection_success(self):
        from app import providers
        stub = StubProviderHTTP(responses={
            ("GET", "/models"): (200, {}, {"data": []})})
        result = providers.test_connection("text", http=stub,
                                           data_dir_override=self.tmp)
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], 200)
        self.assertEqual(stub.calls[0]["url"], "https://api.openai.com/v1/models")
        self.assertNotIn(FAKE_KEY, json.dumps(result))

    def test_connection_failure_401(self):
        from app import providers
        stub = StubProviderHTTP(responses={
            ("GET", "/models"): (401, {}, {"error": {"message": "bad key"}})})
        result = providers.test_connection("text", http=stub,
                                           data_dir_override=self.tmp)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], 401)
        self.assertNotIn(FAKE_KEY, json.dumps(result))

    def test_connection_without_key(self):
        from app import providers
        providers.remove_api_key("text", self.tmp)
        result = providers.test_connection("text", http=StubProviderHTTP(),
                                           data_dir_override=self.tmp)
        self.assertFalse(result["ok"])
        self.assertIsNone(result["status"])


class TestTextAdapters(ProviderEnv):
    def test_anthropic_shaping_and_parse(self):
        from app import providers
        providers.apply_preset("text", "anthropic", self.tmp)
        providers.set_api_key("text", "sk-ant-test-333333", self.tmp)
        stub = StubProviderHTTP(responses={
            ("POST", "/v1/messages"): (
                200, {}, {"content": [{"type": "text", "text": "Claude copy"}]})})
        adapter = providers.text_adapter(http=stub, data_dir_override=self.tmp)
        out = adapter.generate("Write an ad", system="Be brief")
        self.assertEqual(out["text"], "Claude copy")
        call = stub.calls[0]
        self.assertEqual(call["url"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(call["headers"]["x-api-key"], "sk-ant-test-333333")
        self.assertEqual(call["headers"]["anthropic-version"], "2023-06-01")
        self.assertEqual(call["json"]["system"], "Be brief")
        self.assertEqual(call["json"]["model"], "claude-sonnet-4-5")
        self.assertEqual(call["json"]["messages"],
                         [{"role": "user", "content": "Write an ad"}])


class TestImageAdapter(ProviderEnv):
    def test_openai_image_flow_saves_file(self):
        from app import creative, providers
        providers.save_connection("image", {"preset": "openai_compatible"},
                                  api_key=FAKE_KEY, data_dir_override=self.tmp)
        stub = StubProviderHTTP(
            responses={("POST", "/images/generations"): (
                200, {}, {"data": [{"url": "https://img.example/p.png"}]})},
            bytes_response=(200, b"PNGDATA"))
        meta = creative.generate_poster_image("Ek saaf poster", http=stub,
                                              data_dir_override=self.tmp)
        saved = os.path.join(self.tmp, "generated", meta["filename"])
        self.assertTrue(os.path.exists(saved))
        with open(saved, "rb") as f:
            self.assertEqual(f.read(), b"PNGDATA")
        self.assertEqual(meta["remote_url"], "https://img.example/p.png")
        self.assertEqual(meta["cost_note"], "unknown — provider billing")
        body = stub.calls[0]["json"]
        self.assertEqual(body["prompt"], "Ek saaf poster")
        self.assertEqual(body["model"], "gpt-image-1")
        self.assertEqual(body["size"], "1024x1024")

    def test_b64_image_flow(self):
        from app import creative, providers
        providers.save_connection("image", {"preset": "openai_compatible"},
                                  api_key=FAKE_KEY, data_dir_override=self.tmp)
        raw = base64.b64encode(b"B64IMG").decode()
        stub = StubProviderHTTP(responses={
            ("POST", "/images/generations"): (
                200, {}, {"data": [{"b64_json": raw}]})})
        meta = creative.generate_poster_image("poster", http=stub,
                                              data_dir_override=self.tmp)
        with open(os.path.join(self.tmp, "generated", meta["filename"]), "rb") as f:
            self.assertEqual(f.read(), b"B64IMG")
        self.assertIsNone(meta["remote_url"])

    def test_custom_field_mapping(self):
        from app import providers
        providers.save_connection("image", {
            "preset": "custom", "base_url": "https://img.local/api",
            "prompt_field": "prompt_text",
            "response_url_path": "result.image.url",
            "response_b64_path": "result.image.b64",
        }, api_key=FAKE_KEY, data_dir_override=self.tmp)
        stub = StubProviderHTTP(responses={
            ("POST", "/images/generations"): (
                200, {}, {"result": {"image": {"url": "https://img.example/q.jpg"}}})})
        adapter = providers.image_adapter(http=stub, data_dir_override=self.tmp)
        out = adapter.generate("custom prompt")
        self.assertEqual(out["kind"], "url")
        self.assertEqual(out["value"], "https://img.example/q.jpg")
        # custom prompt field name is used; model is blank in the custom
        # preset so no model field is sent; size keeps its preset default.
        self.assertEqual(stub.calls[0]["json"],
                         {"prompt_text": "custom prompt", "size": "1024x1024"})
        self.assertEqual(stub.calls[0]["url"], "https://img.local/api/images/generations")


class TestVideoAdapter(ProviderEnv):
    def test_kling_submit_poll_done(self):
        from app import providers
        providers.save_connection("video", {"preset": "kling_style"},
                                  api_key=FAKE_KEY, data_dir_override=self.tmp)
        stub = StubProviderHTTP(queue=[
            (200, {}, {"data": {"task_id": "job-42"}}),
            (200, {}, {"data": {"task_status": "processing"}}),
            (200, {}, {"data": {"task_status": "succeed",
                                "task_result": {"videos": [
                                    {"url": "https://vid.example/v.mp4"}]}}}),
        ])
        adapter = providers.video_adapter(http=stub, data_dir_override=self.tmp)
        sub = adapter.submit("Ek reel banao", duration="5", aspect="9:16")
        self.assertEqual(sub["job_id"], "job-42")
        self.assertEqual(stub.calls[0]["url"],
                         "https://api.klingai.com/v1/videos/text2video")
        self.assertEqual(stub.calls[0]["json"]["model_name"], "kling-v1-6")
        self.assertEqual(stub.calls[0]["json"]["duration"], "5")
        final = adapter.wait_for("job-42", sleep=lambda s: None)
        self.assertEqual(final["state"], "done")
        self.assertEqual(final["result_url"], "https://vid.example/v.mp4")
        self.assertIn("job-42", stub.calls[1]["url"])

    def test_video_failed_status(self):
        from app import providers
        providers.save_connection("video", {"preset": "kling_style"},
                                  api_key=FAKE_KEY, data_dir_override=self.tmp)
        stub = StubProviderHTTP(queue=[
            (200, {}, {"data": {"task_id": "job-7"}}),
            (200, {}, {"data": {"task_status": "failed"}}),
        ])
        adapter = providers.video_adapter(http=stub, data_dir_override=self.tmp)
        sub = adapter.submit("reel")
        final = adapter.wait_for(sub["job_id"], sleep=lambda s: None)
        self.assertEqual(final["state"], "failed")

    def test_higgsfield_auth_and_submit_shape(self):
        from app import providers
        providers.apply_preset("video", "higgsfield_style", self.tmp)
        providers.set_api_key("video", "ID123:SECRET456", self.tmp)
        stub = StubProviderHTTP(queue=[
            (202, {}, {"request_id": "req-9", "status": "queued"})])
        adapter = providers.video_adapter(http=stub, data_dir_override=self.tmp)
        sub = adapter.submit("Higgsfield reel")
        self.assertEqual(sub["job_id"], "req-9")
        call = stub.calls[0]
        self.assertEqual(call["url"],
                         "https://api.higgsfield.ai/kling-video/v3.0/std/text-to-video")
        self.assertEqual(call["headers"]["Authorization"], "Key ID123:SECRET456")


class TestCreativeFallback(ProviderEnv):
    def test_unconfigured_falls_back_to_templates(self):
        from app import creative
        result = creative.generate_copy_with_api(
            "Brain.fm", "students", data_dir_override=self.tmp)
        self.assertEqual(result["source"], "templates")
        self.assertIn("API not connected", result["label"])
        self.assertIn("policy", result)

    def test_configured_uses_api_and_policy_still_applies(self):
        from app import creative, providers
        providers.save_connection("text", {"preset": "openai_compatible"},
                                  api_key=FAKE_KEY, data_dir_override=self.tmp)
        copy_json = json.dumps({
            "hinglish": {"headline": "AI tools ek jagah",
                         "text": "Software Hub par collections dekho",
                         "cta": "Learn More"},
            "english": {"headline": "AI tools in one place",
                        "text": "Browse collections on Software Hub",
                        "cta": "Learn More"}})
        stub = StubProviderHTTP(responses={
            ("POST", "/chat/completions"): (
                200, {}, {"choices": [{"message": {"content": copy_json}}]})})
        result = creative.generate_copy_with_api(
            "Brain.fm", "students", http=stub, data_dir_override=self.tmp)
        self.assertEqual(result["source"], "api")
        self.assertEqual(result["copy"]["hinglish"]["headline"], "AI tools ek jagah")
        # Brain.fm is NOT eligibility-confirmed in the shipped catalog and
        # the destination gate is closed → policy must still block (gate
        # behaviour unchanged by API generation).
        self.assertFalse(result["policy"]["allowed"])
        self.assertEqual(result["cost_note"], "unknown — provider billing")

    def test_unconfigured_generation_buttons_do_not_break(self):
        from app import creative, providers
        with self.assertRaises(providers.NotConfigured):
            creative.generate_poster_image("poster", data_dir_override=self.tmp)
        with self.assertRaises(providers.NotConfigured):
            creative.submit_reel_video("reel", data_dir_override=self.tmp)


class TestProvidersWebSmoke(ProviderEnv):
    def test_providers_page_save_flow_and_key_never_echoed(self):
        import threading
        import urllib.error
        import urllib.parse
        import urllib.request
        from http.cookiejar import CookieJar
        from http.server import ThreadingHTTPServer
        from app.web import Handler

        os.environ["SH_ADS_DB_PATH"] = os.path.join(self.tmp, "state.db")
        settings_file = os.path.join(self.tmp, "settings.json")
        os.environ["SH_ADS_SETTINGS_PATH"] = settings_file
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump({"AUTOMATION_MODE": "PROPOSE", "DRY_RUN": True}, f)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            jar = CookieJar()
            opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(jar))
            base = "http://127.0.0.1:%d" % port

            def get(path):
                with opener.open(base + path, timeout=10) as r:
                    return r.status, r.read().decode("utf-8")

            def post(path, data):
                req = urllib.request.Request(
                    base + path, data=urllib.parse.urlencode(data).encode(),
                    method="POST")
                try:
                    with opener.open(req, timeout=10) as r:
                        return r.status, r.read().decode("utf-8")
                except urllib.error.HTTPError as e:
                    return e.code, e.read().decode("utf-8")

            status, _ = post("/setup", {"password": "smoke-pass-123"})
            self.assertEqual(status, 200)
            status, body = get("/providers")
            self.assertEqual(status, 200)
            self.assertIn("api.openai.com", body)       # pre-filled base URL
            self.assertIn("api.klingai.com", body)      # video preset pre-fill
            self.assertIn("Higgsfield", body)           # higgsfield preset offered
            self.assertIn("Key is not set", body)
            csrf = re.search(r'name="csrf" value="([^"]+)"', body).group(1)
            status, body = post("/providers/save", {
                "csrf": csrf, "capability": "text",
                "preset": "openai_compatible", "provider_name": "My OpenAI",
                "model": "", "base_url": "", "api_key": FAKE_KEY,
                "auth_style": "bearer", "auth_header": "Authorization",
                "auth_prefix": "", "extra_headers": "", "test_path": "/models",
                "payload_format": "openai", "chat_path": "/chat/completions"})
            self.assertEqual(status, 200)
            self.assertNotIn(FAKE_KEY, body)            # key never echoed
            self.assertIn("Key is set", body)
            status, body = get("/creative")
            self.assertEqual(status, 200)
            self.assertIn("Generate with API", body)
            self.assertIn("Connected", body)
        finally:
            server.shutdown()


class TestPackageHygieneProviders(unittest.TestCase):
    def test_no_secrets_env_anywhere_in_package(self):
        for dirpath, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            self.assertNotIn("secrets.env", files,
                             "secrets.env must never be packaged (%s)" % dirpath)

    def test_gitignore_covers_secrets(self):
        with open(os.path.join(ROOT, ".gitignore"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("data/secrets.env", text)
        self.assertIn("data/generated/*", text)


if __name__ == "__main__":
    unittest.main()
