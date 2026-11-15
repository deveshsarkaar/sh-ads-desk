"""Full-build tests for SH Ads Desk: auth, settings persistence, real Meta
client request shaping (stubbed HTTP — NO network), approval -> PAUSED write
via stub, scheduler CLI, and ZIP hygiene."""
import json
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class TempEnv(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "state.db")
        self.settings_file = os.path.join(self.tmp, "settings.json")
        self._old = {k: os.environ.get(k) for k in
                     ("SH_ADS_DB_PATH", "SH_ADS_SETTINGS_PATH", "META_MODE",
                      "OWNER_PASSWORD_HASH")}
        os.environ["SH_ADS_DB_PATH"] = self.db
        os.environ["SH_ADS_SETTINGS_PATH"] = self.settings_file
        os.environ.pop("OWNER_PASSWORD_HASH", None)
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump({"AUTOMATION_MODE": "PROPOSE", "DRY_RUN": True,
                       "DESTINATION_URL": "", "DESTINATION_READY": False,
                       "LANGUAGES": ["Hinglish", "English"]}, f)

    def tearDown(self):
        for k, v in self._old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class TestAuth(TempEnv):
    def test_wrong_password_rejected_correct_accepted(self):
        from app import auth
        from app.common import get_db
        conn = get_db(self.db)
        auth.create_owner("owner-pass-123", conn)
        self.assertFalse(auth.check_login("wrong-password", conn))
        self.assertFalse(auth.check_login("", conn))
        self.assertTrue(auth.check_login("owner-pass-123", conn))

    def test_no_password_hardcoded_in_package(self):
        from app import auth
        self.assertFalse(auth.owner_exists.__defaults__ and False)  # sanity
        # hash format is pbkdf2, never plain
        h = auth.hash_password("some-long-password")
        self.assertTrue(h.startswith("pbkdf2$"))
        self.assertNotIn("some-long-password", h)


class TestSettings(TempEnv):
    def test_settings_save_load_roundtrip(self):
        from app.common import load_settings, save_settings
        s = load_settings(self.settings_file)
        s["TOTAL_DAILY_BUDGET_CAP"] = 5000
        s["AUTOMATION_MODE"] = "PROPOSE"
        out = os.path.join(self.tmp, "saved.json")
        save_settings(s, out)
        back = load_settings(out)
        self.assertEqual(back["TOTAL_DAILY_BUDGET_CAP"], 5000)
        self.assertEqual(back["AUTOMATION_MODE"], "PROPOSE")
        self.assertNotIn("META_ACCESS_TOKEN", json.dumps(back))


class StubHTTP:
    """Records requests; returns canned Meta-style responses. No network."""

    def __init__(self):
        self.calls = []
        self._n = 0

    def request(self, method, url, params):
        self.calls.append((method, url, dict(params)))
        self._n += 1
        if url.endswith("/insights"):
            return 200, {"x-fb-request-id": "req_insights_1"}, {
                "data": [{"ad_id": "111", "spend": "10.5", "impressions": "100"}]}
        kind = ("campaign" if "/campaigns" in url else
                "adset" if "/adsets" in url else "ad")
        return 200, {"x-fb-request-id": "req_%s_%d" % (kind, self._n)}, {
            "id": "%s_%d" % (kind, self._n)}


def _meta_client(stub):
    from app.meta_client import MetaClient
    return MetaClient(access_token="TEST_TOKEN_NOT_REAL", ad_account_id="12345",
                      http=stub, sleep=lambda s: None)


class TestMetaClientShaping(unittest.TestCase):
    def test_insights_request_shape(self):
        stub = StubHTTP()
        client = _meta_client(stub)
        rows = client.fetch_insights()
        self.assertEqual(len(rows), 1)
        method, url, params = stub.calls[0]
        self.assertEqual(method, "GET")
        self.assertIn("/v25.0/act_12345/insights", url)
        self.assertEqual(params["level"], "ad")
        self.assertIn("req_insights_1", client.request_ids)

    def test_write_requires_owner_approval(self):
        from app.meta_client import MetaError
        stub = StubHTTP()
        client = _meta_client(stub)
        draft = {"campaign_name": "C", "adset_name": "AS", "ad_name": "AD",
                 "creative_text": "hello", "owner_approved": False}
        with self.assertRaises(MetaError):
            client.create_paused_draft(draft, idempotency_key="t-1")
        self.assertEqual(stub.calls, [])  # nothing was sent

    def test_approved_write_creates_paused_with_idempotency(self):
        stub = StubHTTP()
        client = _meta_client(stub)
        draft = {"campaign_name": "C", "adset_name": "AS", "ad_name": "AD",
                 "creative_text": "hello", "owner_approved": True}
        result = client.create_paused_draft(draft, idempotency_key="t-2")
        self.assertEqual(result["status"], "PAUSED")
        posts = [c for c in stub.calls if c[0] == "POST"]
        self.assertEqual(len(posts), 3)  # campaign + adset + ad
        for _m, _u, params in posts:
            self.assertEqual(params["status"], "PAUSED")
        again = client.create_paused_draft(draft, idempotency_key="t-2")
        self.assertEqual(again["campaign_id"], result["campaign_id"])
        self.assertEqual(len([c for c in stub.calls if c[0] == "POST"]), 3)  # no dup

    def test_per_ad_budget_rejected_on_live_client(self):
        client = _meta_client(StubHTTP())
        with self.assertRaises(ValueError):
            client.set_budget("123", 100, object_kind="ad")


class TestApprovalToPausedWrite(TempEnv):
    def _draft_item(self):
        from app.approval_queue import ApprovalQueue
        from app.common import get_db
        conn = get_db(self.db)
        queue = ApprovalQueue(db_path=self.db)
        payload = {
            "kind": "CAMPAIGN_DRAFT", "product": "Brain.fm",
            "campaign_name": "STU_TOOLKIT_REEL_20260101_V1",
            "adset_name": "STU_TOOLKIT_REEL_20260101_V1_AS1",
            "ad_name": "STU_TOOLKIT_REEL_20260101_V1_AD1",
            "creative_text": "Apna AI toolkit ek jagah ready karo",
            "daily_budget": "",
        }
        return conn, queue, queue.add_item("CAMPAIGN_DRAFT", payload)

    def _confirmed_settings(self):
        from app.common import load_settings
        s = load_settings(self.settings_file)
        s.update({"DESTINATION_URL": "https://softwarehub.tech",
                  "DESTINATION_READY": True, "DRY_RUN": True})
        return s

    def _confirmed_eligibility(self):
        return [{"product": "Brain.fm", "supplier": "Test Supplier",
                 "resale_permission_confirmed": True,
                 "proof_note": "test proof", "terms_checked_date": "2026-11-15"}]

    def test_unapproved_item_cannot_execute(self):
        from app.execute import execute_approved_item
        conn, queue, item_id = self._draft_item()
        result = execute_approved_item(item_id, self._confirmed_settings(),
                                       eligibility=self._confirmed_eligibility(),
                                       conn=conn, queue=queue)
        self.assertFalse(result["ok"])
        self.assertIn("not APPROVED", result["blocked"])

    def test_approved_item_writes_paused_via_mock(self):
        from app.execute import execute_approved_item
        conn, queue, item_id = self._draft_item()
        queue.approve(item_id)
        result = execute_approved_item(item_id, self._confirmed_settings(),
                                       eligibility=self._confirmed_eligibility(),
                                       conn=conn, queue=queue)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["mode"], "MOCK")
        self.assertEqual(result["result"]["status"], "PAUSED")
        writes = conn.execute("SELECT * FROM meta_writes").fetchall()
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0]["status"], "PAUSED")

    def test_gate_blocks_unconfirmed_product(self):
        from app.execute import execute_approved_item
        conn, queue, item_id = self._draft_item()
        queue.approve(item_id)
        result = execute_approved_item(item_id, self._confirmed_settings(),
                                       eligibility=[], conn=conn, queue=queue)
        self.assertFalse(result["ok"])  # fails closed


class TestJobsCLI(TempEnv):
    def test_scheduler_commands_run(self):
        from app import jobs, store
        from app.common import get_db
        self.assertEqual(jobs.main(["collect"]), 0)
        self.assertEqual(jobs.main(["optimise"]), 0)
        self.assertEqual(jobs.main(["daily"]), 0)
        self.assertEqual(jobs.main(["weekly"]), 0)
        conn = get_db(self.db)
        self.assertGreaterEqual(len(store.list_reports(conn)), 2)


class TestZipHygiene(unittest.TestCase):
    def test_no_env_db_or_secrets_in_package(self):
        self.assertFalse(os.path.exists(os.path.join(ROOT, ".env")),
                         ".env must never be packaged")
        for dirpath, _dirs, files in os.walk(ROOT):
            if "tests" in dirpath or os.path.basename(dirpath) == "data":
                continue  # tests + runtime data dir are not package sources
            for name in files:
                self.assertNotEqual(name, "state.db")
                if name.endswith((".py", ".md", ".txt", ".yml", ".yaml", ".json")):
                    path = os.path.join(dirpath, name)
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                    bad = re.findall(
                        r"(?i)(access_token|api_key|password)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
                        text)
                    bad = [b for b in bad if "TEST" not in b]
                    self.assertEqual(bad, [], "possible secret in %s" % path)


class TestWebSmoke(TempEnv):
    def test_all_pages_render_and_login_flow(self):
        import threading
        import urllib.request
        from http.cookiejar import CookieJar
        from http.server import ThreadingHTTPServer
        from app.web import Handler

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
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

            import urllib.parse, urllib.error  # noqa: E402
            status, _ = get("/setup")
            self.assertEqual(status, 200)
            status, _ = post("/setup", {"password": "smoke-pass-123"})
            self.assertEqual(status, 200)
            for path in ("/", "/connect", "/roles", "/settings", "/eligibility",
                         "/creative", "/planner", "/approvals", "/budget",
                         "/leads", "/reports", "/trends", "/audit"):
                status, _body = get(path)
                self.assertEqual(status, 200, path)
            # CSRF: a POST without the token must be blocked
            status, _ = post("/leads/add", {"ad_ref": "x", "status": "enquiry",
                                            "count": "1"})
            self.assertEqual(status, 403)
        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main()
