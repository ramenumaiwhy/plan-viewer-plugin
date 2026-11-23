from contextlib import closing
from http.client import HTTPConnection
from http.server import HTTPServer
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest

from server import make_handler


ROOT = Path(__file__).resolve().parents[1]


class PlanPreviewTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.output = Path(temp.name) / "view output"
        config = json.loads((ROOT / "hooks/hooks.json").read_text())
        hook, = config["hooks"]["PreToolUse"]
        self.assertEqual(hook["matcher"], "ExitPlanMode")
        self.command = hook["hooks"][0]["command"]

    def run_hook(self, plan, session="one"):
        return subprocess.run(
            self.command, shell=True, input=json.dumps({"session_id": session, "tool_input": {"plan": plan}}),
            text=True, capture_output=True,
            env=dict(os.environ, CLAUDE_PLUGIN_ROOT=str(ROOT), PLAN_VIEWER_DIR=str(self.output)),
        )

    def preview(self, plan, session="one"):
        result = self.run_hook(plan, session)
        self.assertEqual(result.returncode, 0, result.stderr)
        message = json.loads(result.stdout)
        self.assertEqual(set(message), {"systemMessage"})
        filename = message["systemMessage"].split("/")[1].split()[0]
        return self.output / filename

    def test_submitted_revisions(self):
        first = self.preview("# 予定\n本文 <sample>")
        self.assertIn("# 予定\n本文 &lt;sample&gt;", first.read_text())
        self.assertEqual(first, self.preview("# 予定\n本文 <sample>"))
        self.assertNotEqual(first, self.preview("# 予定\n本文 <sample>", "two"))
        second = self.preview("改訂計画")
        self.assertNotEqual(first, second)
        self.assertIn("改訂計画", second.read_text())
        self.assertTrue(first.exists())

    def test_read_submitted_plan_via_pin_server(self):
        page = self.preview("スマホで承認前に確認")
        original = Path.cwd()
        os.chdir(self.output)
        self.addCleanup(os.chdir, original)
        handler = make_handler(hashlib.sha256(b"1234").hexdigest(), "test")
        with HTTPServer(("127.0.0.1", 0), handler) as server:
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                with closing(HTTPConnection("127.0.0.1", server.server_port)) as client:
                    client.request("GET", "/" + page.name)
                    self.assertIn(b"/api/auth", client.getresponse().read())
                    client.request("POST", "/api/auth", body="pin=1234")
                    login = client.getresponse()
                    self.assertEqual(login.status, 303)
                    cookie = login.getheader("Set-Cookie").split(";", 1)[0]
                    login.read()
                    client.request("GET", "/" + page.name, headers={"Cookie": cookie})
                    response = client.getresponse()
                    self.assertEqual(response.status, 200)
                    self.assertIn("スマホで承認前に確認", response.read().decode())
            finally:
                server.shutdown()
                thread.join()

    def test_missing_plan_and_write_failure_block(self):
        self.assertEqual(self.run_hook("").returncode, 2)
        self.output.touch()
        self.assertEqual(self.run_hook("計画").returncode, 2)
