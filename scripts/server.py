#!/usr/bin/env python3
"""View HTTP server with cache-control headers, annotation POST, and optional PIN auth."""
import argparse
import hashlib
import hmac
import ipaddress
import json
import os
import secrets
import sys
import time
from tempfile import NamedTemporaryFile
from collections import defaultdict
from http import cookies
from urllib.parse import unquote, unquote_plus, urlsplit
from http.server import SimpleHTTPRequestHandler, HTTPServer

MAX_BODY = 64 * 1024  # 64 KB
MAX_ENTRIES = 1000
MAX_PIN_ATTEMPTS = 5  # ロックまでの試行回数
LOCKOUT_SECONDS = 60  # ロック時間
TAILSCALE_IPV4 = ipaddress.ip_network('100.64.0.0/10')
TAILSCALE_IPV6 = ipaddress.ip_network('fd7a:115c:a1e0::/48')

PIN_PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>View</title>
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
  <h1>View</h1>
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
        def list_directory(self, path):
            self.send_error(404)
            return None

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
            return hmac.compare_digest(token.value, expected)

        def _is_private_path(self):
            """コメント保存ファイルとドットファイルの静的配信を拒否する。"""
            path = unquote(urlsplit(self.path).path)
            parts = [part for part in path.split('/') if part]
            target = super().translate_path(self.path)
            if os.path.realpath(target) != os.path.abspath(target):
                return True
            if os.path.isdir(target) and any(os.path.islink(os.path.join(target, name)) for name in ('index.html', 'index.htm')):
                return True
            if any(part.startswith('.') for part in parts):
                return True
            if parts:
                filename = parts[-1].lower()
                if filename == 'questions.json' or filename.startswith('questions.json.') or filename == 'questions.json~':
                    return True
            return bool(parts and parts[0].lower() in {'scripts', '__pycache__'})

        def _is_local_request(self):
            """localhost、認証済みTailscale Serveを許可する。"""
            try:
                client_ip = ipaddress.ip_address(self.client_address[0])
            except ValueError:
                return False

            try:
                hostname = urlsplit(f"//{self.headers.get('Host', '')}").hostname
            except ValueError:
                return False

            forwarded_headers = ('Forwarded', 'X-Forwarded-For', 'X-Forwarded-Host', 'X-Real-IP')
            if not client_ip.is_loopback:
                return False

            if hostname in {'localhost', '127.0.0.1', '::1'}:
                return not any(self.headers.get(header) for header in forwarded_headers)

            if self.headers.get('Tailscale-Headers-Info') != 'https://tailscale.com/s/serve-headers':
                return False
            if not self.headers.get('Tailscale-User-Login', '').strip():
                return False
            if not self.headers.get('Tailscale-User-Name', '').strip():
                return False
            if self.headers.get('X-Forwarded-Proto') != 'https':
                return False
            if self.headers.get('X-Forwarded-Host') != self.headers.get('Host'):
                return False

            try:
                forwarded_ip = ipaddress.ip_address(self.headers.get('X-Forwarded-For', ''))
            except ValueError:
                return False
            return forwarded_ip in TAILSCALE_IPV4 or forwarded_ip in TAILSCALE_IPV6

        def do_GET(self):
            if not self._check_auth():
                self._serve_pin_page()
                return
            if self._is_private_path():
                self.send_error(404)
                return
            super().do_GET()

        def do_HEAD(self):
            if not self._check_auth():
                self._serve_pin_page()
                return
            if self._is_private_path():
                self.send_error(404)
                return
            super().do_HEAD()

        def do_POST(self):
            if self.path == '/api/auth' and pin_hash is not None:
                self._handle_auth()
                return
            if not self._check_auth():
                self.send_error(403)
                return
            if self.path != '/api/questions':
                self.send_error(404)
                return
            if not self._is_local_request():
                self.send_error(403)
                return
            self._handle_questions()

        def _serve_pin_page(self, error=False):
            page = PIN_PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(page)))
            self.end_headers()
            if self.command != 'HEAD':
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

            try:
                body = self.rfile.read(content_length).decode('utf-8')
            except UnicodeDecodeError:
                self.send_error(400)
                return
            # フォーム送信: pin=1234
            submitted_pin = ''
            for pair in body.split('&'):
                if pair.startswith('pin='):
                    submitted_pin = unquote_plus(pair[4:]).strip()
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
            except (UnicodeDecodeError, json.JSONDecodeError):
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

            nofollow = getattr(os, 'O_NOFOLLOW', None)
            if nofollow is None:
                self.send_error(501, 'Saving questions requires os.O_NOFOLLOW on the server')
                return

            questions_file = os.path.join(os.getcwd(), 'questions.json')

            try:
                try:
                    fd = os.open(questions_file, os.O_RDONLY | nofollow)
                except FileNotFoundError:
                    data = []
                else:
                    with os.fdopen(fd, encoding='utf-8') as f:
                        data = json.load(f)
                    if not isinstance(data, list):
                        raise ValueError("invalid questions file")

                data.append(question)
                tmp = NamedTemporaryFile(mode='w', encoding='utf-8', dir='.',
                                         prefix='.questions-', delete=False)
                try:
                    with tmp:
                        json.dump(data[-MAX_ENTRIES:], tmp, ensure_ascii=False, indent=2)
                    os.replace(tmp.name, questions_file)
                finally:
                    if os.path.lexists(tmp.name):
                        os.unlink(tmp.name)
            except (OSError, ValueError):
                self.send_error(500, 'Cannot save questions')
                return

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())

    return PlanViewerHandler


def main():
    default_dir = os.environ.get('PLAN_VIEWER_DIR', os.path.expanduser('~/plan-viewer'))

    parser = argparse.ArgumentParser(description='View HTTP server')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--dir', default=default_dir)
    parser.add_argument('--pin', default=None, help='PIN code (default: random 4-digit)')
    parser.add_argument('--no-pin', action='store_true', help='Disable PIN authentication')
    args = parser.parse_args()

    if os.path.exists(args.dir) and not os.path.isdir(args.dir):
        print(f'Error: "{args.dir}" exists but is not a directory', file=sys.stderr)
        raise SystemExit(1)
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
