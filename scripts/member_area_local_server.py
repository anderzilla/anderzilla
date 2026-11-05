"""Loopback-only local verification server for Member Area & Single Wallet.

Serves static files from apps/web/out and routes /api/* to services.identity.clerk_api.dispatch_clerk
using a temporary SQLite database with synthetic test fixtures.
Strictly restricted to 127.0.0.1 and non-production environments.
"""
from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.identity.clerk_api import dispatch_clerk  # noqa: E402
from services.identity.clerk_auth import ClerkIdentity  # noqa: E402
from services.identity.clerk_service import ClerkAccountService, POLICY_VERSION  # noqa: E402
from services.identity.core import Rejected  # noqa: E402
from services.identity.storage import SQLiteStore  # noqa: E402


def cpf_for_test(number: int) -> str:
    value = f'{number:09}'
    for size in (9, 10):
        value += str((sum(int(value[i]) * (size + 1 - i) for i in range(size)) * 10 % 11) % 10)
    return value


class SyntheticLoopbackGateway:
    def __init__(self):
        now_ts = int(time.time())
        self.identities = {
            'token-player-a': ClerkIdentity('user_synth_a', 'sess_synth_a', 'player.a@example.invalid', now_ts),
            'token-player-b': ClerkIdentity('user_synth_b', 'sess_synth_b', 'player.b@example.invalid', now_ts),
            'token-incomplete': ClerkIdentity('user_synth_inc', 'sess_synth_inc', 'incomplete@example.invalid', now_ts),
        }

    def verify(self, auth_header: str | None) -> ClerkIdentity:
        if not auth_header or not auth_header.startswith('Bearer '):
            raise Rejected('authentication_required', 'Entre para continuar.', 401)
        token = auth_header[7:].strip()
        ident = self.identities.get(token)
        if not ident:
            raise Rejected('invalid_token', 'Sessão inválida ou expirada.', 401)
        return ident

    def delete_user(self, subject: str):
        for k, v in list(self.identities.items()):
            if v.subject == subject:
                self.identities.pop(k, None)

    def revoke_session(self, session_id: str):
        pass

    def ban_user(self, subject: str):
        pass


def seed_synthetic_store(store: SQLiteStore, gateway: SyntheticLoopbackGateway, cfg: dict):
    svc = ClerkAccountService(store, cfg)
    svc.onboard(
        gateway.identities['token-player-a'],
        {
            'cpf': cpf_for_test(123456789),
            'displayName': 'GhostRunner',
            'birthDate': '1995-04-12',
            'termsAccepted': True,
            'termsVersion': POLICY_VERSION,
            'privacyVersion': POLICY_VERSION,
            'marketingOptIn': False,
            'lang': 'pt-BR',
        },
    )
    svc.onboard(
        gateway.identities['token-player-b'],
        {
            'cpf': cpf_for_test(987654321),
            'displayName': 'CyberFox',
            'birthDate': '1997-08-20',
            'termsAccepted': True,
            'termsVersion': POLICY_VERSION,
            'privacyVersion': POLICY_VERSION,
            'marketingOptIn': False,
            'lang': 'pt-BR',
        },
    )

    now_ts = int(time.time())
    starts = now_ts - 86400
    ends = now_ts + 86400 * 30
    questions = [
        {
            'id': 'q1',
            'promptPT': 'Qual recurso exige validação do servidor para Karaca Points?',
            'promptEN': 'Which feature requires server validation for Karaca Points?',
            'options': [
                {'id': 'a', 'textPT': 'Missões oficiais na conta', 'textEN': 'Official account missions'},
                {'id': 'b', 'textPT': 'Favorito local sem login', 'textEN': 'Local bookmark without login'},
            ],
            'correctOption': 'a',
        }
    ]
    with store.transaction() as db:
        db.execute(
            'INSERT OR REPLACE INTO mission_campaigns(id,total_budget_kp,reserved_kp,consumed_kp,per_account_limit_kp,starts_at,ends_at,state) '
            'VALUES(?,?,0,0,?,?,?,?)',
            ('camp-synth-2026', 500, 500, starts, ends, 'active'),
        )
        db.execute(
            'INSERT OR REPLACE INTO missions(id,version,award,starts_at,ends_at,active,verifier,definition_json,coverage_reference) '
            'VALUES(?,?,?,?,?,1,?,?,?)',
            (
                'checkpoint-curiosidade',
                1,
                25,
                starts,
                ends,
                'quiz',
                json.dumps({
                    'titlePT': 'Checkpoint da Curiosidade',
                    'titleEN': 'Curiosity Checkpoint',
                    'summaryPT': 'Responda ao checkpoint oficial validado pelo servidor.',
                    'summaryEN': 'Answer the official server-validated checkpoint.',
                    'questions': questions,
                }),
                'camp-synth-2026',
            ),
        )
        db.execute(
            'INSERT OR REPLACE INTO missions(id,version,award,starts_at,ends_at,active,verifier,definition_json,coverage_reference) '
            'VALUES(?,?,?,?,?,1,?,?,?)',
            (
                'monte-seu-radar',
                1,
                15,
                starts,
                ends,
                'interests',
                json.dumps({
                    'titlePT': 'Monte seu Radar',
                    'titleEN': 'Build your Radar',
                    'summaryPT': 'Escolha ao menos três interesses editoriais na sua conta.',
                    'summaryEN': 'Choose at least three editorial interests in your account.',
                    'minimumInterests': 3,
                }),
                'camp-synth-2026',
            ),
        )


def main():
    if os.getenv('IDENTITY_ENV', 'development').lower() == 'production':
        raise SystemExit('Refusing to start synthetic local server in production.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=4173)
    parser.add_argument(
        '--static-dir',
        type=str,
        default=str(ROOT / 'apps' / 'web' / 'out'),
    )
    args = parser.parse_args()

    tmp_dir = tempfile.mkdtemp(prefix='anderzilla-member-local-')
    store = SQLiteStore(Path(tmp_dir) / 'member.sqlite')
    gateway = SyntheticLoopbackGateway()
    cfg = {
        'ok': True,
        'origins': {
            f'http://127.0.0.1:{args.port}',
            f'http://localhost:{args.port}',
        },
        'cpfKey': 'synthetic-local-key-' * 4,
        'programState': 'active',
        'rewards': True,
    }
    seed_synthetic_store(store, gateway, cfg)
    static_root = Path(args.static_dir).resolve()

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *h_args, **h_kwargs):
            super().__init__(*h_args, directory=str(static_root), **h_kwargs)

        def log_message(self, fmt, *log_args):
            pass

        def _handle_api(self, method: str):
            length = int(self.headers.get('Content-Length') or '0')
            raw = self.rfile.read(length) if length > 0 else b''
            body = json.loads(raw.decode('utf-8')) if raw else {}
            headers = {k: v for k, v in self.headers.items()}
            if 'Origin' not in headers and 'origin' not in headers:
                headers['Origin'] = f'http://127.0.0.1:{args.port}'
            res = dispatch_clerk(
                store,
                method,
                self.path,
                headers=headers,
                body=body,
                gateway=gateway,
                cfg=cfg,
            )
            status = res['status']
            payload = (
                b''
                if status == 204 or res['body'] is None
                else json.dumps(res['body']).encode('utf-8')
            )
            self.send_response(status)
            for hk, hv in res['headers'].items():
                self.send_header(hk, hv)
            if status != 204:
                self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            if payload:
                self.wfile.write(payload)

        def do_OPTIONS(self):
            if self.path.startswith('/api/'):
                self._handle_api('OPTIONS')
            else:
                self.send_response(204)
                self.end_headers()

        def do_GET(self):
            if self.path.startswith('/api/'):
                self._handle_api('GET')
            else:
                super().do_GET()

        def do_POST(self):
            if self.path.startswith('/api/'):
                self._handle_api('POST')
            else:
                self.send_error(405)

        def do_PUT(self):
            if self.path.startswith('/api/'):
                self._handle_api('PUT')
            else:
                self.send_error(405)

        def do_PATCH(self):
            if self.path.startswith('/api/'):
                self._handle_api('PATCH')
            else:
                self.send_error(405)

        def do_DELETE(self):
            if self.path.startswith('/api/'):
                self._handle_api('DELETE')
            else:
                self.send_error(405)

    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Member Area local verification server listening on http://127.0.0.1:{args.port}', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
