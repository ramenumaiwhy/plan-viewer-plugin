#!/usr/bin/env python3
"""Security regression tests for the View HTTP server."""

import hashlib
import importlib.util
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from contextlib import closing
from email.message import Message
from http.client import HTTPConnection
from http.server import HTTPServer
from pathlib import Path
from types import SimpleNamespace


SERVER_PATH = Path(__file__).with_name("server.py")
SPEC = importlib.util.spec_from_file_location("plan_viewer_server", SERVER_PATH)
SERVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SERVER)


class ServerSecurityTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.previous_cwd = os.getcwd()
        os.chdir(self.tempdir.name)
        Path("index.html").write_text("<title>View</title>", encoding="utf-8")
        Path("questions.json").write_text('[{"comment":"private"}]', encoding="utf-8")
        Path("questions.json.tmp").write_text('[{"comment":"temporary"}]', encoding="utf-8")
        Path("questions.json.bak").write_text('[{"comment":"backup"}]', encoding="utf-8")
        Path("questions.json~").write_text('[{"comment":"editor backup"}]', encoding="utf-8")
        Path(".git").mkdir()
        Path(".git/HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
        Path("scripts").mkdir()
        Path("scripts/internal.py").write_text("SECRET = True\n", encoding="utf-8")

        handler = SERVER.make_handler(None, "test-secret")
        self.httpd = HTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.httpd.server_port}"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()
        os.chdir(self.previous_cwd)
        self.tempdir.cleanup()

    def status(self, path, method="GET"):
        request = urllib.request.Request(self.base_url + path, method=method)
        try:
            with urllib.request.urlopen(request) as response:
                return response.status
        except urllib.error.HTTPError as error:
            status = error.code
            error.close()
            return status

    def post_question_status(self, payload, headers=None):
        body = json.dumps(payload).encode()
        request_headers = {"Content-Type": "application/json"}
        request_headers.update(headers or {})
        request = urllib.request.Request(
            self.base_url + "/api/questions",
            data=body,
            headers=request_headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.status
        except urllib.error.HTTPError as error:
            status = error.code
            error.close()
            return status

    def test_pin_login_and_read_page(self):
        pin_hash = hashlib.sha256(b"1234").hexdigest()
        self.httpd.RequestHandlerClass = SERVER.make_handler(pin_hash, "test-secret")
        with closing(HTTPConnection("127.0.0.1", self.httpd.server_port)) as client:
            client.request("GET", "/")
            self.assertIn(b"/api/auth", client.getresponse().read())
            client.request("POST", "/api/auth", body="pin=1234")
            response = client.getresponse()
            self.assertEqual(response.status, 303)
            cookie = response.getheader("Set-Cookie").split(";", 1)[0]
            response.read()
            client.request("GET", "/", headers={"Cookie": cookie})
            self.assertEqual(client.getresponse().read(), b"<title>View</title>")

    def test_directory_without_index_is_private(self):
        Path("assets").mkdir()
        self.assertEqual(self.status("/assets/"), 404)

    def test_private_files_are_not_served(self):
        self.assertEqual(self.status("/"), 200)
        for path in (
            "/questions.json",
            "/questions.json?cache=bust",
            "/questions.json.tmp",
            "/questions.json.bak",
            "/questions.json~",
            "/.git/HEAD",
            "/%2egit/HEAD",
            "/scripts/internal.py",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.status(path), 404)
                self.assertEqual(self.status(path, method="HEAD"), 404)

    def test_non_local_post_is_rejected_without_changing_comments(self):
        existing = [{"page": "one.html", "selectedText": "one", "comment": "first", "timestamp": "1"}]
        questions_file = Path("questions.json")
        questions_file.write_text(json.dumps(existing), encoding="utf-8")
        before = questions_file.read_bytes()

        status = self.post_question_status(
            {
                "page": "three.html",
                "selectedText": "three",
                "comment": "third",
                "timestamp": "3",
            },
            headers={
                "Host": "view.example.ts.net",
                "Tailscale-Headers-Info": "https://tailscale.com/s/serve-headers",
                "Tailscale-User-Login": "attacker@example.com",
                "Tailscale-User-Name": "Attacker",
                "X-Forwarded-For": "203.0.113.10",
                "X-Forwarded-Host": "view.example.ts.net",
                "X-Forwarded-Proto": "https",
            },
        )

        self.assertEqual(status, 403)
        self.assertEqual(questions_file.read_bytes(), before)

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires secure question storage")
    def test_authenticated_tailscale_serve_post_is_allowed(self):
        status = self.post_question_status(
            {
                "page": "tailnet.html",
                "selectedText": "trusted tailnet",
                "comment": "trusted",
                "timestamp": "5",
            },
            headers={
                "Host": "view.example.ts.net",
                "Tailscale-Headers-Info": "https://tailscale.com/s/serve-headers",
                "Tailscale-User-Login": "user@example.com",
                "Tailscale-User-Name": "Tailnet User",
                "X-Forwarded-For": "100.64.0.10",
                "X-Forwarded-Host": "view.example.ts.net",
                "X-Forwarded-Proto": "https",
            },
        )
        self.assertEqual(status, 200)
        saved = json.loads(Path("questions.json").read_text(encoding="utf-8"))
        self.assertEqual(saved[-1]["selectedText"], "trusted tailnet")

    def test_question_storage_without_nofollow(self):
        questions = Path("questions.json")
        before = questions.read_bytes()
        if hasattr(os, "O_NOFOLLOW"):
            self.addCleanup(setattr, os, "O_NOFOLLOW", os.O_NOFOLLOW)
            del os.O_NOFOLLOW
        with closing(HTTPConnection("127.0.0.1", self.httpd.server_port)) as client:
            client.request("POST", "/api/questions", body='{"selectedText":"one"}',
                           headers={"Content-Type": "application/json"})
            response = client.getresponse()
            self.assertEqual(response.status, 501)
            self.assertIn(b"os.O_NOFOLLOW", response.read())
        self.assertEqual(self.status("/"), 200)
        self.assertEqual(questions.read_bytes(), before)

    def writer(self, client_ip, host):
        headers = Message()
        headers["Host"] = host
        handler = SERVER.make_handler(None, "test-secret")
        request = handler.__new__(handler)
        request.client_address = (client_ip, 54321)
        request.headers = headers
        return request

    def test_direct_tailnet_address_can_write(self):
        self.assertTrue(self.writer("100.64.0.11", "100.64.0.10:8765")._can_write())
        self.assertTrue(self.writer("100.101.2.3", "mbp.example.ts.net:8765")._can_write())

    def test_outside_tailnet_or_foreign_host_cannot_write(self):
        self.assertFalse(self.writer("192.168.1.20", "192.168.1.10:8765")._can_write())
        # DNS rebinding: tailnet 端末のブラウザが別名のサイトから書き込もうとする
        self.assertFalse(self.writer("100.64.0.11", "evil.example.com:8765")._can_write())
        # 公開登録は Mac 自身だけ
        self.assertFalse(self.writer("100.64.0.11", "100.64.0.10:8765")._is_mac_itself())

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires secure question storage")
    def test_questions_symlink_rejected(self):
        target = Path("original.json")
        questions = Path("questions.json")
        questions.rename(target)
        before = target.read_bytes()
        questions.symlink_to(target)
        self.assertEqual(self.post_question_status({"selectedText": "one"}), 500)
        self.assertTrue(questions.is_symlink())
        self.assertEqual(target.read_bytes(), before)

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires secure question storage")
    def test_fixed_temp_filename_is_unused(self):
        target = Path("unchanged.txt")
        target.write_text("unchanged")
        old_temp = Path("questions.json.tmp")
        old_temp.unlink()
        old_temp.symlink_to(target)
        self.assertEqual(self.post_question_status({"selectedText": "one"}), 200)
        self.assertEqual(target.read_text(), "unchanged")
        self.assertTrue(old_temp.is_symlink())

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires secure question storage")
    def test_localhost_post_remains_available(self):
        status = self.post_question_status(
            {
                "page": "local.html",
                "selectedText": "local test",
                "comment": "local",
                "timestamp": "4",
            }
        )
        self.assertEqual(status, 200)
        saved = json.loads(Path("questions.json").read_text(encoding="utf-8"))
        self.assertEqual(saved[-1]["selectedText"], "local test")


class ViewsApiTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.previous_cwd = os.getcwd()
        os.chdir(self.tempdir.name)
        self.httpd = HTTPServer(("127.0.0.1", 0), SERVER.make_handler(None, "test-secret"))
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.httpd.server_port}"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()
        os.chdir(self.previous_cwd)
        self.tempdir.cleanup()

    def call(self, method, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(self.base_url + path, data=data, method=method,
                                         headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            body = error.read()
            error.close()
            try:
                return error.code, json.loads(body)
            except json.JSONDecodeError:
                return error.code, None

    def register(self, page="2026-11-25_a.html", project="読書メモ"):
        return self.call("POST", "/api/views", {"page": page, "title": "A", "project": project})

    def test_empty_list(self):
        self.assertEqual(self.call("GET", "/api/views"), (200, {"revision": 0, "views": []}))

    def test_register_then_list(self):
        status, body = self.register()
        self.assertEqual(status, 201)
        self.assertEqual(body["view"]["icon"], "file-text")
        _, listed = self.call("GET", "/api/views")
        self.assertEqual(listed["revision"], 1)
        self.assertEqual([v["project"] for v in listed["views"]], ["読書メモ"])

    def test_register_requires_project(self):
        status, _ = self.call("POST", "/api/views", {"page": "a.html", "title": "A"})
        self.assertEqual(status, 400)

    def test_reregister_keeps_marks(self):
        self.register()
        self.call("POST", "/api/views/2026-11-25_a.html", {"pinned": True})
        status, body = self.register(project="旅行")
        self.assertEqual(status, 200)
        self.assertTrue(body["view"]["pinned"])
        self.assertEqual(body["view"]["project"], "旅行")

    def test_archive_clears_pin_and_page_is_url_encoded(self):
        page = "https://mbp.example.ts.net/memo/"
        self.register(page=page)
        quoted = urllib.parse.quote(page, safe="")
        self.call("POST", f"/api/views/{quoted}", {"pinned": True})
        status, body = self.call("POST", f"/api/views/{quoted}", {"archived": True})
        self.assertEqual(status, 200)
        self.assertEqual((body["view"]["pinned"], body["view"]["archived"]), (False, True))

    def test_stale_change_gets_conflict_with_mac_value(self):
        self.register()
        _, body = self.call("POST", "/api/views/2026-11-25_a.html", {"archived": True})
        status, conflict = self.call("POST", "/api/views/2026-11-25_a.html",
                                     {"archived": False, "changed_at": "2000-01-01T00:00:00+09:00"})
        self.assertEqual(status, 409)
        self.assertTrue(conflict["view"]["archived"])
        status, _ = self.call("POST", "/api/views/2026-11-25_a.html",
                              {"archived": False, "changed_at": body["view"]["changed_at"]})
        self.assertEqual(status, 200)

    def test_bad_updates_are_rejected(self):
        self.register()
        for payload in ({}, {"pinned": "yes"}, {"pinned": True, "archived": True}, {"archived": True, "changed_at": "x"}):
            with self.subTest(payload=payload):
                self.assertEqual(self.call("POST", "/api/views/2026-11-25_a.html", payload)[0], 400)
        self.assertEqual(self.call("POST", "/api/views/missing.html", {"pinned": True})[0], 404)

    def test_views_file_is_not_served(self):
        self.register()
        self.assertEqual(self.call("GET", "/views.json")[0], 404)


if __name__ == "__main__":
    unittest.main()
