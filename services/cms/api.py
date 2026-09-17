"""Shared HTTP routing; never accept identity/roles from request bodies."""
import base64
import json
import os
import re
from core import Error, require
from urllib.parse import urlsplit, parse_qs
from automation import Automation


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
    body = body or {}
    if not isinstance(body, dict):
        raise Error(422, 'invalid_body', 'Objeto JSON obrigatório.')
    parsed = urlsplit(path)
    query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
    path = parsed.path.rstrip('/')
    # Worker machine routes — must be checked before generic require; require(worker) would otherwise 403 due to ROLES.
    if path.startswith('/api/worker/automation/'):
        # Never accept roles/actor from request body
        if any(key in body for key in ('actor', 'actorId', 'role', 'roles', 'principal', 'user', 'userId', 'serviceAccount')):
            raise Error(422, 'invalid_fields', 'Parâmetros desconhecidos.')
        # Also check nested input for actor fields? For lease body is empty; for complete strict.
        # Principal must be exact worker
        if not principal or not principal.get('id'):
            raise Error(401, 'authentication_required', 'Autenticação necessária.')
        roles = set(principal.get('roles', []))
        if roles != {'anderzilla_worker'}:
            raise Error(403, 'forbidden', 'Acesso de worker não autorizado.')
        external = os.environ.get('CMS_AUTOMATION_EXTERNAL_ENABLED', '').lower() == 'true'
        automation = Automation(cms.store, environment, external_enabled=external)
        endpoint = path.removeprefix('/api/worker/automation/')
        if method == 'POST' and endpoint == 'lease':
            if set(body) - set():
                # Lease should be empty body; strictly no fields
                raise Error(422, 'invalid_fields', 'Parâmetros desconhecidos.')
            return automation.lease(principal)
        if method == 'POST' and endpoint == 'complete':
            return automation.complete(principal, body)
        raise Error(404, 'not_found', 'Rota de automação não encontrada.')
    require(principal)
    # Human routes must not be accessed by worker role
    if 'anderzilla_worker' in set(principal.get('roles', [])):
        raise Error(403, 'forbidden', 'Conta não autorizada.')
    body = body or {}
    if path.startswith('/api/admin/automation/'):
        external = os.environ.get('CMS_AUTOMATION_EXTERNAL_ENABLED', '').lower() == 'true'
        automation = Automation(cms.store, environment, external_enabled=external)
        endpoint = path.removeprefix('/api/admin/automation/')
        if method == 'GET' and endpoint == 'processes':
            return automation.processes(principal)
        if method == 'GET' and endpoint == 'summary':
            return automation.summary(principal)
        if method == 'POST' and endpoint == 'runs/preview':
            return automation.preview(principal, body)
        if endpoint == 'runs':
            if method == 'POST':
                return automation.create(principal, body)
            if method == 'GET':
                return automation.list(principal, query)
        match = re.fullmatch(r'runs/([a-zA-Z0-9-]+)(?:/(cancel|retry|transition))?', endpoint)
        if match:
            run_id, command = match.groups()
            if method == 'GET' and not command:
                return automation.get(principal, run_id)
            if method == 'POST' and command:
                return automation.change(principal, run_id, command, body)
        raise Error(404, 'not_found', 'Rota de automação não encontrada.')
    if method == 'GET' and path == '/api/session':
        return {'user': {'name': principal['name'], 'roles': principal['roles']}, 'environment': environment, 'mode': mode}
    if method == 'GET' and path == '/api/admin/summary':
        return cms.summary(principal)
    if method == 'GET' and path == '/api/admin/reports/operations':
        from reporting import operations
        return operations(cms, principal, query, environment)
    if method == 'GET' and path == '/api/admin/health':
        require(principal, publish=True)
        if not hasattr(cms.store, 'health'):
            return {'healthy': True, 'stage': 'local', 'category': 'local_store', 'exceptionType': None}
        return cms.store.health()
    if method == 'POST' and path == '/api/admin/media-upload':
        return cms.upload_media(principal, body)
    match = re.fullmatch(r'/api/admin/records/([a-z_]+)(?:/([a-zA-Z0-9-]+))?(?:/(transition|revisions))?', path)
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
