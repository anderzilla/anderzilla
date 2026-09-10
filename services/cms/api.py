"""Shared HTTP routing; never accept identity/roles from request bodies."""
import base64
import json
import re
from core import Error, require


def swa_principal(encoded):
    try:
        principal = json.loads(base64.b64decode(encoded or '', validate=True))
        roles = principal.get('userRoles', [])
        if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
            return None
        if not principal.get('userId') or 'authenticated' not in roles:
            return None
        return {'id': principal['userId'], 'name': principal.get('userDetails', ''), 'roles': roles}
    except (ValueError, TypeError, KeyError):
        return None


def dispatch(cms, principal, method, path, body=None, environment='homolog', mode='azure-sql'):
    require(principal)
    body = body or {}
    if not isinstance(body, dict):
        raise Error(422, 'invalid_body', 'Objeto JSON obrigatório.')
    path = path.rstrip('/')
    if method == 'GET' and path == '/api/session':
        return {'user': {'name': principal['name'], 'roles': principal['roles']}, 'environment': environment, 'mode': mode}
    if method == 'GET' and path == '/api/admin/summary':
        return cms.summary(principal)
    if method == 'GET' and path == '/api/admin/health':
        require(principal, publish=True)
        if not hasattr(cms.store, 'health'):
            return {'healthy': True, 'stage': 'local', 'category': 'local_store', 'exceptionType': None}
        return cms.store.health()
    if method == 'POST' and path == '/api/admin/media-upload':
        return cms.upload_media(principal, body)
    match = re.fullmatch(r'/api/admin/records/([a-z]+)(?:/([a-zA-Z0-9-]+))?(?:/(transition|revisions))?', path)
    if match:
        collection, record_id, suffix = match.groups()
        if method == 'GET' and suffix == 'revisions' and record_id:
            return cms.revisions(principal, collection, record_id)
        if method == 'GET' and not record_id:
            return cms.list(principal, collection)
        if method == 'POST' and not record_id:
            return cms.save(principal, collection, body.get('data'))
        if method == 'PUT' and record_id and not suffix:
            return cms.save(principal, collection, body.get('data'), record_id, body.get('version'))
        if method == 'POST' and suffix == 'transition':
            return cms.save(principal, collection, None, record_id, body.get('version'), body.get('action'))
    if path == '/api/admin/releases':
        if method == 'POST':
            return cms.release(principal, body.get('idempotencyKey'))
        if method == 'GET':
            return cms.releases(principal)
    match = re.fullmatch(r'/api/admin/releases/([a-zA-Z0-9-]+)(?:/(snapshot|status))?', path)
    if match:
        release_id, suffix = match.groups()
        if method == 'GET':
            return cms.releases(principal, release_id, suffix == 'snapshot')
    raise Error(404, 'not_found', 'Rota não encontrada.')
