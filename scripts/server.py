#!/usr/bin/env python3
"""plan-viewer HTTP server with cache-control headers and annotation POST."""
import argparse
import json
import os
from http.server import SimpleHTTPRequestHandler, HTTPServer

MAX_BODY = 64 * 1024  # 64 KB
MAX_ENTRIES = 1000


class PlanViewerHandler(SimpleHTTPRequestHandler):
    # シンボリックリンク経由の docroot 外アクセスを防ぐ
    def translate_path(self, path):
        resolved = os.path.realpath(super().translate_path(path))
        docroot = os.path.realpath(os.getcwd())
        if not resolved.startswith(docroot + os.sep) and resolved != docroot:
            return docroot  # docroot 外へのアクセスは docroot 自体を返す
        return resolved

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_POST(self):
        if self.path != '/api/questions':
            self.send_error(404)
            return

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


def main():
    default_dir = os.environ.get('PLAN_VIEWER_DIR', os.path.expanduser('~/plan-viewer'))

    parser = argparse.ArgumentParser(description='plan-viewer HTTP server')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--dir', default=default_dir)
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        print(f'Error: "{args.dir}" is not a valid directory', file=__import__('sys').stderr)
        raise SystemExit(1)

    os.chdir(args.dir)
    print(f'Serving {args.dir} on {args.host}:{args.port}')

    HTTPServer((args.host, args.port), PlanViewerHandler).serve_forever()


if __name__ == '__main__':
    main()
