"""Loopback-only review server for local use: API on 8788, faithful preview on 8789, review UI from apps/review/out.
The bearer token must be generated outside source control. This is not the Azure deployment (see docs/ai-api)."""
import hmac
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cms'))
from agent_api import AgentGateway, handle
from core import CMS, Error
from storage import SQLiteStore
from preview_site import PreviewBuilder

API_PORT, PREVIEW_PORT = 8788, 8789
UI_DIR = Path(__file__).resolve().parents[2] / 'apps' / 'review' / 'out'


def make_servers(database, token, preview_dir, ui_dir=UI_DIR, builder=None):
    cms = CMS(SQLiteStore(database))
    previewer = builder or PreviewBuilder(preview_dir)
    gateway = AgentGateway(cms, previewer=previewer, review_base=f'http://127.0.0.1:{API_PORT}')
    human = {'id': 'local-operator', 'name': 'Operador local', 'roles': ['anderzilla_admin']}

    class Api(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass  # never log bearer tokens or content bodies

        def send(self, status, payload=None, content_type='application/json; charset=utf-8', raw=None):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('X-Robots-Tag', 'noindex, nofollow')
            self.end_headers()
            self.wfile.write(raw if raw is not None else json.dumps(payload, ensure_ascii=False).encode())

        def authorized(self):
            return hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + token)

        def route(self):
            parts = urlsplit(self.path)
            if self.headers.get('Host') not in {f'127.0.0.1:{API_PORT}', f'localhost:{API_PORT}'}:
                return self.send(403, {'error': {'code': 'invalid_host', 'message': 'Host não permitido.'}})
            if parts.path.startswith('/v1/'):
                try:
                    if not self.authorized():
                        raise Error(401, 'authentication_required', 'Token local obrigatório.')
                    length = int(self.headers.get('Content-Length', '0'))
                    if not 0 <= length <= 300000:
                        raise Error(413, 'too_large', 'Requisição muito grande.')
                    body = json.loads(self.rfile.read(length)) if length else {}
                    query = {key: values[-1] for key, values in parse_qs(parts.query).items()}
                    if self.command == 'POST' and parts.path.endswith('/open-preview'):  # activate a stored preview
                        sid = parts.path.split('/')[3]
                        gateway.get_submission(human, sid)
                        previewer.activate(sid)
                        return self.send(200, previewer.state(sid))
                    status, payload = handle(gateway, self.command, parts.path, body, None, human, self.headers.get('Idempotency-Key'), query)
                    return self.send(status, payload)
                except Error as error:
                    return self.send(error.status, {'error': {'code': error.code, 'message': str(error)}})
                except (ValueError, UnicodeDecodeError):
                    return self.send(400, {'error': {'code': 'invalid_json', 'message': 'JSON inválido.'}})
                except Exception:
                    return self.send(503, {'error': {'code': 'unavailable', 'message': 'Serviço indisponível.'}})
            # Review UI: static export, no secrets inside.
            relative = parts.path.lstrip('/') or 'index.html'
            target = (ui_dir / relative).resolve()
            if target.is_dir():
                target = target / 'index.html'
            if not str(target).startswith(str(Path(ui_dir).resolve())) or not target.is_file():
                return self.send(404, {'error': {'code': 'not_found', 'message': 'Não encontrado.'}})
            types = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.webp': 'image/webp', '.txt': 'text/plain'}
            return self.send(200, content_type=types.get(target.suffix, 'application/octet-stream'), raw=target.read_bytes())

        do_GET = do_POST = route

    class Preview(SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def translate_path(self, path):
            root = previewer.active_directory()
            missing = str(Path(preview_dir).resolve() / '.no-active-preview')
            if root is None:
                return missing
            base = root.resolve()
            target = (base / unquote(urlsplit(path).path).lstrip('/')).resolve()
            return str(target) if target == base or base in target.parents else missing

        def end_headers(self):
            self.send_header('X-Robots-Tag', 'noindex, nofollow')
            self.send_header('Cache-Control', 'no-store')
            super().end_headers()

    return ThreadingHTTPServer(('127.0.0.1', API_PORT), Api), ThreadingHTTPServer(('127.0.0.1', PREVIEW_PORT), Preview)


def main():
    token = os.environ.get('REVIEW_LOCAL_TOKEN', '')
    if len(token) < 32:
        raise SystemExit('Set REVIEW_LOCAL_TOKEN to a random token of at least 32 characters.')
    base = Path(os.environ.get('REVIEW_LOCAL_DIR', Path.home() / '.codex' / 'anderzilla-review'))
    api, preview = make_servers(base / 'cms.sqlite3', token, base / 'previews')
    import threading
    threading.Thread(target=preview.serve_forever, daemon=True).start()
    print(f'Review UI + API: http://127.0.0.1:{API_PORT}  |  preview: http://127.0.0.1:{PREVIEW_PORT}  |  bearer token required', flush=True)
    api.serve_forever()


if __name__ == '__main__':
    main()
