"""Smoke test of the deployed HOMOLOG content API with a throwaway 1-day key that never leaves this process.

It creates test drafts (marked as tests) and one pending package in the homolog sandbox database: the runtime credential
cannot delete, so they stay there. It refuses to run against anything but anderzilla-cms-homolog. The key is revoked at
the end even when a check fails. Nothing is approved and no release is created."""
import base64
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).parent
sys.path[:0] = [str(HERE.parent / 'cms'), str(HERE)]
from agent_api import AgentGateway
from core import CMS

BASE = os.environ.get('CONTENT_API_BASE', 'https://anderzilla-content-api-homolog.azurewebsites.net')
OPERATOR = {'id': 'operator:smoke-test', 'name': 'Smoke test issuer', 'roles': ['anderzilla_admin']}


def png(color, size=(640, 360)):
    from PIL import Image
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, 'PNG')
    return base64.b64encode(buffer.getvalue()).decode()


class Smoke:
    def __init__(self, gateway, base=BASE, out=print):
        self.gateway, self.base, self.out, self.results, self.key = gateway, base, out, [], None

    def call(self, method, path, body=None, idem=None, headers=None, raw=None, key=True):
        h = {'Content-Type': 'application/json', **(headers or {})}
        if key and self.key:
            h['Authorization'] = 'Bearer ' + self.key
        if idem:
            h['Idempotency-Key'] = idem
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        started = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(self.base + path, data=data, headers=h, method=method), timeout=150) as r:
                return r.status, json.loads(r.read() or b'{}'), time.time() - started
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b'{}'), time.time() - started

    def check(self, name, ok, detail=''):
        self.results.append(bool(ok))
        self.out(('PASS ' if ok else 'FAIL ') + name + (' | ' + detail if detail else ''))

    def run(self):
        with self.gateway.store.transaction() as db:
            releases_before = len(db.releases())
        issued = self.gateway.create_key(OPERATOR, 'smoke-' + uuid.uuid4().hex[:8], 1)
        self.key, key_id = issued['key'], issued['id']
        run = uuid.uuid4().hex[:8]
        self.out(f'throwaway key {key_id} created (not displayed), valid 1 day')
        try:
            self.scenario(run)
            with self.gateway.store.transaction() as db:
                releases_after = len(db.releases())
            self.check('no release was created', releases_after == releases_before, f'{releases_before} -> {releases_after}')
        finally:
            self.gateway.revoke_key(OPERATOR, key_id)
            status, _, _ = self.call('GET', '/v1/schema')
            self.check('revoked key is refused', status == 401, str(status))
            self.key = None
        self.out(f'\n{sum(self.results)}/{len(self.results)} checks passed')
        return all(self.results)

    def scenario(self, run):
        c = self.check
        s, p, t = self.call('GET', '/v1/health', key=False)
        c('health', s == 200 and p.get('status') == 'ok', f'{s} in {t:.1f}s')
        s, p, t = self.call('GET', '/v1/schema')
        c('schema with key', s == 200 and 'content' in p.get('collections', {}), f'{s} in {t:.1f}s')
        s, p, _ = self.call('GET', '/v1/schema', key=False)
        c('no key is refused', s == 401)
        article = {'titlePT': f'[TESTE {run}] Notícia de teste', 'titleEN': f'[TEST {run}] Test article', 'summaryPT': 'Resumo de teste.', 'summaryEN': 'Test summary.',
                   'bodyPT': 'Corpo **de teste**.', 'bodyEN': 'Body of the **test**.', 'category': 'ia', 'sourceName': 'Exemplo', 'sourceUrl': 'https://example.com/smoke',
                   'publishedAt': '2026-10-29', 'slugPT': f'teste-{run}', 'slugEN': f'test-{run}', 'isDemo': True}
        s, p, _ = self.call('POST', '/v1/articles:validate', article)
        c('validate accepts a good article', s == 200 and p.get('valid') is True)
        s, p, _ = self.call('POST', '/v1/articles:validate', {**article, 'sourceUrl': 'http://inseguro.example.com'})
        c('validate catches an http source', s == 200 and p.get('valid') is False and p['errors'][0]['field'] == 'sourceUrl')
        media_body = {'contentBase64': png((17, 27, 45)), 'filename': 'smoke.png', 'altPT': 'Imagem de teste', 'altEN': 'Test image', 'credit': 'Gerada para teste',
                      'license': 'Uso interno de teste', 'sourceUrl': 'https://example.com/smoke-foto'}
        s, media, t = self.call('POST', '/v1/media', media_body, idem=f'smoke-media-{run}')
        c('upload image (base64)', s == 201 and media['data']['mimeType'] == 'image/webp' and media['status'] == 'draft', f'{s} in {t:.1f}s')
        s, again, _ = self.call('POST', '/v1/media', media_body, idem=f'smoke-media-{run}')
        c('idempotent replay returns the same record', s == 201 and again['id'] == media['id'])
        s, p, _ = self.call('POST', '/v1/media', {**media_body, 'altPT': 'outro'}, idem=f'smoke-media-{run}')
        c('same Idempotency-Key with another body is refused', s == 409)
        s, p, _ = self.call('POST', '/v1/media', {'sourceImageUrl': 'https://example.com/x.png', **{k: media_body[k] for k in ('altPT', 'altEN', 'credit', 'license', 'sourceUrl')}}, idem=f'smoke-url-{run}')
        c('image by URL is refused while the host allow-list is empty', s == 422 and p['error']['code'] == 'host_not_allowed', p.get('error', {}).get('code', ''))
        s, art, _ = self.call('POST', '/v1/articles', {'key': f'smoke-artigo-{run}', 'data': {**article, 'coverMediaId': media['id']}}, idem=f'smoke-art-{run}')
        c('create draft article', s == 201 and art['status'] == 'draft')
        s, p, _ = self.call('POST', '/v1/articles', {'key': f'smoke-b-{run}', 'data': {**article, 'status': 'approved'}}, idem=f'smoke-b-{run}')
        c('agent cannot smuggle status=approved', s == 422)
        s, p, _ = self.call('POST', '/v1/articles', {'key': f'smoke-c-{run}', 'data': {**article, 'assetBase64': 'AAAA'}}, idem=f'smoke-c-{run}')
        c('agent cannot write protected asset fields', s == 422)
        banner = {'key': f'smoke-banner-{run}', 'imageMediaId': media['id'], 'titlePT': '[TESTE] Banner', 'titleEN': '[TEST] Banner', 'linkPT': '/pt/produtos/', 'linkEN': '/en/produtos/',
                  'startsAt': '2026-11-01T00:00:00+00:00', 'isDemo': True}
        s, ban, _ = self.call('POST', '/v1/banners', banner, idem=f'smoke-ban-{run}')
        c('create draft banner', s == 201 and ban['status'] == 'draft')
        s, p, _ = self.call('POST', '/v1/banners', {**banner, 'key': f'smoke-ban2-{run}', 'linkPT': 'javascript:alert(1)'}, idem=f'smoke-ban2-{run}')
        c('banner with a javascript: link is refused', s == 422)
        records = [{'collection': k, 'id': r['id'], 'version': r['version']} for k, r in (('media', media), ('content', art), ('banners', ban))]
        s, sub, _ = self.call('POST', '/v1/submissions', {'note': f'Smoke test {run}', 'records': records}, idem=f'smoke-sub-{run}')
        c('submit a package for review', s == 201 and sub['status'] == 'pending' and '/submissions/' in sub['reviewUrl'])
        s, got, _ = self.call('GET', f"/v1/submissions/{sub['id']}")
        c('agent reads its package status', s == 200 and got['status'] == 'pending')
        forged = base64.b64encode(json.dumps({'userId': 'x', 'userDetails': 'a', 'userRoles': ['authenticated', 'anderzilla_admin']}).encode()).decode()
        for label, method, path, headers in (('approve', 'POST', f"/v1/submissions/{sub['id']}/approve", None), ('list every package', 'GET', '/v1/submissions', None),
                                             ('promote', 'POST', '/v1/releases/x/promote', None), ('approve with a forged admin principal', 'POST', f"/v1/submissions/{sub['id']}/approve", {'x-ms-client-principal': forged})):
            s, p, _ = self.call(method, path, {} if method == 'POST' else None, headers=headers)
            c(f'agent cannot {label}', s in (401, 403), str(s))
        s, p, _ = self.call('POST', '/v1/articles', raw=b'x' * 400000, idem=f'smoke-big-{run}')
        c('oversized JSON is refused', s == 413, str(s))
        with self.gateway.store.transaction() as db:
            ids = {x['id'] for x in records}
            states = {k: sorted({r['status'] for r in db.records(k) if r['id'] in ids}) for k in ('media', 'content', 'banners')}
        c('all records are still drafts in the database', all(v == ['draft'] for v in states.values()), json.dumps(states))


def main():
    if os.environ.get('CMS_SQL_DATABASE') != 'anderzilla-cms-homolog':
        raise SystemExit('Refusing to run: CMS_SQL_DATABASE must be anderzilla-cms-homolog (this smoke test writes test drafts).')
    from storage import AzureSQLStore
    ok = Smoke(AgentGateway(CMS(AzureSQLStore()), media_hosts=[])).run()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
