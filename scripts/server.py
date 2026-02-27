#!/usr/bin/env python3
"""plan-viewer HTTP server with cache-control headers and annotation POST."""
import argparse
import json
import os
from http.server import SimpleHTTPRequestHandler, HTTPServer


class PlanViewerHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_POST(self):
        if self.path != '/api/questions':
            self.send_error(404)
            return

        content_length = int(self.headers.get('Content-Length', 0))
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

        with open(questions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode())


def main():
    default_dir = os.environ.get('PLAN_VIEWER_DIR', os.path.expanduser('~/plan-viewer'))

    parser = argparse.ArgumentParser(description='plan-viewer HTTP server')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--dir', default=default_dir)
    args = parser.parse_args()

    os.chdir(args.dir)
    print(f'Serving {args.dir} on port {args.port}')

    HTTPServer(('', args.port), PlanViewerHandler).serve_forever()


if __name__ == '__main__':
    main()
