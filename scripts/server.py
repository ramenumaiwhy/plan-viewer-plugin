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
from datetime import datetime, timezone
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


QUESTIONS_FILE = 'questions.json'
VIEWS_FILE = 'views.json'


def _nofollow():
    return getattr(os, 'O_NOFOLLOW', None)


def _in_tailnet(ip):
    return ip in TAILSCALE_IPV4 or ip in TAILSCALE_IPV6


def _now():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def _parse_time(value):
    """changed_at を比べられる時刻にする。無いものは一番古い扱い。"""
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.astimezone()


def _read_json_file(name, default):
    """作業ディレクトリの JSON を読む。シンボリックリンクは開かない。"""
    try:
        fd = os.open(name, os.O_RDONLY | (_nofollow() or 0))
    except FileNotFoundError:
        return default
    with os.fdopen(fd, encoding='utf-8') as f:
        return json.load(f)


def _write_json_file(name, data):
    """一時ファイルに書いてから入れ替える。書き込み中に読まれても壊れない。"""
    tmp = NamedTemporaryFile(mode='w', encoding='utf-8', dir='.', prefix=f'.{name}-', delete=False)
    try:
        with tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
        os.replace(tmp.name, name)
    finally:
        if os.path.lexists(tmp.name):
            os.unlink(tmp.name)


def _load_views():
    data = _read_json_file(VIEWS_FILE, {'revision': 0, 'views': []})
    if not isinstance(data, dict) or not isinstance(data.get('views'), list) or not isinstance(data.get('revision'), int):
        raise ValueError('invalid views file')
    return data


def _save_views(data):
    if _nofollow() is None:
        raise OSError('views require os.O_NOFOLLOW')
    _write_json_file(VIEWS_FILE, data)


def _find_view(data, page):
    return next((view for view in data['views'] if view.get('page') == page), None)


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
                for private in (QUESTIONS_FILE, VIEWS_FILE):
                    if filename == private or filename.startswith(private + '.') or filename == private + '~':
                        return True
            return bool(parts and parts[0].lower() in {'scripts', '__pycache__'})

        def _client_and_host(self):
            try:
                client_ip = ipaddress.ip_address(self.client_address[0])
                hostname = urlsplit(f"//{self.headers.get('Host', '')}").hostname
            except ValueError:
                return None, None
            return client_ip, hostname

        def _is_mac_itself(self):
            """Mac 自身から localhost 宛てに直接来た要求だけを許可する。"""
            client_ip, hostname = self._client_and_host()
            if client_ip is None or not client_ip.is_loopback:
                return False
            if hostname not in {'localhost', '127.0.0.1', '::1'}:
                return False
            forwarded_headers = ('Forwarded', 'X-Forwarded-For', 'X-Forwarded-Host', 'X-Real-IP')
            return not any(self.headers.get(header) for header in forwarded_headers)

        def _is_tailnet_direct(self):
            """Tailscale のアドレスから、Tailscale の IP か ts.net 名で直接開かれた要求を許可する。"""
            client_ip, hostname = self._client_and_host()
            if client_ip is None or not _in_tailnet(client_ip) or not hostname:
                return False
            if hostname.endswith('.ts.net'):
                return True
            try:
                return _in_tailnet(ipaddress.ip_address(hostname))
            except ValueError:
                return False  # 別名の Host は DNS rebinding の恐れがあるので拒否する

        def _can_write(self):
            """書き込みを許す相手: Mac 自身、Tailscale のアドレス、認証済み Tailscale Serve。"""
            return self._is_mac_itself() or self._is_tailnet_direct() or self._is_tailscale_serve()

        def _is_tailscale_serve(self):
            """認証済み Tailscale Serve 経由（Mac 自身へのプロキシ）を許可する。"""
            client_ip, hostname = self._client_and_host()
            if client_ip is None or not client_ip.is_loopback:
                return False
            if hostname in {'localhost', '127.0.0.1', '::1'}:
                return False

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
            return _in_tailnet(forwarded_ip)

        def do_GET(self):
            if not self._check_auth():
                self._serve_pin_page()
                return
            if urlsplit(self.path).path == '/api/views':
                try:
                    self._send_json(200, _load_views())
                except (OSError, ValueError):
                    self.send_error(500, 'Cannot read views')
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
            path = urlsplit(self.path).path
            if path == '/api/questions':
                handle, allowed = self._handle_questions, self._can_write()
            elif path == '/api/views':
                handle, allowed = self._handle_register_view, self._is_mac_itself()
            elif path.startswith('/api/views/'):
                page = unquote(path[len('/api/views/'):])
                handle, allowed = (lambda: self._handle_update_view(page)), self._can_write()
            else:
                self.send_error(404)
                return
            if not allowed:
                self.send_error(403)
                return
            handle()

        def _send_json(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json_object(self):
            """JSON の本文を dict で返す。だめなら応答を送って None を返す。"""
            if 'application/json' not in self.headers.get('Content-Type', ''):
                self.send_error(415)
                return None
            try:
                content_length = int(self.headers.get('Content-Length', 0))
            except ValueError:
                self.send_error(400)
                return None
            if content_length <= 0 or content_length > MAX_BODY:
                self.send_error(413)
                return None
            try:
                payload = json.loads(self.rfile.read(content_length))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self.send_error(400)
                return None
            if not isinstance(payload, dict):
                self.send_error(400)
                return None
            return payload

        def _handle_register_view(self):
            """公開スクリプトからの記事登録。同じ page なら中身を更新し、印は残す。"""
            payload = self._read_json_object()
            if payload is None:
                return
            fields = {k: payload.get(k) for k in ('page', 'title', 'project', 'icon', 'updated_at')}
            if not all(isinstance(fields[k], str) and fields[k].strip() for k in ('page', 'title', 'project')):
                self.send_error(400, 'page, title, project are required')
                return
            if any(v is not None and not isinstance(v, str) for v in fields.values()):
                self.send_error(400)
                return
            now = _now()
            try:
                data = _load_views()
                view = _find_view(data, fields['page'])
                created = view is None
                if created:
                    view = {'page': fields['page'], 'pinned': False, 'archived': False}
                    data['views'].append(view)
                view.update({
                    'title': fields['title'].strip(),
                    'project': fields['project'].strip(),
                    'icon': fields['icon'] or view.get('icon') or 'file-text',
                    'updated_at': fields['updated_at'] or now,
                    'changed_at': now,
                })
                data['revision'] += 1
                _save_views(data)
            except (OSError, ValueError):
                self.send_error(500, 'Cannot save views')
                return
            self._send_json(201 if created else 200, {'revision': data['revision'], 'view': view})

        def _handle_update_view(self, page):
            """ピン留め・アーカイブ・プロジェクト名の変更。Mac 側が新しければ 409 で今の値を返す。"""
            patch = self._read_json_object()
            if patch is None:
                return
            seen = patch.get('changed_at')
            changes = {k: patch[k] for k in ('pinned', 'archived', 'project') if k in patch}
            if (not changes
                    or any(not isinstance(changes[k], bool) for k in ('pinned', 'archived') if k in changes)
                    or ('project' in changes and not isinstance(changes['project'], str))
                    or (seen is not None and not isinstance(seen, str))
                    or (changes.get('pinned') and changes.get('archived'))):
                self.send_error(400)
                return
            try:
                seen_time = _parse_time(seen)
            except ValueError:
                self.send_error(400, 'changed_at must be ISO 8601')
                return
            try:
                data = _load_views()
                view = _find_view(data, page)
                if view is None:
                    self.send_error(404)
                    return
                if seen is not None and _parse_time(view.get('changed_at')) > seen_time:
                    self._send_json(409, {'revision': data['revision'], 'view': view})
                    return
                if 'project' in changes:
                    changes['project'] = changes['project'].strip()
                view.update(changes)
                if changes.get('pinned'):
                    view['archived'] = False
                if view.get('archived'):
                    view['pinned'] = False
                view['changed_at'] = _now()
                data['revision'] += 1
                _save_views(data)
            except (OSError, ValueError):
                self.send_error(500, 'Cannot save views')
                return
            self._send_json(200, {'revision': data['revision'], 'view': view})

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
            question = self._read_json_object()
            if question is None:
                return
            allowed_keys = {'page', 'selectedText', 'comment', 'timestamp'}
            question = {k: v for k, v in question.items() if k in allowed_keys and isinstance(v, str)}
            if not question.get('selectedText'):
                self.send_error(400)
                return
            if _nofollow() is None:
                self.send_error(501, 'Saving questions requires os.O_NOFOLLOW on the server')
                return
            try:
                data = _read_json_file(QUESTIONS_FILE, [])
                if not isinstance(data, list):
                    raise ValueError("invalid questions file")
                data.append(question)
                _write_json_file(QUESTIONS_FILE, data[-MAX_ENTRIES:])
            except (OSError, ValueError):
                self.send_error(500, 'Cannot save questions')
                return
            self._send_json(200, {'status': 'ok'})

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
