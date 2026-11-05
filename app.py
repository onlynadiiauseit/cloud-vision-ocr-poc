"""Local PoC server. Run: python app.py; open http://127.0.0.1:8000."""
import argparse
import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from vision_client import recognize, extract_text, VisionError, MAX_IMAGE_BYTES

ROOT = Path(__file__).resolve().parent
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Do not log image content or secrets.

    def send(self, status, body, content_type='application/json; charset=utf-8'):
        data = json.dumps(body, ensure_ascii=False).encode() if isinstance(body, dict) else body
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        route = urlsplit(self.path).path
        if route == '/api/status':
            return self.send(200, {'key_configured': bool(os.environ.get('GOOGLE_VISION_API_KEY', '').strip())})
        files = {'/': ('static/index.html', 'text/html; charset=utf-8'),
                 '/app.js': ('static/app.js', 'text/javascript; charset=utf-8'),
                 '/style.css': ('static/style.css', 'text/css; charset=utf-8'),
                 '/sample.png': ('samples/sample.png', 'image/png')}
        if route not in files:
            return self.send(404, {'error': 'Не знайдено.'})
        path, mime = files[route]
        self.send(200, (ROOT/path).read_bytes(), mime)

    def do_POST(self):
        # Custom header and no CORS prevent ordinary cross-origin browser calls.
        if self.headers.get('X-OCR-Client') != 'local-poc':
            return self.send(403, {'error': 'Запит дозволено лише з інтерфейсу застосунку.'})
        route = urlsplit(self.path)
        if route.path == '/api/demo':
            fixture = json.loads((ROOT/'samples/demo_response.json').read_text(encoding='utf-8'))
            return self.send(200, {'text': extract_text(fixture), 'mode': 'demo',
                'elapsed_ms': None, 'feature': 'TEXT_DETECTION',
                'notice': 'Імітація відповіді для sample.png. Запит до Google не виконувався.'})
        if route.path != '/api/ocr':
            return self.send(404, {'error': 'Не знайдено.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length <= 0 or length > MAX_IMAGE_BYTES:
                return self.send(413, {'error': 'Потрібен PNG/JPEG до 4 MiB.'})
            self.connection.settimeout(35)
            image = self.rfile.read(length)
            if len(image) != length:
                raise ValueError('Файл завантажено не повністю.')
            feature = parse_qs(route.query).get('feature', ['TEXT_DETECTION'])[0]
            result = recognize(image, feature)
            return self.send(200, result)
        except (ValueError, TimeoutError) as exc:
            return self.send(400, {'error': str(exc)})
        except VisionError as exc:
            return self.send(502, {'error': str(exc)})

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Cloud OCR: http://127.0.0.1:{args.port} (Ctrl+C для зупинки)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
