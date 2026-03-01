#!/usr/bin/env python3
"""plan-viewer HTTP server with cache-control headers, annotation POST, and optional PIN auth."""
import argparse
import hashlib
import hmac
import json
import os
import secrets
import time
from collections import defaultdict
from http import cookies
from http.server import SimpleHTTPRequestHandler, HTTPServer

MAX_BODY = 64 * 1024  # 64 KB
MAX_ENTRIES = 1000
MAX_PIN_ATTEMPTS = 5  # ロックまでの試行回数
LOCKOUT_SECONDS = 60  # ロック時間

PIN_PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>plan-viewer</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Hiragino Sans', sans-serif;
         background: #0d223a; color: #c8d6e5; display: flex; align-items: center;
         justify-content: center; min-height: 100dvh; }
  .card { background: #0f2744; border: 1px solid #2e445c; border-radius: 16px;
          padding: 32px 28px; width: min(340px, calc(100vw - 40px)); text-align: center; }
  h1 { font-size: 1.1rem; color: #dee4ed; margin-bottom: 8px; }
  p { font-size: 0.85rem; color: #acbcc7; margin-bottom: 24px; }
  input { width: 100%; font-size: 1.8rem; text-align: center; letter-spacing: 0.5em;
          background: #0b2c53; color: #dee4ed; border: 1px solid #2e445c; border-radius: 10px;
          padding: 14px; font-family: 'SFMono-Regular', Consolas, monospace;
          outline: none; -webkit-text-security: disc; }
  input:focus { border-color: #3ea8ff; }
  button { width: 100%; margin-top: 16px; padding: 14px; background: #3ea8ff;
           color: #0d223a; font-size: 1rem; font-weight: bold; border: none;
           border-radius: 10px; cursor: pointer; min-height: 48px; }
  .err { color: #c63939; font-size: 0.85rem; margin-top: 12px; display: none; }
</style>
</head>
<body>
<div class="card">
  <h1>plan-viewer</h1>
  <p>PINコードを入力してください</p>
  <form id="f" method="POST" action="/api/auth">
    <input id="pin" name="pin" type="tel" inputmode="numeric" pattern="[0-9]*"
           maxlength="8" autocomplete="one-time-code" autofocus>
    <button type="submit">OK</button>
  </form>
  <div class="err" id="err">PINが違います</div>
</div>
<script>
var err = location.search.indexOf('err=1') !== -1;
if (err) document.getElementById('err').style.display = 'block';
document.getElementById('pin').focus();
</script>
</body>
</html>"""


def make_handler(pin_hash, auth_token_secret):
    """PIN 認証付きハンドラを生成する。pin_hash が None なら認証なし。"""
    # IP 単位の試行回数トラッキング
    failed_attempts = defaultdict(list)

    class PlanViewerHandler(SimpleHTTPRequestHandler):
        # シンボリックリンク経由の docroot 外アクセスを防ぐ
        def translate_path(self, path):
            resolved = os.path.realpath(super().translate_path(path))
            docroot = os.path.realpath(os.getcwd())
            if not resolved.startswith(docroot + os.sep) and resolved != docroot:
                return docroot
            return resolved

        def end_headers(self):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            super().end_headers()

        def _check_auth(self):
            """PIN 認証が必要なら Cookie をチェック。認証不要 or 認証済みなら True。"""
            if pin_hash is None:
                return True
            cookie_header = self.headers.get('Cookie', '')
            c = cookies.SimpleCookie()
            try:
                c.load(cookie_header)
            except cookies.CookieError:
                return False
            token = c.get('pv-auth')
            if token is None:
                return False
            expected = hashlib.sha256(f"{auth_token_secret}:{pin_hash}".encode()).hexdigest()
            return token.value == expected

        def do_GET(self):
            if not self._check_auth():
                self._serve_pin_page()
                return
            super().do_GET()

        def do_POST(self):
            if self.path == '/api/auth':
                self._handle_auth()
                return
            if not self._check_auth():
                self.send_error(403)
                return
            if self.path != '/api/questions':
                self.send_error(404)
                return
            self._handle_questions()

        def _serve_pin_page(self, error=False):
            page = PIN_PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(page)))
            self.end_headers()
            self.wfile.write(page)

        def _is_locked_out(self):
            """IP 単位のレート制限。一定回数失敗したら一時ロック。"""
            ip = self.client_address[0]
            now = time.time()
            # 期限切れの記録を除去
            failed_attempts[ip] = [t for t in failed_attempts[ip] if now - t < LOCKOUT_SECONDS]
            return len(failed_attempts[ip]) >= MAX_PIN_ATTEMPTS

        def _handle_auth(self):
            if self._is_locked_out():
                self.send_error(429, 'Too Many Requests')
                return

            try:
                content_length = int(self.headers.get('Content-Length', 0))
            except ValueError:
                self.send_error(400)
                return
            if content_length <= 0 or content_length > 1024:
                self.send_error(400)
                return

            body = self.rfile.read(content_length).decode('utf-8')
            # フォーム送信: pin=1234
            submitted_pin = ''
            for pair in body.split('&'):
                if pair.startswith('pin='):
                    submitted_pin = pair[4:].strip()
                    break

            submitted_hash = hashlib.sha256(submitted_pin.encode()).hexdigest()
            if not hmac.compare_digest(submitted_hash, pin_hash):
                ip = self.client_address[0]
                failed_attempts[ip].append(time.time())
                self.send_response(303)
                self.send_header('Location', '/?err=1')
                self.end_headers()
                return

            # 認証成功: 失敗記録をクリア
            ip = self.client_address[0]
            failed_attempts.pop(ip, None)
            token = hashlib.sha256(f"{auth_token_secret}:{pin_hash}".encode()).hexdigest()
            self.send_response(303)
            self.send_header('Set-Cookie', f'pv-auth={token}; Path=/; SameSite=Strict; HttpOnly; Max-Age=86400')
            self.send_header('Location', '/')
            self.end_headers()

        def _handle_questions(self):
            content_type = self.headers.get('Content-Type', '')
            if 'application/json' not in content_type:
                self.send_error(415)
                return

            try:
                content_length = int(self.headers.get('Content-Length', 0))
            except ValueError:
                self.send_error(400)
                return

            if content_length <= 0 or content_length > MAX_BODY:
                self.send_error(413)
                return

            body = self.rfile.read(content_length)

            try:
                question = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400)
                return

            if not isinstance(question, dict):
                self.send_error(400)
                return
            allowed_keys = {'page', 'selectedText', 'comment', 'timestamp'}
            question = {k: v for k, v in question.items() if k in allowed_keys and isinstance(v, str)}
            if not question.get('selectedText'):
                self.send_error(400)
                return

            questions_file = os.path.join(os.getcwd(), 'questions.json')

            try:
                with open(questions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = []

            data.append(question)
            if len(data) > MAX_ENTRIES:
                data = data[-MAX_ENTRIES:]

            # アトミック書き込み: クラッシュ時のデータ破損を防ぐ
            tmp_path = questions_file + '.tmp'
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, questions_file)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())

    return PlanViewerHandler


def main():
    default_dir = os.environ.get('PLAN_VIEWER_DIR', os.path.expanduser('~/plan-viewer'))

    parser = argparse.ArgumentParser(description='plan-viewer HTTP server')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--dir', default=default_dir)
    parser.add_argument('--pin', default=None, help='PIN code (default: random 4-digit)')
    parser.add_argument('--no-pin', action='store_true', help='Disable PIN authentication')
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        os.makedirs(args.dir, exist_ok=True)
        print(f'Created directory: {args.dir}')

    pin_hash = None
    auth_token_secret = secrets.token_hex(16)
    if args.no_pin:
        pin_hash = None
    elif args.pin is not None:
        pin_hash = hashlib.sha256(args.pin.encode()).hexdigest()
    else:
        # デフォルト: ランダム4桁 PIN を生成
        random_pin = f'{secrets.randbelow(10000):04d}'
        pin_hash = hashlib.sha256(random_pin.encode()).hexdigest()
        print(f'PIN: {random_pin}')

    os.chdir(args.dir)
    auth_msg = ' (PIN protected)' if pin_hash else ' (no PIN)'
    print(f'Serving {args.dir} on {args.host}:{args.port}{auth_msg}')

    handler = make_handler(pin_hash, auth_token_secret)
    HTTPServer((args.host, args.port), handler).serve_forever()


if __name__ == '__main__':
    main()
