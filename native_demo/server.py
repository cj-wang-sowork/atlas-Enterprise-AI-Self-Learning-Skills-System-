"""Strict loopback-only HTTP service. No request bodies or model text in logs."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import secrets
import threading

from .service import DemoService
from .runner import GenerationError


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, service):
        self.service = service
        self.csrf_token = secrets.token_urlsafe(32)
        self.job_lock = threading.BoundedSemaphore(1)
        self.connection_slots = threading.BoundedSemaphore(12)
        super().__init__(address, Handler)

    def process_request(self, request, client_address):
        if not self.connection_slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.connection_slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.connection_slots.release()

    def handle_error(self, request, client_address):
        # Never log a traceback that might contain task data or provider errors.
        pass


class Handler(BaseHTTPRequestHandler):
    server: DemoServer

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, format, *args):
        pass

    def send_data(self, status, body, content_type='application/json; charset=utf-8'):
        if isinstance(body, dict):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def local_request(self):
        port = self.server.server_address[1]
        allowed = {'127.0.0.1:' + str(port), 'localhost:' + str(port)}
        hosts = self.headers.get_all('Host', [])
        if (len(hosts) != 1 or hosts[0] not in allowed or
                self.headers.get('Sec-Fetch-Site') == 'cross-site'):
            self.send_data(403, {'error': 'LOCALHOST_REQUIRED'})
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return
        if self.path == '/health':
            self.send_data(200, {'ok': True, 'mode': 'personal-localhost-only'})
        elif self.path in ('/', '/app.css', '/app.js'):
            names = {'/': ('index.html', 'text/html; charset=utf-8'),
                     '/app.css': ('app.css', 'text/css; charset=utf-8'),
                     '/app.js': ('app.js', 'text/javascript; charset=utf-8')}
            name, content_type = names[self.path]
            data = (Path(__file__).resolve().parent / name).read_bytes()
            if self.path == '/':
                data = data.replace(b'__ATLAS_CSRF__', self.server.csrf_token.encode('ascii'))
            self.send_data(200, data, content_type)
        else:
            self.send_data(404, {'error': 'NOT_FOUND'})

    def do_POST(self):
        if not self.local_request():
            return
        if self.path != '/api/run':
            self.send_data(404, {'error': 'NOT_FOUND'})
            return
        origin = 'http://' + self.headers['Host']
        if (self.headers.get_all('Origin', []) != [origin] or
                self.headers.get_all('X-Atlas-CSRF', []) != [self.server.csrf_token]):
            self.send_data(403, {'error': 'CSRF_REJECTED'})
            return
        if self.headers.get('Content-Type', '').lower() not in ('application/json', 'application/json; charset=utf-8'):
            self.send_data(415, {'error': 'JSON_REQUIRED'})
            return
        try:
            lengths = self.headers.get_all('Content-Length', [])
            if len(lengths) != 1 or self.headers.get('Transfer-Encoding'):
                raise ValueError()
            length = int(lengths[0])
            if length > 16384:
                self.send_data(413, {'error': 'REQUEST_TOO_LARGE'})
                return
            if length <= 0:
                raise ValueError()
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError()
            payload = json.loads(raw.decode('utf-8'))
            if (not isinstance(payload, dict) or set(payload) - {'task', 'context'} or
                    not isinstance(payload.get('task'), str) or not payload['task'].strip() or
                    not isinstance(payload.get('context', ''), str)):
                raise ValueError()
        except (ValueError, UnicodeError, RecursionError, OSError):
            self.send_data(400, {'error': 'INVALID_REQUEST'})
            return
        if not self.server.job_lock.acquire(blocking=False):
            self.send_data(429, {'error': 'BUSY'})
            return
        try:
            result = self.server.service.run(payload['task'], payload.get('context', ''))
            self.send_data(200, result)
        except GenerationError as error:
            self.send_data(504 if error.code == 'MODEL_TIMEOUT' else 502, {'error': error.code})
        except Exception:
            self.send_data(500, {'error': 'GENERATION_FAILED'})
        finally:
            self.server.job_lock.release()


def make_server(host='127.0.0.1', port=8765, service=None):
    if host != '127.0.0.1':
        raise ValueError('Only 127.0.0.1 binding is allowed; never expose personal OAuth publicly')
    return DemoServer((host, port), service or DemoService())
