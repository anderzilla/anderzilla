"""Phase 1 operator-controlled process records. No external dispatch or workers."""
import hashlib
import json
import os
import re
import uuid
from datetime import date, datetime, timezone, timedelta
from urllib.parse import urlparse
from core import Error, now, require

CATALOG = [
    ('editorial-package', 'Pacote editorial', 'Preparar e revisar pauta PT/EN.', 'anderzilla_editor'),
    ('offer-check', 'Verificação de ofertas', 'Revisar ofertas e disclosures por mercado.', 'anderzilla_commercial'),
    ('live-overlay', 'Preparação de live', 'Revisar canais, agenda e overlay.', 'anderzilla_editor'),
    ('media-cuts', 'Planejamento de cortes', 'Registrar revisão manual de mídia própria; não processa vídeo.', 'anderzilla_editor'),
    ('seo-audit', 'Auditoria SEO', 'Registrar verificações editoriais e técnicas.', 'anderzilla_editor'),
    ('report-weekly', 'Relatório semanal', 'Registrar análise manual do período solicitado.', 'anderzilla_commercial'),
    ('report-monthly', 'Relatório mensal', 'Registrar análise manual do período solicitado.', 'anderzilla_commercial'),
    ('report-custom', 'Relatório personalizado', 'Registrar análise manual de um intervalo.', 'anderzilla_commercial'),
]
PROCESSES = {identifier: {'id': identifier, 'version': 1, 'title': title, 'description': description,
    'role': role, 'status': 'manual_only', 'available': True, 'executorConnected': False,
    'executionMode': 'manual'} for identifier, title, description, role in CATALOG}

ALLOWED_HOSTS = {
    "anderzilla.com",
    "www.anderzilla.com",
    "salmon-stone-0a4d29c0f.5.azurestaticapps.net",
    "mango-coast-0322c590f.5.azurestaticapps.net",
    "salmon-stone-0a4d29c0f-visual.eastus2.5.azurestaticapps.net",
}

LEASE_TTL_SECONDS = 120
MAX_RESULT_SERIALIZED = 64 * 1024
MAX_LEASES_PER_RUN = 3
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

# Allowlisted stable error codes; unknown codes are mapped to worker_failed
ALLOWED_ERROR_CODES = {
    'fetch_timeout', 'target_unreachable', 'dns_error', 'tls_error',
    'render_error', 'parsing_error', 'rate_limited', 'worker_failed',
    'lease_exhausted', 'validation_error', 'internal_error',
}
ERROR_GENERIC_MESSAGES = {
    'fetch_timeout': 'Tempo de coleta excedido.',
    'target_unreachable': 'Destino não alcançável.',
    'dns_error': 'Falha de DNS.',
    'tls_error': 'Falha de TLS.',
    'render_error': 'Falha de renderização.',
    'parsing_error': 'Falha de análise.',
    'rate_limited': 'Limite excedido.',
    'worker_failed': 'Falha no processamento externo.',
    'lease_exhausted': 'Lease expirado sem conclusão.',
    'validation_error': 'Resultado inválido.',
    'internal_error': 'Erro interno do worker.',
}


def _canonical_dumps(obj):
    """Stable serialization for size/hash/replay: sort_keys, stable separators, ensure_ascii False."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def authorize(principal, process):
    require(principal)
    if not {'anderzilla_admin', process['role']}.intersection(principal.get('roles', [])):
        raise Error(403, 'forbidden', 'Processo não autorizado para esta conta.')


def _require_worker(principal):
    if not principal or not isinstance(principal, dict) or not principal.get('id'):
        raise Error(401, 'authentication_required', 'Entre com uma conta autorizada.')
    roles = set(principal.get('roles', []))
    if roles != {'anderzilla_worker'}:
        raise Error(403, 'forbidden', 'Acesso de worker não autorizado.')


def _validate_target_url(raw):
    if not isinstance(raw, str) or not raw:
        raise Error(422, 'invalid_targetUrl', 'Informe targetUrl HTTPS válido.')
    if len(raw) > 2048:
        raise Error(422, 'targetUrl_too_long', 'targetUrl muito longo.')
    try:
        p = urlparse(raw)
        if p.scheme != 'https':
            raise Error(422, 'targetUrl_scheme_must_be_https', 'targetUrl deve usar https.')
        if p.username or p.password:
            raise Error(422, 'targetUrl_userinfo_not_allowed', 'targetUrl não pode conter credenciais.')
        if p.fragment and "@" in p.fragment:
            raise Error(422, 'targetUrl_userinfo_not_allowed', 'targetUrl não pode conter credenciais.')
        host = (p.hostname or '').lower()
        if not host:
            raise Error(422, 'invalid_targetUrl', 'targetUrl inválido.')
        if host not in ALLOWED_HOSTS:
            raise Error(422, 'targetUrl_host_not_allowed', 'Host não permitido.')
        try:
            port = p.port
        except ValueError:
            raise Error(422, 'invalid_targetUrl', 'Porta inválida.')
        if port is not None and port != 443:
            raise Error(422, 'targetUrl_port_not_allowed', 'Porta não permitida.')
        # ensure no userinfo fragment bypass via urlparse quirks
        if "@" in raw.split("://", 1)[-1].split("/", 1)[0] and host not in raw.split("@")[-1].lower():
            # already checked username, but catch edge
            raise Error(422, 'targetUrl_userinfo_not_allowed', 'targetUrl não pode conter credenciais.')
        return raw
    except Error:
        raise
    except Exception:
        raise Error(422, 'invalid_targetUrl', 'targetUrl inválido.')


def key_hash(body):
    key = body.get('idempotencyKey')
    if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9._:-]{8,100}', key):
        raise Error(422, 'invalid_idempotency', 'Informe chave idempotente de 8 a 100 caracteres.')
    return key, hashlib.sha256(json.dumps({k: v for k, v in body.items() if k != 'idempotencyKey'}, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


class Automation:
    def __init__(self, store, environment='homolog', external_enabled=False):
        if environment not in {'local', 'homolog', 'production'}:
            raise Error(422, 'invalid_environment', 'Ambiente de automação inválido.')
        self.store, self.environment = store, environment
        # Allow env var string "true" to enable when not explicitly passed
        if isinstance(external_enabled, str):
            self.external_enabled = external_enabled.lower() == 'true'
        else:
            self.external_enabled = bool(external_enabled)
        # If not explicitly enabled, check env var as fallback for direct instantiation without param
        if not self.external_enabled:
            env_val = os.environ.get('CMS_AUTOMATION_EXTERNAL_ENABLED', '')
            if isinstance(env_val, str) and env_val.lower() == 'true':
                self.external_enabled = True

    def _is_external_process(self, process_id):
        return self.external_enabled and process_id == 'seo-audit'

    def processes(self, principal):
        require(principal)
        items = [dict(p) for p in PROCESSES.values() if {'anderzilla_admin', p['role']}.intersection(principal.get('roles', []))]
        for item in items:
            if self._is_external_process(item['id']):
                item['executorConnected'] = True
                item['executionMode'] = 'external'
                item['status'] = 'external'
            else:
                item['executorConnected'] = False
                item['executionMode'] = 'manual'
        return {'items': items, 'externalDispatchEnabled': bool(self.external_enabled)}

    def preview(self, principal, body):
        if set(body) - {'processId', 'processVersion', 'input', 'idempotencyKey'}:
            raise Error(422, 'invalid_fields', 'Parâmetros desconhecidos.')
        process = PROCESSES.get(body.get('processId'))
        if not process:
            raise Error(404, 'not_found', 'Processo não encontrado.')
        authorize(principal, process)
        if type(body.get('processVersion')) is not int or body['processVersion'] != process['version']:
            raise Error(409, 'process_version', 'Versão do processo alterada; atualize o catálogo.')
        data = body.get('input', {})
        # Determine allowed input keys
        base_allowed = {'market', 'language', 'notes', 'periodStart', 'periodEnd'}
        is_seo = process['id'] == 'seo-audit'
        allowed = set(base_allowed)
        if is_seo:
            allowed.add('targetUrl')
        if not isinstance(data, dict) or set(data) - allowed:
            raise Error(422, 'invalid_input', 'Entradas não permitidas.')
        if data.get('market') not in {'br', 'intl', 'global'} or data.get('language') not in {'pt-BR', 'en'}:
            raise Error(422, 'invalid_input', 'Escolha mercado e idioma válidos.')
        if 'notes' in data and (not isinstance(data['notes'], str) or len(data['notes']) > 2000):
            raise Error(422, 'invalid_input', 'Notas devem conter até 2000 caracteres.')
        if is_seo:
            is_external = self._is_external_process(process['id'])
            if is_external:
                if 'targetUrl' not in data:
                    raise Error(422, 'targetUrl_required', 'Informe targetUrl HTTPS válido.')
                _validate_target_url(data['targetUrl'])
            elif 'targetUrl' in data:
                _validate_target_url(data['targetUrl'])
        report = process['id'].startswith('report-')
        if report or data.get('periodStart') or data.get('periodEnd'):
            try:
                start, end = date.fromisoformat(data['periodStart']), date.fromisoformat(data['periodEnd'])
                if not 1 <= (end - start).days <= 366:
                    raise ValueError()
            except (KeyError, ValueError, TypeError):
                raise Error(422, 'invalid_period', 'Informe início e fim exclusivo YYYY-MM-DD, entre 1 e 366 dias.')
        is_external = self._is_external_process(process['id'])
        proc_copy = dict(process)
        if is_external:
            proc_copy['executorConnected'] = True
            proc_copy['executionMode'] = 'external'
            proc_copy['status'] = 'external'
        else:
            proc_copy['executorConnected'] = False
            proc_copy['executionMode'] = 'manual'
        warnings = ['Será despachado para worker externo privado; sem publicação automática.'] if is_external else ['Registro de trabalho manual. Nenhum worker, IA externa, coleta ou publicação será executado.']
        return {'process': proc_copy, 'input': dict(data), 'executionMode': 'external' if is_external else 'manual',
                'externalDispatchEnabled': bool(is_external), 'costEstimate': None,
                'warnings': warnings}

    def replay(self, db, actor, key, digest):
        row = db.execute('SELECT input_hash,document FROM automation_commands WHERE environment=? AND actor_id=? AND request_key=?', (self.environment, actor, key)).fetchone()
        if row:
            if row[0] != digest:
                raise Error(409, 'idempotency_conflict', 'Chave já utilizada com outro comando ou conteúdo.')
            return json.loads(row[1])

    def remember(self, db, principal, key, digest, result):
        db.execute('INSERT INTO automation_commands(environment,actor_id,request_key,input_hash,document) VALUES(?,?,?,?,?)', (self.environment, principal['id'], key, digest, json.dumps(result)))

    def persist(self, db, run, new=False):
        if new:
            db.execute('INSERT INTO automation_runs(id,environment,process_id,created_at,status,document) VALUES(?,?,?,?,?,?)', (run['id'], self.environment, run['processId'], run['createdAt'], run['status'], json.dumps(run)))
        else:
            db.execute('UPDATE automation_runs SET status=?,document=? WHERE environment=? AND id=?', (run['status'], json.dumps(run), self.environment, run['id']))

    def new_run(self, principal, process, inputs, parent=None):
        timestamp = now()
        # Determine executionMode for new run
        if parent:
            parent_external = parent.get('executionMode') == 'external'
            if parent_external and self.external_enabled:
                execution_mode = 'external'
            elif parent_external and not self.external_enabled:
                execution_mode = 'manual'
            else:
                execution_mode = 'manual'
        else:
            execution_mode = 'external' if self._is_external_process(process['id']) else 'manual'
        # Copy process with correct flags
        proc_copy = dict(process)
        if execution_mode == 'external':
            proc_copy['executorConnected'] = True
            proc_copy['executionMode'] = 'external'
            proc_copy['status'] = 'external'
        run = {'id': str(uuid.uuid4()), 'processId': process['id'], 'processVersion': process['version'],
                'process': proc_copy, 'input': dict(inputs), 'status': 'queued', 'version': 1,
                'environment': self.environment, 'requestedBy': principal['id'], 'createdAt': timestamp,
                'updatedAt': timestamp, 'parentRunId': parent['id'] if parent else None,
                'attempt': parent['attempt'] + 1 if parent else 1, 'executionMode': execution_mode,
                'externalDispatched': False, 'history': [{'status': 'queued', 'at': timestamp, 'actor': principal['id']}]}
        if execution_mode == 'external':
            run['fencingToken'] = 0
            run['deliveryCount'] = 0
        return run

    def create(self, principal, body):
        preview = self.preview(principal, body)
        key, digest = key_hash({**body, 'command': 'create'})
        with self.store.transaction() as db:
            replay = self.replay(db, principal['id'], key, digest)
            if replay:
                return replay
            process = preview['process']
            if not db.execute('SELECT id FROM automation_processes WHERE id=? AND version=?', (process['id'], process['version'])).fetchone():
                db.execute('INSERT INTO automation_processes(id,version,document) VALUES(?,?,?)', (process['id'], process['version'], json.dumps(process)))
            run = self.new_run(principal, process, preview['input'])
            self.persist(db, run, new=True)
            self.remember(db, principal, key, digest, run)
            audit_action = 'automation_queued_external' if run['executionMode'] == 'external' else 'automation_queued_manual'
            db.audit(principal['id'], audit_action, 'automation_runs', run['id'], 1)
            return run

    def load(self, db, principal, run_id):
        row = db.execute('SELECT document FROM automation_runs WHERE environment=? AND id=?', (self.environment, run_id)).fetchone()
        if not row:
            raise Error(404, 'not_found', 'Execução não encontrada.')
        run = json.loads(row[0])
        authorize(principal, run['process'])
        return run

    def load_worker(self, db, run_id):
        row = db.execute('SELECT document FROM automation_runs WHERE environment=? AND id=?', (self.environment, run_id)).fetchone()
        if not row:
            raise Error(404, 'not_found', 'Execução não encontrada.')
        return json.loads(row[0])

    def get(self, principal, run_id):
        require(principal)
        with self.store.transaction() as db:
            return self.load(db, principal, run_id)

    def change(self, principal, run_id, command, body):
        require(principal)
        # Block worker principal from human routes
        if 'anderzilla_worker' in set(principal.get('roles', [])):
            raise Error(403, 'forbidden', 'Acesso não autorizado.')
        if set(body) - {'idempotencyKey', 'version', 'reason', 'action', 'evidence'}:
            raise Error(422, 'invalid_fields', 'Parâmetros desconhecidos.')
        reason = body.get('reason')
        if not isinstance(reason, str) or not 3 <= len(reason.strip()) <= 1000:
            raise Error(422, 'reason_required', 'Informe motivo entre 3 e 1000 caracteres.')
        reason = reason.strip()
        key, digest = key_hash({**body, 'command': command, 'runId': run_id})
        with self.store.transaction() as db:
            run = self.load(db, principal, run_id)
            replay = self.replay(db, principal['id'], key, digest)
            if replay:
                return replay
            if type(body.get('version')) is not int or body['version'] != run['version']:
                raise Error(409, 'version_conflict', 'A execução mudou. Recarregue antes de continuar.')
            # Manual operations must not start/complete/fail external runs
            is_external = run.get('executionMode') == 'external'
            if command == 'retry':
                if run['status'] != 'failed' or run['attempt'] >= 3 or run.get('retryRunId'):
                    raise Error(409, 'retry_not_allowed', 'Reexecução permitida uma vez por falha, até 3 tentativas.')
                child = self.new_run(principal, run['process'], run['input'], parent=run)
                run.update(retryRunId=child['id'], version=run['version'] + 1, updatedAt=now())
                run['history'].append({'status': run['status'], 'action': 'retry_requested', 'at': run['updatedAt'], 'actor': principal['id'], 'reason': reason, 'childRunId': child['id']})
                child['history'][0].update(reason=reason, parentRunId=run['id'], action='retry_created')
                self.persist(db, run)
                self.persist(db, child, new=True)
                db.audit(principal['id'], 'automation_retry_created', 'automation_runs', child['id'], 1)
                result = child
            else:
                action = 'cancel' if command == 'cancel' else body.get('action')
                target = {'cancel': 'cancelled', 'start': 'running', 'complete': 'succeeded', 'fail': 'failed'}.get(action)
                allowed = {'queued': {'cancel', 'start'}, 'running': {'cancel', 'complete', 'fail'}}
                if not target or action not in allowed.get(run['status'], set()):
                    raise Error(409, 'invalid_transition', 'Transição não permitida no estado atual.')
                # Protect external runs from manual start/complete/fail
                if is_external:
                    if action in ('start', 'complete', 'fail'):
                        raise Error(409, 'invalid_transition', 'Transição manual não permitida para execução externa.')
                    # queued external may still be cancelled; running external cancel maybe not allowed? Allow only queued cancel
                    if action == 'cancel' and run['status'] != 'queued':
                        raise Error(409, 'invalid_transition', 'Transição não permitida no estado atual.')
                evidence = body.get('evidence', '')
                if action == 'complete' and (not isinstance(evidence, str) or not 3 <= len(evidence.strip()) <= 2000):
                    raise Error(422, 'evidence_required', 'Conclusão manual exige referência ou descrição do resultado.')
                evidence = evidence.strip() if isinstance(evidence, str) else evidence
                timestamp = now()
                run.update(status=target, version=run['version'] + 1, updatedAt=timestamp)
                event = {'status': target, 'at': timestamp, 'actor': principal['id'], 'reason': reason}
                if action == 'complete':
                    event.update(evidence=evidence, evidenceSource='operator_reported')
                run['history'].append(event)
                self.persist(db, run)
                result = run
            self.remember(db, principal, key, digest, result)
            db.audit(principal['id'], 'automation_' + command, 'automation_runs', run_id, run['version'])
            return result

    def list(self, principal, query=None):
        allowed = [item['id'] for item in self.processes(principal)['items']]
        query = query or {}
        try:
            offset, limit = int(query.get('cursor', 0)), int(query.get('limit', 50))
            if offset < 0 or not 1 <= limit <= 100:
                raise ValueError()
        except (TypeError, ValueError):
            raise Error(422, 'invalid_pagination', 'Paginação inválida.')
        if query.get('processId'):
            allowed = [value for value in allowed if value == query['processId']]
        if not allowed:
            return {'items': [], 'nextCursor': None}
        where = 'environment=? AND process_id IN (' + ','.join('?' for _ in allowed) + ')'
        params = [self.environment, *allowed]
        if query.get('status'):
            where += ' AND status=?'
            params.append(query['status'])
        with self.store.transaction() as db:
            sql = 'SELECT document FROM automation_runs WHERE ' + where + ' ORDER BY created_at DESC,id DESC '
            sql += 'OFFSET ? ROWS FETCH NEXT ? ROWS ONLY' if db.sql_server else 'LIMIT ? OFFSET ?'
            params.extend([offset, limit + 1] if db.sql_server else [limit + 1, offset])
            rows = db.execute(sql, params).fetchall()
            return {'items': [json.loads(row[0]) for row in rows[:limit]], 'nextCursor': str(offset + limit) if len(rows) > limit else None}

    def summary(self, principal):
        processes = self.processes(principal)['items']
        ids = [row['id'] for row in processes]
        counts = {state: 0 for state in ('queued', 'running', 'succeeded', 'failed', 'cancelled')}
        if ids:
            with self.store.transaction() as db:
                rows = db.execute('SELECT status,COUNT(*) FROM automation_runs WHERE environment=? AND process_id IN (' + ','.join('?' for _ in ids) + ') GROUP BY status', [self.environment, *ids]).fetchall()
                counts.update(dict(rows))
        is_external = bool(self.external_enabled)
        return {'availableProcesses': len(ids), 'counts': counts, 'executorConnected': is_external,
                'externalDispatchEnabled': is_external, 'costs': None, 'asOf': now(), 'environment': self.environment}

    # ── Machine lease / complete ────────────────────────────────────────

    def _derive_idempotency(self, run_id, fencing_token):
        raw = f"{run_id}:{fencing_token}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def lease(self, principal):
        _require_worker(principal)
        if not self.external_enabled:
            raise Error(503, 'external_disabled', 'Despacho externo desabilitado.')
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        # Phase 1: recover expired leases (commit even if no work later, to persist lease_exhausted)
        with self.store.transaction() as db:
            rows = db.execute('SELECT document FROM automation_runs WHERE environment=?', (self.environment,)).fetchall()
            for row in rows:
                try:
                    run = json.loads(row[0])
                except Exception:
                    continue
                if run.get('executionMode') != 'external':
                    continue
                if run.get('status') != 'running':
                    continue
                exp = run.get('leaseExpiresAt')
                if not exp:
                    continue
                try:
                    exp_dt = datetime.fromisoformat(exp.replace('Z', '+00:00'))
                except Exception:
                    continue
                if now_dt > exp_dt:
                    run['fencingToken'] = int(run.get('fencingToken', 0)) + 1
                    run['version'] = int(run.get('version', 1)) + 1
                    run['updatedAt'] = now_iso
                    delivery = int(run.get('deliveryCount', 0))
                    if delivery >= MAX_LEASES_PER_RUN:
                        run['status'] = 'failed'
                        run['finishedAt'] = now_iso
                        generic = ERROR_GENERIC_MESSAGES['lease_exhausted']
                        run['error'] = {'code': 'lease_exhausted', 'message': generic}
                        run.pop('leaseId', None)
                        run.pop('leasedAt', None)
                        run.pop('leaseExpiresAt', None)
                        run['history'].append({'status': 'failed', 'at': now_iso, 'actor': f"gcp-worker:{principal['id']}", 'reason': 'lease_exhausted', 'code': 'lease_exhausted', 'fencingToken': run['fencingToken'], 'error': run['error']})
                        db.execute('UPDATE automation_runs SET status=?,document=? WHERE environment=? AND id=?', (run['status'], json.dumps(run), self.environment, run['id']))
                        db.audit(f"gcp-worker:{principal['id']}", 'automation_lease_exhausted', 'automation_runs', run['id'], run['version'])
                    else:
                        run['status'] = 'queued'
                        run.pop('leaseId', None)
                        run.pop('leasedAt', None)
                        run.pop('leaseExpiresAt', None)
                        run['history'].append({'status': 'queued', 'at': now_iso, 'actor': f"gcp-worker:{principal['id']}", 'reason': 'lease_expired', 'fencingToken': run['fencingToken']})
                        db.execute('UPDATE automation_runs SET status=?,document=? WHERE environment=? AND id=?', (run['status'], json.dumps(run), self.environment, run['id']))
        # Phase 2: select oldest queued external seo-audit and lease
        with self.store.transaction() as db:
            q_rows = db.execute('SELECT document FROM automation_runs WHERE environment=? AND status=? AND process_id=?', (self.environment, 'queued', 'seo-audit')).fetchall()
            candidates = []
            for row in q_rows:
                try:
                    run = json.loads(row[0])
                except Exception:
                    continue
                if run.get('executionMode') != 'external':
                    continue
                if run.get('status') != 'queued':
                    continue
                if int(run.get('deliveryCount', 0)) >= MAX_LEASES_PER_RUN:
                    continue
                candidates.append(run)
            if not candidates:
                raise Error(404, 'no_work', 'Nenhum trabalho disponível.')
            candidates.sort(key=lambda r: (r.get('createdAt', ''), r.get('id', '')))
            chosen = candidates[0]
            chosen['status'] = 'running'
            chosen['externalDispatched'] = True
            chosen['leaseId'] = str(uuid.uuid4())
            chosen['fencingToken'] = int(chosen.get('fencingToken', 0)) + 1
            chosen['deliveryCount'] = int(chosen.get('deliveryCount', 0)) + 1
            chosen['leasedAt'] = now_iso
            expires_dt = now_dt + timedelta(seconds=LEASE_TTL_SECONDS)
            chosen['leaseExpiresAt'] = expires_dt.isoformat()
            chosen['version'] = int(chosen.get('version', 1)) + 1
            chosen['updatedAt'] = now_iso
            chosen['history'].append({'status': 'running', 'at': now_iso, 'actor': f"gcp-worker:{principal['id']}", 'leaseId': chosen['leaseId'], 'fencingToken': chosen['fencingToken'], 'deliveryCount': chosen['deliveryCount']})
            db.execute('UPDATE automation_runs SET status=?,document=? WHERE environment=? AND id=?', (chosen['status'], json.dumps(chosen), self.environment, chosen['id']))
            db.audit(f"gcp-worker:{principal['id']}", 'automation_leased', 'automation_runs', chosen['id'], chosen['version'])
            idem = self._derive_idempotency(chosen['id'], chosen['fencingToken'])
            inp = chosen.get('input', {})
            bounded_input = {}
            for key in ('market', 'language', 'targetUrl'):
                if key in inp:
                    bounded_input[key] = inp[key]
            if 'notes' in inp and isinstance(inp['notes'], str) and inp['notes']:
                bounded_input['notes'] = inp['notes'][:2000]
            envelope = {
                'schemaVersion': 1,
                'runId': chosen['id'],
                'processId': chosen['processId'],
                'idempotencyKey': idem,
                'input': bounded_input,
                'leaseId': chosen['leaseId'],
                'fencingToken': chosen['fencingToken'],
                'leasedAt': chosen['leasedAt'],
                'leaseExpiresAt': chosen['leaseExpiresAt'],
            }
            return envelope

    def complete(self, principal, body):
        _require_worker(principal)
        if not isinstance(body, dict):
            raise Error(422, 'invalid_body', 'Objeto JSON obrigatório.')
        # Body max and strict fields
        allowed_keys = {'runId', 'leaseId', 'fencingToken', 'status', 'result', 'errorCode', 'errorMessage'}
        if set(body) - allowed_keys:
            raise Error(422, 'invalid_fields', 'Parâmetros desconhecidos.')
        # Validate presence
        run_id = body.get('runId')
        lease_id = body.get('leaseId')
        fencing = body.get('fencingToken')
        status = body.get('status')
        if not isinstance(run_id, str) or not UUID_RE.match(run_id):
            raise Error(422, 'invalid_runId', 'runId inválido.')
        if not isinstance(lease_id, str) or not UUID_RE.match(lease_id):
            raise Error(422, 'invalid_leaseId', 'leaseId inválido.')
        if type(fencing) is not int or fencing <= 0:
            raise Error(422, 'invalid_fencingToken', 'fencingToken inválido.')
        if status not in ('succeeded', 'failed'):
            raise Error(422, 'invalid_status', 'status deve ser succeeded ou failed.')
        # Validate result/error mutual exclusivity and bounds
        if status == 'succeeded':
            if 'result' not in body:
                raise Error(422, 'result_required', 'Resultado obrigatório para succeeded.')
            if 'errorCode' in body or 'errorMessage' in body:
                raise Error(422, 'invalid_fields', 'Campos de erro não permitidos para succeeded.')
            result = body['result']
            if not isinstance(result, dict):
                raise Error(422, 'invalid_result', 'result deve ser objeto.')
            try:
                serialized = _canonical_dumps(result)
            except Exception:
                raise Error(422, 'invalid_result', 'result inválido.')
            if len(serialized.encode('utf-8')) > MAX_RESULT_SERIALIZED:
                raise Error(422, 'result_too_large', 'Resultado excede 64KB.')
            # bound top-level result size sanity: max 1MB check already
        else:
            if 'errorCode' not in body or 'errorMessage' not in body:
                raise Error(422, 'error_required', 'errorCode e errorMessage obrigatórios para failed.')
            if 'result' in body:
                raise Error(422, 'invalid_fields', 'result não permitido para failed.')
            error_code = body['errorCode']
            error_msg = body['errorMessage']
            if not isinstance(error_code, str) or not 1 <= len(error_code.strip()) <= 100:
                raise Error(422, 'invalid_error', 'errorCode inválido.')
            if not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', error_code.strip()):
                raise Error(422, 'invalid_error', 'errorCode inválido.')
            if not isinstance(error_msg, str) or not 1 <= len(error_msg.strip()) <= 500:
                raise Error(422, 'invalid_error', 'errorMessage inválida.')
            # Raw errorMessage is validated for bounds but never persisted; only mapped generic is stored
        with self.store.transaction() as db:
            row = db.execute('SELECT document FROM automation_runs WHERE environment=? AND id=?', (self.environment, run_id)).fetchone()
            if not row:
                raise Error(404, 'not_found', 'Execução não encontrada.')
            run = json.loads(row[0])
            # Must be external
            if run.get('executionMode') != 'external':
                raise Error(409, 'invalid_execution_mode', 'Execução não é externa.')
            # If already terminal, handle replay/divergence
            if run.get('status') in ('succeeded', 'failed'):
                stored_lease = run.get('leaseId')
                stored_fence = run.get('fencingToken')
                # Duplicate exact completion must replay same receipt
                if stored_lease == lease_id and stored_fence == fencing and run.get('status') == status:
                    if status == 'succeeded':
                        incoming_hash = hashlib.sha256(_canonical_dumps(body['result']).encode()).hexdigest()
                        if run.get('resultHash') == incoming_hash:
                            return {'runId': run['id'], 'status': run['status'], 'version': run['version'], 'resultHash': run.get('resultHash'), 'finishedAt': run.get('finishedAt')}
                    else:
                        # Compare allowlisted code and generic message (not raw)
                        raw_code = body['errorCode'].strip()
                        stable = raw_code if raw_code in ALLOWED_ERROR_CODES else 'worker_failed'
                        expected_msg = ERROR_GENERIC_MESSAGES.get(stable, ERROR_GENERIC_MESSAGES['worker_failed'])
                        if run.get('error', {}).get('code') == stable and run.get('error', {}).get('message') == expected_msg:
                            return {'runId': run['id'], 'status': run['status'], 'version': run['version'], 'error': run.get('error'), 'finishedAt': run.get('finishedAt')}
                raise Error(409, 'completion_conflict', 'Conclusão divergente ou expirada.')

            # Must be running with active unexpired lease and fencing token
            if run.get('status') != 'running':
                raise Error(409, 'invalid_lease', 'Execução não está em execução.')
            if run.get('leaseId') != lease_id or run.get('fencingToken') != fencing:
                raise Error(409, 'fencing_conflict', 'Lease ou fencingToken inválido.')
            exp = run.get('leaseExpiresAt')
            if not exp:
                raise Error(409, 'invalid_lease', 'Lease inválido.')
            try:
                exp_dt = datetime.fromisoformat(exp.replace('Z', '+00:00'))
                now_dt = datetime.now(timezone.utc)
                if now_dt > exp_dt:
                    raise Error(409, 'lease_expired', 'Lease expirado.')
            except Error:
                raise
            except Exception:
                raise Error(409, 'invalid_lease', 'Lease inválido.')

            timestamp = now()
            if status == 'succeeded':
                serialized = _canonical_dumps(body['result'])
                result_hash = hashlib.sha256(serialized.encode()).hexdigest()
                run['status'] = 'succeeded'
                run['result'] = body['result']
                run['resultHash'] = result_hash
                run['finishedAt'] = timestamp
                run['version'] = int(run.get('version', 1)) + 1
                run['updatedAt'] = timestamp
                run['history'].append({'status': 'succeeded', 'at': timestamp, 'actor': f"gcp-worker:{principal['id']}", 'leaseId': lease_id, 'fencingToken': fencing, 'evidenceSource': 'google_worker', 'resultHash': result_hash})
                db.execute('UPDATE automation_runs SET status=?,document=? WHERE environment=? AND id=?', (run['status'], json.dumps(run), self.environment, run['id']))
                db.audit(f"gcp-worker:{principal['id']}", 'automation_completed', 'automation_runs', run_id, run['version'])
                return {'runId': run['id'], 'status': 'succeeded', 'version': run['version'], 'resultHash': result_hash, 'finishedAt': timestamp}
            else:
                raw_code = body['errorCode'].strip()
                # Map to allowlisted stable code, never persist raw errorMessage/URLs/secrets
                stable_code = raw_code if raw_code in ALLOWED_ERROR_CODES else 'worker_failed'
                if stable_code not in ALLOWED_ERROR_CODES:
                    stable_code = 'worker_failed'
                generic_msg = ERROR_GENERIC_MESSAGES.get(stable_code, ERROR_GENERIC_MESSAGES['worker_failed'])
                run['status'] = 'failed'
                run['error'] = {'code': stable_code, 'message': generic_msg}
                run['finishedAt'] = timestamp
                run['version'] = int(run.get('version', 1)) + 1
                run['updatedAt'] = timestamp
                run['history'].append({'status': 'failed', 'at': timestamp, 'actor': f"gcp-worker:{principal['id']}", 'leaseId': lease_id, 'fencingToken': fencing, 'evidenceSource': 'google_worker', 'error': {'code': stable_code, 'message': generic_msg}})
                db.execute('UPDATE automation_runs SET status=?,document=? WHERE environment=? AND id=?', (run['status'], json.dumps(run), self.environment, run['id']))
                db.audit(f"gcp-worker:{principal['id']}", 'automation_failed', 'automation_runs', run_id, run['version'])
                return {'runId': run['id'], 'status': 'failed', 'version': run['version'], 'error': run['error'], 'finishedAt': timestamp}

