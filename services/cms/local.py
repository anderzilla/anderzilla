"""Explicit loopback-only operator API. Token must be generated outside source control."""
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from api import dispatch
from core import CMS, Error
from storage import SQLiteStore


def main():
    token = os.environ.get('CMS_LOCAL_TOKEN', '')
    if len(token) < 32:
        raise SystemExit('Set CMS_LOCAL_TOKEN to a random token of at least 32 characters.')
    path = os.environ.get('CMS_LOCAL_DATABASE', str(Path.home() / '.codex' / 'anderzilla-cms' / 'local.sqlite3'))
    cms = CMS(SQLiteStore(path))

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass  # Never log bearer tokens or content bodies.

        def respond(self, status, payload=None):
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            if self.headers.get('Origin') == 'http://127.0.0.1:4181':
                self.send_header('Access-Control-Allow-Origin', 'http://127.0.0.1:4181')
                self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')
                self.send_header('Vary', 'Origin')
            self.end_headers()
            if payload is not None:
                self.wfile.write(json.dumps(payload, ensure_ascii=False).encode())

        def do_OPTIONS(self):
            self.respond(204 if self.headers.get('Origin') == 'http://127.0.0.1:4181' else 403)

        def handle_api(self):
            try:
                if self.headers.get('Host') not in {'127.0.0.1:8787', 'localhost:8787'}:
                    raise Error(403, 'invalid_host', 'Host não permitido.')
                if self.headers.get('Origin') not in {None, 'http://127.0.0.1:4181'}:
                    raise Error(403, 'invalid_origin', 'Origem não permitida.')
                if not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + token):
                    raise Error(401, 'authentication_required', 'Token local obrigatório.')
                length = int(self.headers.get('Content-Length', '0'))
                maximum = 2900000 if urlsplit(self.path).path == '/api/admin/media-upload' else 300000
                if not 0 <= length <= maximum:
                    raise Error(413, 'too_large', 'Requisição muito grande.')
                body = json.loads(self.rfile.read(length)) if length else {}
                principal = {'id': 'local-operator', 'name': 'Operador local', 'roles': ['anderzilla_admin']}
                self.respond(200, dispatch(cms, principal, self.command, urlsplit(self.path).path, body, 'local', 'sqlite-local'))
            except Error as error:
                self.respond(error.status, {'error': {'code': error.code, 'message': str(error)}})
            except (ValueError, UnicodeDecodeError):
                self.respond(400, {'error': {'code': 'invalid_json', 'message': 'JSON inválido.'}})
            except Exception:
                self.respond(503, {'error': {'code': 'unavailable', 'message': 'Serviço indisponível.'}})

        do_GET = do_POST = do_PUT = handle_api

    print('CMS local: http://127.0.0.1:8787; bearer token required; persistent SQLite.', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8787), Handler).serve_forever()


if __name__ == '__main__':
    main()
