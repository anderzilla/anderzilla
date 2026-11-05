"""Authoritative Member Area service for Clerk-authenticated adult members.

Implements:
- Central member guard (`require_member`) requiring active Clerk session, verified email,
  active local account, and completed 18+ registration (`managed_profiles`).
- Editorial visibility & entitlement enforcement before projecting any item metadata.
- Additive per-account backfill from `preferences_bookmarks` into relational collections.
- Interests (`GET/PUT /api/member/interests`) with versioned optimistic concurrency (`409 interests_conflict`).
- Backpack (`GET/PUT/DELETE /api/member/backpack`) with >1000 pagination and unavailable placeholders.
- Personalized Radar (`GET /api/member/radar`) with union of declared interests and temporary category filter.
- Exploration (`GET /api/member/exploration`, `POST /events`, `DELETE /{id}`, `POST /clear`) with
  atomic `exploration_generation` increment and tombstone rejection of stale in-transit events.
- Player Dashboard (`GET /api/member/dashboard`) in 6 blocks.
- Transactional Missions & Authoritative Single Wallet (`GET /api/points/wallet`, `/ledger`, `/missions`,
  `POST /challenge`, `GET /challenges/{attemptId}`, `POST /evidence`, `POST /pending/claim`,
  `GET /operations/{operationId}`, `GET /operation-status`) with campaign budget & per-account quota
  reservation, idempotency keys, and single release/consume guarantees.
"""
import base64
import json
import os
import re
import time

from . import catalog, security
from .clerk_service import ClerkAccountService, birth_date, iso
from .core import INTERESTS, Rejected, identifier, preferences, reject

SAFE_ID_RE = re.compile(r'^[A-Za-z0-9_.:-]{1,128}$')
SUPPORT_CHANNEL = 'player.one@anderzilla.com'
VALID_PROGRAM_STATES = frozenset({'disabled', 'active', 'new_activity_paused', 'maintenance', 'closed'})
FORBIDDEN_AUTHORITY_FIELDS = frozenset({
    'accountId', 'account_id', 'userId', 'user_id', 'subject', 'sub',
    'role', 'roles', 'isAdmin', 'is_admin', 'plan', 'entitlement', 'entitlements',
    'award', 'awardKP', 'award_kp', 'balance', 'available', 'reserved',
    'cpf', 'cpfMasked', 'birthDate', 'birth_date', 'email', 'emailVerified',
    'state', 'approved', 'correct', 'coverageReference',
})


def reject_authority_fields(body):
    if isinstance(body, dict):
        forbidden = set(body.keys()) & FORBIDDEN_AUTHORITY_FIELDS
        if forbidden:
            reject('invalid_fields', 'Campos de autoridade ou identidade não são permitidos.', 422)


def validate_discovery_id(value):
    if not isinstance(value, str) or not SAFE_ID_RE.fullmatch(value.strip()):
        reject('invalid_discovery', 'Identificador de conteúdo inválido.', 422)
    return value.strip()


def validate_idempotency_key(value, required=True):
    if value is None or value == '':
        if required:
            reject('idempotency_key_required', 'Cabeçalho Idempotency-Key obrigatório.', 422)
        return None
    if not isinstance(value, str) or not 8 <= len(value.strip()) <= 128 or not SAFE_ID_RE.fullmatch(value.strip()):
        reject('invalid_idempotency_key', 'Cabeçalho Idempotency-Key inválido.', 422)
    return value.strip()


def parse_expected_version(body, headers=None, required=False):
    raw = None
    if isinstance(body, dict) and 'expectedVersion' in body:
        raw = body.get('expectedVersion')
    elif headers and headers.get('if-match'):
        etag = str(headers.get('if-match')).strip().strip('"').strip("'")
        if etag.startswith('W/'):
            etag = etag[2:].strip().strip('"')
        if etag.isdigit():
            raw = int(etag)
        else:
            raw = etag
    if raw is None:
        if required:
            reject('invalid_version', 'Informe expectedVersion inteiro positivo.', 422)
        return None
    if type(raw) is not int or raw < 1:
        reject('invalid_version', 'Informe expectedVersion inteiro positivo.', 422)
    return raw


def parse_item_version(value):
    if value is None:
        return None
    if type(value) is int and value >= 1:
        return value
    if isinstance(value, str):
        s = value.strip()
        if s.lower().startswith('v') and s[1:].isdigit():
            v = int(s[1:])
            if v >= 1:
                return v
        if s.isdigit():
            v = int(s)
            if v >= 1:
                return v
        # Date or string version -> deterministic positive int
        if SAFE_ID_RE.fullmatch(s):
            return 1
    reject('invalid_version', 'itemVersion inválido.', 422)


def encode_cursor(data):
    raw = json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')


def decode_cursor(cursor_str, expected_scope=None):
    if not cursor_str:
        return None
    if not isinstance(cursor_str, str) or len(cursor_str) > 512:
        reject('invalid_cursor', 'Cursor de paginação inválido.', 422)
    try:
        padded = cursor_str + '=' * (-len(cursor_str) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode('ascii')).decode('utf-8'))
        if not isinstance(payload, dict):
            raise ValueError()
        if expected_scope is not None and payload.get('s') != expected_scope:
            reject('invalid_cursor', 'Cursor não corresponde ao filtro atual.', 422)
        return payload
    except Rejected:
        raise
    except Exception:
        reject('invalid_cursor', 'Cursor de paginação inválido.', 422)


def parse_limit(query, default=20, maximum=50):
    raw = (query or {}).get('limit')
    if raw is None or raw == '':
        return default
    try:
        val = int(raw)
    except (ValueError, TypeError):
        reject('invalid_limit', f'Limite deve ser entre 1 e {maximum}.', 422)
    if not 1 <= val <= maximum:
        reject('invalid_limit', f'Limite deve ser entre 1 e {maximum}.', 422)
    return val


class MemberAreaService:
    """Single source of truth for Member Area collections, Radar, Dashboard, Missions and KP Wallet."""

    def __init__(self, store, cfg, clock=None, catalog_overrides=None):
        self.store = store
        self.cfg = cfg or {}
        self.clock = clock or (lambda: int(time.time()))
        self.accounts = ClerkAccountService(store, self.cfg, clock=self.clock)
        self.catalog_overrides = catalog_overrides

    def program_state(self):
        state = (
            self.cfg.get('programState')
            or self.cfg.get('programStatus')
            or os.environ.get('IDENTITY_KP_PROGRAM_STATE', '').strip()
            or os.environ.get('IDENTITY_KP_PROGRAM_STATUS', '').strip()
        )
        if state in VALID_PROGRAM_STATES:
            return state
        enabled = self.cfg.get('rewards')
        if enabled is None:
            enabled = self.cfg.get('rewardsEnabled')
        if enabled is None:
            enabled = os.environ.get('IDENTITY_REWARDS_ENABLED', '').lower() == 'true'
        return 'active' if enabled else 'disabled'

    def rewards_enabled(self):
        return self.program_state() in {'active', 'new_activity_paused', 'maintenance', 'closed'}

    def _catalog(self):
        overrides = self.catalog_overrides if self.catalog_overrides is not None else self.cfg.get('catalogOverrides')
        return catalog.get_catalog(overrides)

    def _resolve_member_id(self, db, identity_or_account_id):
        if isinstance(identity_or_account_id, str):
            row = db.execute('SELECT * FROM accounts WHERE id=?', (identity_or_account_id,)).fetchone()
            if not row or row['state'] != 'active':
                reject('authentication_required', 'Conta indisponível.', 401)
            self._ensure_collection_state(db, row['id'])
            return row
        return self.require_member(db, identity_or_account_id)

    def require_member(self, db, identity):
        """Enforce active Clerk identity + active local account + completed 18+ adult registration."""
        if identity is None:
            reject('authentication_required', 'Entre para continuar.', 401)
        if isinstance(identity, str):
            return self._resolve_member_id(db, identity)
        row = self.accounts._record(db, identity, required=True, allow_deleted=False)
        if not row['cpf_fingerprint'] or not row['birth_date']:
            reject('onboarding_required', 'Complete seu cadastro para acessar o espaço do jogador.', 403)
        _, age = birth_date(row['birth_date'], self.clock())
        if age < 18:
            reject('minor_registration_unavailable', 'Acesso exclusivo para maiores de 18 anos.', 403)
        if not row['email_verified']:
            reject('email_unverified', 'Confirme seu e-mail para continuar.', 403)
        self._ensure_collection_state(db, row['id'])
        return row

    def _ensure_collection_state(self, db, account_id):
        """Additive idempotent per-account backfill from preferences_bookmarks to relational tables."""
        state = db.execute('SELECT * FROM member_collection_state WHERE account_id=?', (account_id,)).fetchone()
        now = self.clock()
        if state is not None and state['backfilled_at'] is not None:
            return state
        pref = db.execute('SELECT interests,saved,opened FROM preferences_bookmarks WHERE account_id=?', (account_id,)).fetchone()
        interests, saved, opened = [], [], []
        if pref:
            try:
                interests = [c for c in json.loads(pref['interests'] or '[]') if isinstance(c, str) and c in INTERESTS]
            except Exception:
                interests = []
            try:
                saved = [s for s in json.loads(pref['saved'] or '[]') if isinstance(s, str) and SAFE_ID_RE.fullmatch(s)]
            except Exception:
                saved = []
            try:
                opened = [o for o in json.loads(pref['opened'] or '[]') if isinstance(o, str) and SAFE_ID_RE.fullmatch(o)]
            except Exception:
                opened = []
        if state is None:
            db.execute(
                'INSERT INTO member_collection_state(account_id,interests_version,exploration_generation,exploration_paused,backfilled_at,updated_at) VALUES(?,?,?,?,?,?)',
                (account_id, 1, 1, 0, now, now),
            )
        else:
            db.execute('UPDATE member_collection_state SET backfilled_at=?,updated_at=? WHERE account_id=?', (now, now, account_id))
        for cat_id in sorted(set(interests)):
            if not db.execute('SELECT 1 FROM member_interests WHERE account_id=? AND category_id=?', (account_id, cat_id)).fetchone():
                db.execute('INSERT INTO member_interests(account_id,category_id,created_at) VALUES(?,?,?)', (account_id, cat_id, now))
        for idx, disc_id in enumerate(dict.fromkeys(saved)):
            if not db.execute('SELECT 1 FROM member_bookmarks WHERE account_id=? AND discovery_id=?', (account_id, disc_id)).fetchone():
                db.execute('INSERT INTO member_bookmarks(account_id,discovery_id,saved_at) VALUES(?,?,?)', (account_id, disc_id, now - idx))
        for idx, disc_id in enumerate(dict.fromkeys(opened)):
            if not db.execute('SELECT 1 FROM member_exploration WHERE account_id=? AND discovery_id=?', (account_id, disc_id)).fetchone():
                ts = now - idx
                db.execute(
                    'INSERT INTO member_exploration(account_id,discovery_id,first_opened_at,last_opened_at,open_count,generation,item_version) VALUES(?,?,?,?,?,?,?)',
                    (account_id, disc_id, ts, ts, 1, 1, 1),
                )
        return db.execute('SELECT * FROM member_collection_state WHERE account_id=?', (account_id,)).fetchone()

    def _sync_legacy_mirror(self, db, account_id):
        """Keep preferences_bookmarks synchronized as a read-only mirror for rollback safety."""
        interests = [r['category_id'] for r in db.execute('SELECT category_id FROM member_interests WHERE account_id=? ORDER BY category_id', (account_id,)).fetchall()]
        saved = [r['discovery_id'] for r in db.page('SELECT discovery_id FROM member_bookmarks WHERE account_id=? ORDER BY saved_at DESC, discovery_id DESC', (account_id,), 1000).fetchall()]
        opened = [r['discovery_id'] for r in db.page('SELECT discovery_id FROM member_exploration WHERE account_id=? ORDER BY last_opened_at DESC, discovery_id DESC', (account_id,), 1000).fetchall()]
        db.execute(
            'UPDATE preferences_bookmarks SET interests=?,saved=?,opened=? WHERE account_id=?',
            (json.dumps(interests), json.dumps(saved), json.dumps(opened), account_id),
        )

    def _active_entitlements(self, db, account_id):
        now = self.clock()
        rows = db.execute(
            "SELECT kind,target_id,state,starts_at,ends_at FROM account_entitlements WHERE account_id=? AND state='active'",
            (account_id,),
        ).fetchall()
        return [
            r for r in rows
            if (r['starts_at'] is None or r['starts_at'] <= now) and (r['ends_at'] is None or r['ends_at'] > now)
        ]

    def _accessible_item(self, db, account_id, discovery_id, entitlements=None):
        items = self._catalog()
        item = items.get(discovery_id)
        if not item:
            return None
        if entitlements is None:
            entitlements = self._active_entitlements(db, account_id)
        if not catalog.can_access_discovery(item, is_active_member=True, active_entitlements=entitlements, now=self.clock()):
            return None
        return catalog.project_discovery(item)

    # -------------------------------------------------------------------------
    # Interests
    # -------------------------------------------------------------------------
    def get_interests(self, identity):
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            state = self._ensure_collection_state(db, member['id'])
            rows = db.execute('SELECT category_id FROM member_interests WHERE account_id=? ORDER BY category_id', (member['id'],)).fetchall()
            cats = [r['category_id'] for r in rows]
            return {
                'interests': cats,
                'categoryIds': cats,
                'version': state['interests_version'],
                'updatedAt': iso(state['updated_at']),
                'availableCategories': sorted(INTERESTS),
            }

    def put_interests(self, identity, body, headers=None):
        reject_authority_fields(body)
        if not isinstance(body, dict) or set(body.keys()) - {'categoryIds', 'interests', 'expectedVersion'}:
            reject('invalid_fields', 'Campos inválidos para interesses.', 422)
        expected_version = parse_expected_version(body, headers, required=True)
        raw_cats = body.get('interests') if 'interests' in body else body.get('categoryIds', [])
        cats = preferences(raw_cats)
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            state = self._ensure_collection_state(db, member['id'])
            if expected_version is not None and state['interests_version'] != expected_version:
                reject('interests_conflict', 'Seus interesses mudaram em outro acesso. Confira a seleção antes de salvar.', 409)
            now = self.clock()
            new_version = state['interests_version'] + 1
            db.execute('DELETE FROM member_interests WHERE account_id=?', (member['id'],))
            for cat_id in cats:
                db.execute('INSERT INTO member_interests(account_id,category_id,created_at) VALUES(?,?,?)', (member['id'], cat_id, now))
            db.execute(
                'UPDATE member_collection_state SET interests_version=?,updated_at=? WHERE account_id=?',
                (new_version, now, member['id']),
            )
            self._sync_legacy_mirror(db, member['id'])
            return {
                'interests': cats,
                'categoryIds': cats,
                'version': new_version,
                'updatedAt': iso(now),
                'availableCategories': sorted(INTERESTS),
            }

    # -------------------------------------------------------------------------
    # Backpack (Mochila)
    # -------------------------------------------------------------------------
    def get_backpack(self, identity, query=None):
        query = query or {}
        limit = parse_limit(query, default=20, maximum=50)
        cat_filter = query.get('category', '').strip()
        if cat_filter and cat_filter not in INTERESTS:
            reject('invalid_category', 'Categoria inválida.', 422)
        search_q = query.get('q', '').strip().lower()
        if len(search_q) > 120:
            reject('invalid_query', 'Busca muito longa.', 422)
        scope = f'backpack:{cat_filter}:{search_q}'
        cursor = decode_cursor(query.get('cursor'), expected_scope=scope)
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            entitlements = self._active_entitlements(db, member['id'])
            total_count = db.execute('SELECT COUNT(*) AS count FROM member_bookmarks WHERE account_id=?', (member['id'],)).fetchone()['count']
            rows = db.execute(
                'SELECT discovery_id,saved_at FROM member_bookmarks WHERE account_id=? ORDER BY saved_at DESC, discovery_id DESC',
                (member['id'],),
            ).fetchall()
            matched = []
            for r in rows:
                disc_id = r['discovery_id']
                saved_at = r['saved_at']
                proj = self._accessible_item(db, member['id'], disc_id, entitlements)
                if proj is None:
                    # Unavailable item placeholder: never leak private title, summary, slug or category!
                    if cat_filter or search_q:
                        continue
                    entry = {
                        'discoveryId': disc_id,
                        'available': False,
                        'savedAt': iso(saved_at),
                        '_sortSavedAt': saved_at,
                    }
                else:
                    if cat_filter and proj['category'] != cat_filter:
                        continue
                    if search_q:
                        haystack = f"{proj['titlePT']} {proj['titleEN']} {proj['summaryPT']} {proj['summaryEN']}".lower()
                        if search_q not in haystack:
                            continue
                    entry = {
                        **proj,
                        'discoveryId': disc_id,
                        'available': True,
                        'savedAt': iso(saved_at),
                        'item': proj,
                        '_sortSavedAt': saved_at,
                    }
                if cursor:
                    c_ts = cursor.get('ts')
                    c_id = cursor.get('id')
                    if (saved_at > c_ts) or (saved_at == c_ts and disc_id >= c_id):
                        continue
                matched.append(entry)
            page_items = matched[:limit]
            next_cursor = None
            if len(matched) > limit and page_items:
                last = page_items[-1]
                next_cursor = encode_cursor({'s': scope, 'ts': last['_sortSavedAt'], 'id': last['discoveryId']})
            for it in page_items:
                it.pop('_sortSavedAt', None)
            return {
                'items': page_items,
                'totalCount': total_count,
                'filteredCount': len(matched) if not cursor else None,
                'nextCursor': next_cursor,
            }

    def put_backpack_item(self, identity, discovery_id):
        disc_id = validate_discovery_id(discovery_id)
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            entitlements = self._active_entitlements(db, member['id'])
            proj = self._accessible_item(db, member['id'], disc_id, entitlements)
            if proj is None:
                reject('content_unavailable', 'Esta descoberta não está disponível agora.', 404)
            existing = db.execute(
                'SELECT saved_at FROM member_bookmarks WHERE account_id=? AND discovery_id=?',
                (member['id'], disc_id),
            ).fetchone()
            now = self.clock()
            if existing:
                saved_at = existing['saved_at']
                already_saved = True
            else:
                count = db.execute('SELECT COUNT(*) AS count FROM member_bookmarks WHERE account_id=?', (member['id'],)).fetchone()['count']
                if count >= 5000:
                    reject('backpack_capacity_reached', 'Limite da mochila atingido. Remova itens antigos para guardar novos.', 409)
                saved_at = now
                already_saved = False
                db.execute(
                    'INSERT INTO member_bookmarks(account_id,discovery_id,saved_at) VALUES(?,?,?)',
                    (member['id'], disc_id, saved_at),
                )
                db.execute('UPDATE member_collection_state SET updated_at=? WHERE account_id=?', (now, member['id']))
                self._sync_legacy_mirror(db, member['id'])
            total = db.execute('SELECT COUNT(*) AS count FROM member_bookmarks WHERE account_id=?', (member['id'],)).fetchone()['count']
            return {
                'discoveryId': disc_id,
                'saved': True,
                'alreadySaved': already_saved,
                'savedAt': iso(saved_at),
                'totalCount': total,
                'item': proj,
            }

    def delete_backpack_item(self, identity, discovery_id):
        disc_id = validate_discovery_id(discovery_id)
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            existing = db.execute(
                'SELECT saved_at FROM member_bookmarks WHERE account_id=? AND discovery_id=?',
                (member['id'], disc_id),
            ).fetchone()
            now = self.clock()
            if existing:
                db.execute('DELETE FROM member_bookmarks WHERE account_id=? AND discovery_id=?', (member['id'], disc_id))
                db.execute('UPDATE member_collection_state SET updated_at=? WHERE account_id=?', (now, member['id']))
                self._sync_legacy_mirror(db, member['id'])
            total = db.execute('SELECT COUNT(*) AS count FROM member_bookmarks WHERE account_id=?', (member['id'],)).fetchone()['count']
            return {
                'discoveryId': disc_id,
                'saved': False,
                'removed': bool(existing),
                'totalCount': total,
            }

    # -------------------------------------------------------------------------
    # Personalized Radar (Seu Radar)
    # -------------------------------------------------------------------------
    def get_radar(self, identity, query=None):
        query = query or {}
        limit = parse_limit(query, default=20, maximum=50)
        cat_filter = query.get('category', '').strip()
        if cat_filter and cat_filter not in INTERESTS:
            reject('invalid_category', 'Categoria inválida.', 422)
        search_q = query.get('q', '').strip().lower()
        if len(search_q) > 120:
            reject('invalid_query', 'Busca muito longa.', 422)
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            state = self._ensure_collection_state(db, member['id'])
            entitlements = self._active_entitlements(db, member['id'])
            interests = [
                r['category_id']
                for r in db.execute('SELECT category_id FROM member_interests WHERE account_id=? ORDER BY category_id', (member['id'],)).fetchall()
            ]
            saved_ids = {
                r['discovery_id']
                for r in db.execute('SELECT discovery_id FROM member_bookmarks WHERE account_id=?', (member['id'],)).fetchall()
            }
            scope = f"radar:{state['interests_version']}:{cat_filter}:{search_q}"
            cursor = decode_cursor(query.get('cursor'), expected_scope=scope)
            if not interests and not cat_filter:
                return {
                    'status': 'interests_empty',
                    'items': [],
                    'declaredInterests': [],
                    'interestsVersion': state['interests_version'],
                    'activeCategoryFilter': None,
                    'hasInterests': False,
                    'outsideDeclaredInterests': False,
                    'temporaryFilterOutsideInterests': False,
                    'nextCursor': None,
                }
            outside_declared = bool(cat_filter and cat_filter not in interests)
            effective_cats = {cat_filter} if cat_filter else set(interests)
            catalog_items = [
                {
                    **catalog.project_discovery(item),
                    'discoveryId': item['id'],
                    'available': True,
                }
                for item in self._catalog().values()
                if catalog.can_access_discovery(item, is_active_member=True, active_entitlements=entitlements, now=self.clock())
                and item.get('category') in effective_cats
            ]
            if search_q:
                catalog_items = [
                    it for it in catalog_items
                    if search_q in f"{it['titlePT']} {it['titleEN']} {it['summaryPT']} {it['summaryEN']}".lower()
                ]
            sorted_items = catalog.sort_discoveries(catalog_items)
            if cursor:
                c_rec = cursor.get('r', '')
                c_pub = cursor.get('p', '')
                c_id = cursor.get('id', '')
                filtered = []
                for it in sorted_items:
                    rec = it['recencyDay']
                    pub = it['published'][:10] if it['published'] else '0000-00-00'
                    if (rec < c_rec) or (rec == c_rec and pub < c_pub) or (rec == c_rec and pub == c_pub and it['id'] > c_id):
                        filtered.append(it)
                sorted_items = filtered
            page = sorted_items[:limit]
            for it in page:
                it['saved'] = it['id'] in saved_ids
            next_cursor = None
            if len(sorted_items) > limit and page:
                last = page[-1]
                next_cursor = encode_cursor({
                    's': scope,
                    'r': last['recencyDay'],
                    'p': last['published'][:10] if last['published'] else '0000-00-00',
                    'id': last['id'],
                })
            return {
                'status': 'ok' if page else 'radar_empty',
                'items': page,
                'declaredInterests': interests,
                'interestsVersion': state['interests_version'],
                'activeCategoryFilter': cat_filter or None,
                'hasInterests': bool(interests),
                'outsideDeclaredInterests': outside_declared,
                'temporaryFilterOutsideInterests': outside_declared,
                'nextCursor': next_cursor,
            }

    # -------------------------------------------------------------------------
    # Exploration (Exploração)
    # -------------------------------------------------------------------------
    def get_exploration(self, identity, query=None):
        query = query or {}
        limit = parse_limit(query, default=20, maximum=50)
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            state = self._ensure_collection_state(db, member['id'])
            entitlements = self._active_entitlements(db, member['id'])
            gen = state['exploration_generation']
            scope = f'exploration:{gen}'
            cursor = decode_cursor(query.get('cursor'), expected_scope=scope)
            rows = db.execute(
                'SELECT discovery_id,first_opened_at,last_opened_at,open_count,generation,item_version '
                'FROM member_exploration WHERE account_id=? ORDER BY last_opened_at DESC, discovery_id DESC',
                (member['id'],),
            ).fetchall()
            matched = []
            categories_explored = set()
            for r in rows:
                disc_id = r['discovery_id']
                proj = self._accessible_item(db, member['id'], disc_id, entitlements)
                if proj is not None:
                    categories_explored.add(proj['category'])
                    entry = {
                        **proj,
                        'discoveryId': disc_id,
                        'available': True,
                        'openedAt': iso(r['last_opened_at']),
                        'firstOpenedAt': iso(r['first_opened_at']),
                        'lastOpenedAt': iso(r['last_opened_at']),
                        'openCount': r['open_count'],
                        'itemVersion': r['item_version'],
                        'item': proj,
                        '_sortTs': r['last_opened_at'],
                    }
                else:
                    entry = {
                        'discoveryId': disc_id,
                        'available': False,
                        'openedAt': iso(r['last_opened_at']),
                        'firstOpenedAt': iso(r['first_opened_at']),
                        'lastOpenedAt': iso(r['last_opened_at']),
                        'openCount': r['open_count'],
                        'itemVersion': r['item_version'],
                        'item': None,
                        '_sortTs': r['last_opened_at'],
                    }
                if cursor:
                    c_ts = cursor.get('ts')
                    c_id = cursor.get('id')
                    if (r['last_opened_at'] > c_ts) or (r['last_opened_at'] == c_ts and disc_id >= c_id):
                        continue
                matched.append(entry)
            page = matched[:limit]
            next_cursor = None
            if len(matched) > limit and page:
                last = page[-1]
                next_cursor = encode_cursor({'s': scope, 'ts': last['_sortTs'], 'id': last['discoveryId']})
            for it in page:
                it.pop('_sortTs', None)
            return {
                'items': page,
                'historyGeneration': gen,
                'totalOpened': len(rows),
                'territoriesExplored': len(categories_explored),
                'territoriesTotal': len(INTERESTS),
                'categoriesExploredCount': len(categories_explored),
                'categoriesExplored': sorted(categories_explored),
                'nextCursor': next_cursor,
            }

    def record_exploration_event(self, identity, body):
        """Record confirmed content opening. Never awards KP or claims full reading."""
        reject_authority_fields(body)
        if not isinstance(body, dict) or set(body.keys()) - {'discoveryId', 'eventType', 'eventId', 'historyGeneration', 'itemVersion'}:
            reject('invalid_fields', 'Campos inválidos para evento de exploração.', 422)
        disc_id = validate_discovery_id(body.get('discoveryId'))
        event_type = body.get('eventType', 'open')
        if event_type != 'open':
            reject('invalid_event_type', 'Apenas eventos de abertura confirmada (open) são aceitos.', 422)
        req_gen = body.get('historyGeneration')
        if type(req_gen) is not int or req_gen < 1:
            reject('invalid_generation', 'historyGeneration inválido.', 422)
        req_item_ver = parse_item_version(body.get('itemVersion'))
        raw_event_id = body.get('eventId')
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            state = self._ensure_collection_state(db, member['id'])
            current_gen = state['exploration_generation']
            if req_gen != current_gen:
                reject('stale_exploration_event', 'Este evento pertence a um histórico já limpo.', 409)
            entitlements = self._active_entitlements(db, member['id'])
            proj = self._accessible_item(db, member['id'], disc_id, entitlements)
            if proj is None:
                reject('content_unavailable', 'Esta descoberta não está disponível agora.', 404)
            if raw_event_id is not None:
                if not isinstance(raw_event_id, str) or not 8 <= len(raw_event_id.strip()) <= 128 or not SAFE_ID_RE.fullmatch(raw_event_id.strip()):
                    reject('invalid_event_id', 'Identificador de evento inválido.', 422)
                event_id = raw_event_id.strip()
            else:
                ver_token = str(body.get('itemVersion') or 'v1')
                event_id = f'open:{disc_id}:{ver_token}:g{current_gen}'
            already = db.execute(
                'SELECT created_at FROM member_exploration_events WHERE account_id=? AND event_id=?',
                (member['id'], event_id),
            ).fetchone()
            now = self.clock()
            if already:
                row = db.execute(
                    'SELECT first_opened_at,last_opened_at,open_count,item_version FROM member_exploration WHERE account_id=? AND discovery_id=?',
                    (member['id'], disc_id),
                ).fetchone()
                return {
                    'recorded': True,
                    'duplicate': True,
                    'deduplicated': True,
                    'discoveryId': disc_id,
                    'historyGeneration': current_gen,
                    'firstOpenedAt': iso(row['first_opened_at']) if row else iso(already['created_at']),
                    'lastOpenedAt': iso(row['last_opened_at']) if row else iso(already['created_at']),
                    'openCount': row['open_count'] if row else 1,
                    'kpAwarded': 0,
                    'awardedKP': 0,
                }
            tombstone = db.execute(
                'SELECT item_version,removed_at FROM member_exploration_tombstones WHERE account_id=? AND discovery_id=?',
                (member['id'], disc_id),
            ).fetchone()
            if tombstone and req_item_ver is not None and req_item_ver <= tombstone['item_version']:
                reject('stale_exploration_event', 'Evento anterior à remoção deste item do histórico.', 409)
            db.execute(
                'INSERT INTO member_exploration_events(account_id,event_id,discovery_id,history_generation,created_at) VALUES(?,?,?,?,?)',
                (member['id'], event_id, disc_id, current_gen, now),
            )
            existing = db.execute(
                'SELECT first_opened_at,last_opened_at,open_count,item_version FROM member_exploration WHERE account_id=? AND discovery_id=?',
                (member['id'], disc_id),
            ).fetchone()
            next_item_ver = (tombstone['item_version'] + 1) if tombstone else (req_item_ver or 1)
            if existing:
                first_ts = existing['first_opened_at']
                open_count = existing['open_count'] + 1
                item_ver = max(existing['item_version'], next_item_ver)
                db.execute(
                    'UPDATE member_exploration SET last_opened_at=?,open_count=?,generation=?,item_version=? WHERE account_id=? AND discovery_id=?',
                    (now, open_count, current_gen, item_ver, member['id'], disc_id),
                )
            else:
                first_ts = now
                open_count = 1
                item_ver = next_item_ver
                db.execute(
                    'INSERT INTO member_exploration(account_id,discovery_id,first_opened_at,last_opened_at,open_count,generation,item_version) VALUES(?,?,?,?,?,?,?)',
                    (member['id'], disc_id, first_ts, now, open_count, current_gen, item_ver),
                )
            db.execute('UPDATE member_collection_state SET updated_at=? WHERE account_id=?', (now, member['id']))
            self._sync_legacy_mirror(db, member['id'])
            return {
                'recorded': True,
                'duplicate': False,
                'deduplicated': False,
                'discoveryId': disc_id,
                'historyGeneration': current_gen,
                'itemVersion': item_ver,
                'firstOpenedAt': iso(first_ts),
                'lastOpenedAt': iso(now),
                'openCount': open_count,
                'kpAwarded': 0,
                'awardedKP': 0,
            }

    def delete_exploration_item(self, identity, discovery_id):
        disc_id = validate_discovery_id(discovery_id)
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            state = self._ensure_collection_state(db, member['id'])
            gen = state['exploration_generation'] + 1
            existing = db.execute(
                'SELECT item_version FROM member_exploration WHERE account_id=? AND discovery_id=?',
                (member['id'], disc_id),
            ).fetchone()
            tombstone = db.execute(
                'SELECT item_version FROM member_exploration_tombstones WHERE account_id=? AND discovery_id=?',
                (member['id'], disc_id),
            ).fetchone()
            now = self.clock()
            ver = max(existing['item_version'] if existing else 1, (tombstone['item_version'] + 1) if tombstone else 1)
            if existing:
                db.execute('DELETE FROM member_exploration WHERE account_id=? AND discovery_id=?', (member['id'], disc_id))
            if tombstone:
                db.execute(
                    'UPDATE member_exploration_tombstones SET removed_at=?,removed_generation=?,item_version=? WHERE account_id=? AND discovery_id=?',
                    (now, gen, ver, member['id'], disc_id),
                )
            else:
                db.execute(
                    'INSERT INTO member_exploration_tombstones(account_id,discovery_id,removed_at,removed_generation,item_version) VALUES(?,?,?,?,?)',
                    (member['id'], disc_id, now, gen, ver),
                )
            db.execute('UPDATE member_collection_state SET exploration_generation=?,updated_at=? WHERE account_id=?', (gen, now, member['id']))
            self._sync_legacy_mirror(db, member['id'])
            return {
                'discoveryId': disc_id,
                'removed': bool(existing),
                'historyGeneration': gen,
                'itemVersion': ver,
            }

    def clear_exploration(self, identity, body=None):
        body = {} if body is None else body
        reject_authority_fields(body)
        if not isinstance(body, dict) or set(body.keys()) - {'confirm', 'expectedGeneration'}:
            reject('invalid_fields', 'Campos inválidos para limpar exploração.', 422)
        if body.get('confirm') is not True:
            reject('confirmation_required', 'Confirme a limpeza do histórico de exploração.', 422)
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            state = self._ensure_collection_state(db, member['id'])
            expected_gen = body.get('expectedGeneration')
            if expected_gen is not None and expected_gen != state['exploration_generation']:
                reject('generation_conflict', 'Seu histórico de exploração já foi atualizado em outra sessão.', 409)
            now = self.clock()
            new_gen = state['exploration_generation'] + 1
            db.execute('DELETE FROM member_exploration WHERE account_id=?', (member['id'],))
            db.execute('DELETE FROM member_exploration_tombstones WHERE account_id=?', (member['id'],))
            db.execute(
                'UPDATE member_collection_state SET exploration_generation=?,updated_at=? WHERE account_id=?',
                (new_gen, now, member['id']),
            )
            self._sync_legacy_mirror(db, member['id'])
            return {
                'cleared': True,
                'historyGeneration': new_gen,
                'clearedAt': iso(now),
            }

    # -------------------------------------------------------------------------
    # Missions & Authoritative Wallet / Ledger
    # -------------------------------------------------------------------------
    def _release_expired_pending_claims(self, db, account_id=None):
        """Durable opportunistic release of expired pending claims (single-release guarantee)."""
        now = self.clock()
        where = "WHERE reservation_state='reserved' AND expires_at<=?"
        params = [now]
        if account_id:
            where += ' AND account_id=?'
            params.append(account_id)
        expired_rows = db.execute(
            f'SELECT id,attempt_id,campaign_id,award_kp FROM mission_pending_claims {where}',
            tuple(params),
        ).fetchall()
        released_count = 0
        for row in expired_rows:
            cur = db.execute(
                "UPDATE mission_pending_claims SET reservation_state='released',released_at=? WHERE id=? AND reservation_state='reserved'",
                (now, row['id']),
            )
            if getattr(cur, 'rowcount', 1) == 1:
                db.execute(
                    'UPDATE mission_campaigns SET reserved_kp = CASE WHEN reserved_kp >= ? THEN reserved_kp - ? ELSE 0 END WHERE id=?',
                    (row['award_kp'], row['award_kp'], row['campaign_id']),
                )
                db.execute(
                    "UPDATE mission_attempts SET state='expired',result_code='claim_expired' WHERE id=? AND state='submitted'",
                    (row['attempt_id'],),
                )
                released_count += 1
        return released_count

    def _get_or_create_campaign(self, db, mission):
        camp_id = mission['coverage_reference'].strip()
        row = db.execute('SELECT * FROM mission_campaigns WHERE id=?', (camp_id,)).fetchone()
        if row:
            return row
        # Funding is provisioned by a trusted operator, never inferred from a
        # mission or minted by a runtime default when a campaign is missing.
        reject('reward_capacity', 'Esta missão ainda não está disponível.', 409)

    def _mission_meta(self, mission):
        try:
            data = json.loads(mission['definition_json'])
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
        occurrence = str(data.get('occurrenceKey') or mission['id'])
        max_attempts = int(data.get('maxAttempts', 3))
        cooldown_sec = int(data.get('cooldownSeconds', 0))
        return data, occurrence, max(1, max_attempts), max(0, cooldown_sec)

    def get_wallet(self, identity):
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            self._release_expired_pending_claims(db, member['id'])
            p_state = self.program_state()
            wallet = db.execute('SELECT available,reserved FROM wallets WHERE account_id=?', (member['id'],)).fetchone()
            earned_row = db.execute(
                'SELECT COALESCE(SUM(CASE WHEN available_delta>0 THEN available_delta ELSE 0 END),0) AS earned FROM ledger WHERE account_id=?',
                (member['id'],),
            ).fetchone()
            lifetime_earned = int(earned_row['earned'] or 0)
            pending_rows = db.execute(
                "SELECT id,mission_id,mission_version,attempt_id,award_kp,expires_at,created_at FROM mission_pending_claims "
                "WHERE account_id=? AND reservation_state='reserved' AND expires_at>? ORDER BY created_at DESC",
                (member['id'], self.clock()),
            ).fetchall()
            pending_items = [
                {
                    'pendingId': r['id'],
                    'pendingToken': r['id'],
                    'attemptId': r['attempt_id'],
                    'missionId': r['mission_id'],
                    'missionVersion': r['mission_version'],
                    'awardKP': r['award_kp'],
                    'awardPreview': r['award_kp'],
                    'expiresAt': iso(r['expires_at']),
                    'createdAt': iso(r['created_at']),
                }
                for r in pending_rows
            ]
            recent_ledger = db.page(
                'SELECT id,available_delta,reserved_delta,reason,reference_id,created_at FROM ledger WHERE account_id=? ORDER BY created_at DESC, id DESC',
                (member['id'],),
                20,
            ).fetchall()
            entries = [
                {
                    'id': r['id'],
                    'availableDelta': r['available_delta'],
                    'reservedDelta': r['reserved_delta'],
                    'reason': r['reason'],
                    'referenceId': r['reference_id'],
                    'createdAt': iso(r['created_at']),
                }
                for r in recent_ledger
            ]
            last_ledger = recent_ledger[0] if recent_ledger else None
            version_str = f"{wallet['available']}:{wallet['reserved']}:{len(pending_items)}:{last_ledger['id'] if last_ledger else '0'}"
            return {
                'available': wallet['available'],
                'reserved': wallet['reserved'],
                'lifetimeEarned': lifetime_earned,
                'pendingConfirmationKP': sum(r['award_kp'] for r in pending_rows),
                'pendingClaims': pending_items,
                'entries': entries,
                'unit': 'KP',
                'programState': p_state,
                'programStatus': p_state,
                'rewardsEnabled': p_state in {'active', 'new_activity_paused'},
                'asOf': iso(self.clock()),
                'version': security.token_hash(version_str)[:16],
            }

    def get_ledger(self, identity, query=None):
        query = query or {}
        limit = parse_limit(query, default=25, maximum=100)
        reason_filter = query.get('reason', '').strip()
        if reason_filter and not SAFE_ID_RE.fullmatch(reason_filter):
            reject('invalid_reason', 'Filtro de motivo inválido.', 422)
        scope = f'ledger:{reason_filter}'
        cursor = decode_cursor(query.get('cursor'), expected_scope=scope)
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            self._release_expired_pending_claims(db, member['id'])
            params = [member['id']]
            where = ''
            if reason_filter:
                where += ' AND l.reason=?'
                params.append(reason_filter)
            if cursor:
                c_ts = int(cursor['ts'])
                c_id = str(cursor['id'])
                where += ' AND (l.created_at<? OR (l.created_at=? AND l.id<?))'
                params.extend([c_ts, c_ts, c_id])
            rows = db.page(
                'SELECT l.id,l.available_delta,l.reserved_delta,l.reason,l.reference_id,l.created_at,'
                'r.mission_id,r.mission_version,r.support_ref '
                'FROM ledger l LEFT JOIN mission_receipts r ON r.ledger_id=l.id '
                'WHERE l.account_id=?' + where + ' ORDER BY l.created_at DESC, l.id DESC',
                tuple(params),
                limit + 1,
            ).fetchall()
            missions_map = {}
            for m in db.execute('SELECT id,version,definition_json FROM missions').fetchall():
                t_pt, t_en = self.accounts.domain._title(m['definition_json'])
                missions_map[(m['id'], m['version'])] = (t_pt or m['id'], t_en or m['id'])
            page = rows[:limit]
            items = []
            for r in page:
                m_key = (r.get('mission_id'), r.get('mission_version'))
                title_pt, title_en = missions_map.get(m_key, ('Movimentação KP', 'KP activity'))
                items.append({
                    'id': r['id'],
                    'availableDelta': r['available_delta'],
                    'reservedDelta': r['reserved_delta'],
                    'reason': r['reason'],
                    'referenceId': r['reference_id'],
                    'missionId': r.get('mission_id'),
                    'missionVersion': r.get('mission_version'),
                    'titlePT': title_pt,
                    'titleEN': title_en,
                    'supportRef': r.get('support_ref') or f"KP-{r['id'][:8].upper()}",
                    'createdAt': iso(r['created_at']),
                    '_sortTs': r['created_at'],
                })
            next_cursor = None
            if len(rows) > limit and items:
                last = items[-1]
                next_cursor = encode_cursor({'s': scope, 'ts': last['_sortTs'], 'id': last['id']})
            for it in items:
                it.pop('_sortTs', None)
            p_state = self.program_state()
            return {
                'items': items,
                'entries': items,
                'programState': p_state,
                'programStatus': p_state,
                'nextCursor': next_cursor,
            }

    def list_missions(self, identity):
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            self._release_expired_pending_claims(db, member['id'])
            p_state = self.program_state()
            if p_state == 'disabled':
                return {
                    'programState': 'disabled',
                    'programStatus': 'disabled',
                    'rewardsEnabled': False,
                    'items': [],
                    'nextCursor': None,
                }
            now = self.clock()
            rows = db.execute(
                "SELECT * FROM missions WHERE active=1 AND starts_at<=? AND ends_at>? AND coverage_reference<>'' ORDER BY id,version",
                (now, now),
            ).fetchall()
            items = []
            for m in rows:
                defn, occ_key, max_attempts, cooldown = self._mission_meta(m)
                campaign = self._get_or_create_campaign(db, m)
                receipt = db.execute(
                    'SELECT id,award_kp,support_ref,created_at FROM mission_receipts WHERE account_id=? AND mission_id=? AND occurrence_key=?',
                    (member['id'], m['id'], occ_key),
                ).fetchone()
                pending = db.execute(
                    "SELECT id,attempt_id,award_kp,expires_at FROM mission_pending_claims WHERE account_id=? AND mission_id=? AND occurrence_key=? AND reservation_state='reserved' AND expires_at>?",
                    (member['id'], m['id'], occ_key, now),
                ).fetchone()
                attempts = db.execute(
                    'SELECT id,state,attempt_number,expires_at,submitted_at,result_code,created_at FROM mission_attempts WHERE account_id=? AND mission_id=? AND occurrence_key=? ORDER BY attempt_number DESC',
                    (member['id'], m['id'], occ_key),
                ).fetchall()
                active_attempt = next((a for a in attempts if a['state'] == 'active' and a['expires_at'] > now), None)
                used_attempts = len([a for a in attempts if a['state'] in ('submitted', 'failed', 'expired', 'completed')])
                remaining_budget = campaign['total_budget_kp'] - campaign['reserved_kp'] - campaign['consumed_kp']
                if receipt:
                    member_status = 'completed'
                elif pending:
                    member_status = 'pending_claim'
                elif active_attempt:
                    member_status = 'in_progress'
                elif p_state in ('new_activity_paused', 'maintenance', 'closed') or campaign['state'] in ('new_activity_paused', 'maintenance', 'closed', 'draft'):
                    member_status = 'paused'
                elif remaining_budget < m['award']:
                    member_status = 'coverage_exhausted'
                elif used_attempts >= max_attempts:
                    member_status = 'attempts_exhausted'
                else:
                    member_status = 'available'
                items.append({
                    'id': m['id'],
                    'version': m['version'],
                    'occurrenceKey': occ_key,
                    'kind': m['verifier'],
                    'awardKP': m['award'],
                    'titlePT': defn.get('titlePT', m['id']),
                    'titleEN': defn.get('titleEN', m['id']),
                    'summaryPT': defn.get('summaryPT', ''),
                    'summaryEN': defn.get('summaryEN', ''),
                    'rulesPT': defn.get('rulesPT', []),
                    'rulesEN': defn.get('rulesEN', []),
                    'discoveryId': defn.get('discoveryId'),
                    'startsAt': iso(m['starts_at']),
                    'endsAt': iso(m['ends_at']),
                    'maxAttempts': max_attempts,
                    'usedAttempts': used_attempts,
                    'memberStatus': member_status,
                    'completed': bool(receipt),
                    'activeAttemptId': active_attempt['id'] if active_attempt else None,
                    'activeAttemptExpiresAt': iso(active_attempt['expires_at']) if active_attempt else None,
                    'activeAttempt': {
                        'attemptId': active_attempt['id'],
                        'challengeId': active_attempt['id'],
                        'status': 'issued',
                        'expiresAt': iso(active_attempt['expires_at']),
                    } if active_attempt else None,
                    'pendingClaim': {
                        'pendingId': pending['id'],
                        'pendingToken': pending['id'],
                        'attemptId': pending['attempt_id'],
                        'awardKP': pending['award_kp'],
                        'awardPreview': pending['award_kp'],
                        'expiresAt': iso(pending['expires_at']),
                        'status': 'reserved',
                    } if pending else None,
                    'receipt': {
                        'receiptId': receipt['id'],
                        'awardKP': receipt['award_kp'],
                        'awardedKP': receipt['award_kp'],
                        'supportRef': receipt['support_ref'],
                        'completedAt': iso(receipt['created_at']),
                    } if receipt else None,
                })
            return {
                'programState': p_state,
                'programStatus': p_state,
                'rewardsEnabled': p_state in {'active', 'new_activity_paused'},
                'items': items,
                'nextCursor': None,
            }

    def _check_idempotent_replay(self, db, account_id, op_type, idem_key, payload_hash):
        row = db.execute(
            'SELECT operation_id,payload_hash,status_code,response_json FROM idempotent_operations WHERE account_id=? AND operation_type=? AND idempotency_key=?',
            (account_id, op_type, idem_key),
        ).fetchone()
        if not row:
            return None
        if not security.equal(row['payload_hash'], payload_hash):
            reject('idempotency_conflict', 'Chave de idempotência já utilizada com parâmetros diferentes.', 409)
        return json.loads(row['response_json'])

    def _save_idempotent_operation(self, db, account_id, op_type, idem_key, payload_hash, response_body, status_code=200):
        op_id = response_body.get('operationId') or identifier()
        response_body['operationId'] = op_id
        db.execute(
            'INSERT INTO idempotent_operations(account_id,operation_type,idempotency_key,operation_id,payload_hash,status_code,response_json,created_at) VALUES(?,?,?,?,?,?,?,?)',
            (account_id, op_type, idem_key, op_id, payload_hash, status_code, json.dumps(response_body), self.clock()),
        )
        return response_body

    def start_challenge(self, identity, body, headers=None):
        reject_authority_fields(body)
        if not isinstance(body, dict) or set(body.keys()) - {'missionId', 'missionVersion'}:
            reject('invalid_fields', 'Campos inválidos para iniciar missão.', 422)
        mission_id = body.get('missionId')
        mission_version = body.get('missionVersion')
        if not isinstance(mission_id, str) or not SAFE_ID_RE.fullmatch(mission_id) or type(mission_version) is not int or mission_version < 1:
            reject('invalid_mission', 'Missão inválida.', 422)
        idem_key = validate_idempotency_key((headers or {}).get('idempotency-key'), required=False)
        payload_hash = security.token_hash(json.dumps(['challenge', mission_id, mission_version], separators=(',', ':')))
        subj = identity if isinstance(identity, str) else (identity.subject if identity else 'anon')
        self.accounts.domain.rate('member_challenge', subj, 25)
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            self._release_expired_pending_claims(db, member['id'])
            if idem_key:
                replay = self._check_idempotent_replay(db, member['id'], 'challenge', idem_key, payload_hash)
                if replay is not None:
                    return replay
            p_state = self.program_state()
            if p_state == 'disabled':
                reject('rewards_unavailable', 'Karaca Points ainda não está liberado.', 503)
            if p_state == 'maintenance':
                reject('program_maintenance', 'Missões temporariamente em manutenção.', 503)
            if p_state in ('new_activity_paused', 'closed'):
                reject('program_paused', 'Esta missão está em pausa para novas participações.', 409)
            mission = self.accounts.domain._mission(db, mission_id, mission_version)
            defn = self.accounts.domain._definition(mission)
            _, occ_key, max_attempts, cooldown = self._mission_meta(mission)
            campaign = self._get_or_create_campaign(db, mission)
            if campaign['state'] in ('draft', 'new_activity_paused', 'closed'):
                reject('program_paused', 'Esta missão está em pausa.', 409)
            if campaign['state'] == 'maintenance':
                reject('program_maintenance', 'Missão em manutenção temporária.', 503)
            now = self.clock()
            existing_receipt = db.execute(
                'SELECT id FROM mission_receipts WHERE account_id=? AND mission_id=? AND occurrence_key=?',
                (member['id'], mission_id, occ_key),
            ).fetchone()
            if existing_receipt:
                reject('award_already', 'Esta missão já rendeu seus KP.', 409)
            existing_pending = db.execute(
                "SELECT id FROM mission_pending_claims WHERE account_id=? AND mission_id=? AND occurrence_key=? AND reservation_state='reserved' AND expires_at>?",
                (member['id'], mission_id, occ_key, now),
            ).fetchone()
            if existing_pending:
                reject('award_pending', 'Missão já validada. Confirme seus KP pendentes.', 409)
            active_attempt = db.execute(
                "SELECT * FROM mission_attempts WHERE account_id=? AND mission_id=? AND occurrence_key=? AND state='active' AND expires_at>? ORDER BY attempt_number DESC",
                (member['id'], mission_id, occ_key, now),
            ).fetchone()
            if active_attempt:
                result = self._format_attempt_response(active_attempt, mission, defn)
                if idem_key:
                    self._save_idempotent_operation(db, member['id'], 'challenge', idem_key, payload_hash, result)
                return result
            remaining_global = campaign['total_budget_kp'] - campaign['reserved_kp'] - campaign['consumed_kp']
            if remaining_global < mission['award']:
                reject('reward_capacity', 'Cobertura de KP esgotada para esta missão.', 409)
            account_used = self._account_campaign_kp(db, member['id'], campaign['id'], now)
            if account_used + mission['award'] > campaign['per_account_limit_kp']:
                reject('mission_ineligible', 'Limite de KP desta campanha atingido para sua conta.', 403)
            db.execute(
                "UPDATE mission_attempts SET state='expired',result_code='mission_expired' WHERE account_id=? AND mission_id=? AND occurrence_key=? AND state='active' AND expires_at<=?",
                (member['id'], mission_id, occ_key, now),
            )
            past_attempts = db.execute(
                'SELECT attempt_number,submitted_at,created_at,state FROM mission_attempts WHERE account_id=? AND mission_id=? AND occurrence_key=? ORDER BY attempt_number DESC',
                (member['id'], mission_id, occ_key),
            ).fetchall()
            if len(past_attempts) >= max_attempts:
                reject('mission_ineligible', 'Limite de tentativas atingido para esta missão.', 403)
            if past_attempts and cooldown > 0:
                last_ts = past_attempts[0]['submitted_at'] or past_attempts[0]['created_at']
                if now - last_ts < cooldown:
                    reject('mission_cooldown', 'Aguarde o intervalo antes de iniciar nova tentativa.', 429)
            attempt_id = identifier()
            attempt_num = (past_attempts[0]['attempt_number'] + 1) if past_attempts else 1
            expires_at = min(now + 1800, mission['ends_at'])
            def_hash = security.token_hash(mission['definition_json'])
            db.execute(
                'INSERT INTO challenges(id,browser_hash,account_id,mission_id,mission_version,definition_hash,expires_at) VALUES(?,?,?,?,?,?,?)',
                (attempt_id, security.token_hash(member['id']), member['id'], mission_id, mission_version, def_hash, expires_at),
            )
            db.execute(
                'INSERT INTO mission_attempts(id,account_id,mission_id,mission_version,occurrence_key,campaign_id,definition_hash,award_kp,state,attempt_number,expires_at,created_at) '
                'VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                (attempt_id, member['id'], mission_id, mission_version, occ_key, campaign['id'], def_hash, mission['award'], 'active', attempt_num, expires_at, now),
            )
            attempt_row = db.execute('SELECT * FROM mission_attempts WHERE id=?', (attempt_id,)).fetchone()
            result = self._format_attempt_response(attempt_row, mission, defn)
            if idem_key:
                self._save_idempotent_operation(db, member['id'], 'challenge', idem_key, payload_hash, result)
            return result

    def _account_campaign_kp(self, db, account_id, campaign_id, now):
        reserved = db.execute(
            "SELECT COALESCE(SUM(award_kp),0) AS amount FROM mission_pending_claims WHERE account_id=? AND campaign_id=? AND reservation_state IN ('reserved','consumed')",
            (account_id, campaign_id),
        ).fetchone()['amount']
        return int(reserved or 0)

    def _format_attempt_response(self, attempt_row, mission, defn, pending_row=None, receipt_row=None):
        questions = [
            {k: q[k] for k in ('id', 'promptPT', 'promptEN', 'options')}
            for q in defn.get('questions', [])
        ]
        state_val = attempt_row['state']
        status_alias = 'issued' if state_val == 'active' else state_val
        return {
            'attemptId': attempt_row['id'],
            'challengeId': attempt_row['id'],
            'missionId': attempt_row['mission_id'],
            'missionVersion': attempt_row['mission_version'],
            'occurrenceKey': attempt_row['occurrence_key'],
            'kind': mission['verifier'],
            'awardKP': attempt_row['award_kp'],
            'state': state_val,
            'status': status_alias,
            'attemptNumber': attempt_row['attempt_number'],
            'expiresAt': iso(attempt_row['expires_at']),
            'titlePT': defn.get('titlePT', attempt_row['mission_id']),
            'titleEN': defn.get('titleEN', attempt_row['mission_id']),
            'questions': questions,
            'resultCode': attempt_row['result_code'],
            'pendingClaim': {
                'pendingId': pending_row['id'],
                'pendingToken': pending_row['id'],
                'awardKP': pending_row['award_kp'],
                'awardPreview': pending_row['award_kp'],
                'expiresAt': iso(pending_row['expires_at']),
                'reservationState': pending_row['reservation_state'],
            } if pending_row else None,
            'receipt': {
                'receiptId': receipt_row['id'],
                'completionId': receipt_row['completion_id'],
                'awardKP': receipt_row['award_kp'],
                'awardedKP': receipt_row['award_kp'],
                'supportRef': receipt_row['support_ref'],
                'completedAt': iso(receipt_row['created_at']),
            } if receipt_row else None,
        }

    def get_challenge(self, identity, attempt_id):
        if not isinstance(attempt_id, str) or not SAFE_ID_RE.fullmatch(attempt_id):
            reject('not_found', 'Tentativa não encontrada.', 404)
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            self._release_expired_pending_claims(db, member['id'])
            now = self.clock()
            attempt = db.execute('SELECT * FROM mission_attempts WHERE id=?', (attempt_id,)).fetchone()
            if not attempt or attempt['account_id'] != member['id']:
                reject('not_found', 'Tentativa não encontrada.', 404)
            if attempt['state'] == 'active' and attempt['expires_at'] <= now:
                db.execute("UPDATE mission_attempts SET state='expired',result_code='mission_expired' WHERE id=?", (attempt_id,))
                attempt = db.execute('SELECT * FROM mission_attempts WHERE id=?', (attempt_id,)).fetchone()
            mission = db.execute('SELECT * FROM missions WHERE id=? AND version=?', (attempt['mission_id'], attempt['mission_version'])).fetchone()
            defn = self.accounts.domain._definition(mission) if mission else {'titlePT': attempt['mission_id'], 'titleEN': attempt['mission_id'], 'questions': []}
            pending = db.execute('SELECT * FROM mission_pending_claims WHERE attempt_id=?', (attempt_id,)).fetchone()
            receipt = db.execute('SELECT * FROM mission_receipts WHERE attempt_id=?', (attempt_id,)).fetchone()
            return self._format_attempt_response(attempt, mission or {'verifier': 'quiz'}, defn, pending, receipt)

    def submit_evidence(self, identity, body, headers=None):
        result = self._submit_evidence_transaction(identity, body, headers)
        if isinstance(result, Rejected):
            raise result
        return result

    def _submit_evidence_transaction(self, identity, body, headers=None):
        reject_authority_fields(body)
        if not isinstance(body, dict) or set(body.keys()) - {'attemptId', 'challengeId', 'answers', 'interests'}:
            reject('invalid_fields', 'Campos inválidos para envio de evidência.', 422)
        attempt_id = body.get('attemptId') or body.get('challengeId')
        if not isinstance(attempt_id, str) or not SAFE_ID_RE.fullmatch(attempt_id):
            reject('invalid_attempt', 'Tentativa inválida.', 422)
        idem_key = validate_idempotency_key((headers or {}).get('idempotency-key'), required=False)
        payload_hash = security.token_hash(json.dumps(['evidence', attempt_id, body.get('answers'), body.get('interests')], sort_keys=True, separators=(',', ':')))
        subj = identity if isinstance(identity, str) else (identity.subject if identity else 'anon')
        self.accounts.domain.rate('member_evidence', subj, 20)
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            self._release_expired_pending_claims(db, member['id'])
            if idem_key:
                replay = self._check_idempotent_replay(db, member['id'], 'evidence', idem_key, payload_hash)
                if replay is not None:
                    return replay
            p_state = self.program_state()
            if p_state == 'disabled':
                reject('rewards_unavailable', 'Karaca Points ainda não está liberado.', 503)
            if p_state == 'maintenance':
                reject('program_maintenance', 'Missões temporariamente em manutenção.', 503)
            if p_state in ('new_activity_paused', 'closed'):
                reject('program_paused', 'Esta missão está em pausa para novas participações.', 409)
            now = self.clock()
            attempt = db.execute('SELECT * FROM mission_attempts WHERE id=?', (attempt_id,)).fetchone()
            if not attempt or attempt['account_id'] != member['id']:
                reject('not_found', 'Tentativa não encontrada.', 404)
            if attempt['state'] in ('submitted', 'completed'):
                pending = db.execute('SELECT * FROM mission_pending_claims WHERE attempt_id=?', (attempt_id,)).fetchone()
                if pending:
                    res = {
                        'attemptId': attempt_id,
                        'pendingId': pending['id'],
                        'pendingToken': pending['id'],
                        'evidenceRef': pending['evidence_id'],
                        'awardPreview': pending['award_kp'],
                        'expiresAt': iso(pending['expires_at']),
                        'state': attempt['state'],
                    }
                    if idem_key:
                        self._save_idempotent_operation(db, member['id'], 'evidence', idem_key, payload_hash, res)
                    return res
                reject('challenge_used', 'Esta tentativa já foi concluída.', 409)
            if attempt['state'] == 'failed':
                reject('challenge_used', 'Esta tentativa já foi encerrada. Inicie outra se disponível.', 409)
            if attempt['state'] == 'expired' or attempt['expires_at'] <= now:
                db.execute("UPDATE mission_attempts SET state='expired',result_code='mission_expired' WHERE id=?", (attempt_id,))
                reject('mission_expired', 'O tempo desta tentativa terminou.', 410)
            mission = self.accounts.domain._mission(db, attempt['mission_id'], attempt['mission_version'])
            if not security.equal(attempt['definition_hash'], security.token_hash(mission['definition_json'])):
                db.execute("UPDATE mission_attempts SET state='expired',result_code='mission_changed' WHERE id=?", (attempt_id,))
                reject('mission_changed', 'A regra desta missão foi atualizada. Inicie uma nova tentativa.', 409)
            campaign = self._get_or_create_campaign(db, mission)
            if campaign['state'] in ('draft', 'new_activity_paused', 'closed'):
                reject('program_paused', 'Esta missão está em pausa.', 409)
            if campaign['state'] == 'maintenance':
                reject('program_maintenance', 'Missão em manutenção temporária.', 503)
            try:
                validated = self.accounts.domain._answers(mission, body)
            except Rejected as err:
                if err.code == 'evidence_invalid':
                    db.execute(
                        "UPDATE mission_attempts SET state='failed',submitted_at=?,result_code='mission_try_again' WHERE id=?",
                        (now, attempt_id),
                    )
                    db.execute('UPDATE challenges SET used_at=? WHERE id=?', (now, attempt_id))
                    # Commit failed state; raising here would roll it back.
                    return err
                raise
            account_used = self._account_campaign_kp(db, member['id'], campaign['id'], now)
            if account_used + attempt['award_kp'] > campaign['per_account_limit_kp']:
                reject('mission_ineligible', 'Limite de KP desta campanha atingido para sua conta.', 403)
            res_cur = db.execute(
                "UPDATE mission_campaigns SET reserved_kp = reserved_kp + ? "
                "WHERE id=? AND state='active' AND reserved_kp + consumed_kp + ? <= total_budget_kp",
                (attempt['award_kp'], campaign['id'], attempt['award_kp']),
            )
            if getattr(res_cur, 'rowcount', 1) != 1:
                reject('reward_capacity', 'Cobertura de KP esgotada para esta campanha; nenhuma promessa foi gerada.', 409)
            evidence_id = identifier()
            pending_id = identifier()
            claim_expires = min(now + 1800, mission['ends_at'])
            db.execute('UPDATE challenges SET used_at=? WHERE id=?', (now, attempt_id))
            db.execute(
                'INSERT INTO mission_evidence(id,challenge_id,browser_hash,account_id,mission_id,mission_version,payload,created_at) VALUES(?,?,?,?,?,?,?,?)',
                (evidence_id, attempt_id, security.token_hash(member['id']), member['id'], mission['id'], mission['version'], json.dumps(validated), now),
            )
            db.execute(
                "INSERT INTO mission_pending_claims(id,account_id,attempt_id,mission_id,mission_version,occurrence_key,campaign_id,evidence_id,award_kp,reservation_state,expires_at,created_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,'reserved',?,?)",
                (pending_id, member['id'], attempt_id, mission['id'], mission['version'], attempt['occurrence_key'], campaign['id'], evidence_id, attempt['award_kp'], claim_expires, now),
            )
            db.execute(
                "UPDATE mission_attempts SET state='submitted',submitted_at=?,result_code='award_pending',pending_id=? WHERE id=?",
                (now, pending_id, attempt_id),
            )
            result = {
                'attemptId': attempt_id,
                'pendingId': pending_id,
                'pendingToken': pending_id,
                'evidenceRef': evidence_id,
                'awardPreview': attempt['award_kp'],
                'expiresAt': iso(claim_expires),
                'state': 'submitted',
            }
            if idem_key:
                self._save_idempotent_operation(db, member['id'], 'evidence', idem_key, payload_hash, result)
            return result

    def claim_pending(self, identity, body, headers=None, fail_after_step=None):
        """Atomic consumption of covered pending claim -> completion + ledger + wallet + receipt."""
        reject_authority_fields(body)
        if not isinstance(body, dict) or set(body.keys()) - {'pendingId', 'attemptId', 'pendingToken'}:
            reject('invalid_fields', 'Campos inválidos para confirmação de KP.', 422)
        pending_id = body.get('pendingId') or body.get('pendingToken')
        attempt_id = body.get('attemptId')
        if not pending_id and not attempt_id:
            reject('invalid_pending', 'Informe pendingId ou attemptId.', 422)
        if pending_id is not None and (not isinstance(pending_id, str) or not SAFE_ID_RE.fullmatch(pending_id)):
            reject('invalid_pending', 'Identificador de pendência inválido.', 422)
        if attempt_id is not None and (not isinstance(attempt_id, str) or not SAFE_ID_RE.fullmatch(attempt_id)):
            reject('invalid_attempt', 'Identificador de tentativa inválido.', 422)
        raw_idem = headers if isinstance(headers, str) else (headers or {}).get('idempotency-key')
        idem_key = validate_idempotency_key(raw_idem, required=True)
        payload_hash = security.token_hash(json.dumps(['claim', pending_id, attempt_id], separators=(',', ':')))
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            replay = self._check_idempotent_replay(db, member['id'], 'claim', idem_key, payload_hash)
            if replay is not None:
                return replay
            p_state = self.program_state()
            if p_state == 'disabled':
                reject('rewards_unavailable', 'Karaca Points ainda não está liberado.', 503)
            if p_state == 'maintenance':
                reject('program_maintenance', 'Confirmação de KP temporariamente em manutenção.', 503)
            if p_state == 'closed':
                reject('program_closed', 'Ciclo de Karaca Points encerrado.', 409)
            now = self.clock()
            if pending_id:
                pending = db.execute('SELECT * FROM mission_pending_claims WHERE id=?', (pending_id,)).fetchone()
            else:
                pending = db.execute('SELECT * FROM mission_pending_claims WHERE attempt_id=?', (attempt_id,)).fetchone()
            if not pending or pending['account_id'] != member['id']:
                reject('not_found', 'Pendência de KP não encontrada.', 404)
            existing_receipt = db.execute(
                'SELECT * FROM mission_receipts WHERE account_id=? AND mission_id=? AND occurrence_key=?',
                (member['id'], pending['mission_id'], pending['occurrence_key']),
            ).fetchone()
            if existing_receipt:
                wallet = db.execute('SELECT available,reserved FROM wallets WHERE account_id=?', (member['id'],)).fetchone()
                res = self._format_claim_receipt(existing_receipt, wallet, already_claimed=True)
                self._save_idempotent_operation(db, member['id'], 'claim', idem_key, payload_hash, res)
                return res
            if pending['reservation_state'] == 'released' or pending['expires_at'] <= now:
                self._release_expired_pending_claims(db, member['id'])
                reject('claim_expired', 'O prazo para confirmar estes KP terminou.', 410)
            if pending['reservation_state'] != 'reserved':
                reject('pending_claimed', 'Estes KP já foram processados.', 409)
            mission = db.execute('SELECT * FROM missions WHERE id=? AND version=?', (pending['mission_id'], pending['mission_version'])).fetchone()
            attempt = db.execute('SELECT * FROM mission_attempts WHERE id=?', (pending['attempt_id'],)).fetchone()
            if not mission or not attempt or not security.equal(attempt['definition_hash'], security.token_hash(mission['definition_json'])):
                self._release_expired_pending_claims(db, member['id'])
                reject('mission_changed', 'A regra da missão mudou antes da confirmação.', 409)
            camp_cur = db.execute(
                'UPDATE mission_campaigns SET reserved_kp = reserved_kp - ?, consumed_kp = consumed_kp + ? '
                'WHERE id=? AND reserved_kp >= ? AND reserved_kp + consumed_kp <= total_budget_kp',
                (pending['award_kp'], pending['award_kp'], pending['campaign_id'], pending['award_kp']),
            )
            if getattr(camp_cur, 'rowcount', 1) != 1:
                reject('reward_capacity', 'Reserva de cobertura indisponível.', 409)
            pend_cur = db.execute(
                "UPDATE mission_pending_claims SET reservation_state='consumed',claimed_at=? WHERE id=? AND reservation_state='reserved'",
                (now, pending['id']),
            )
            if getattr(pend_cur, 'rowcount', 1) != 1:
                reject('pending_claimed', 'Pendência já consumida.', 409)
            completion_id = identifier()
            ledger_id = identifier()
            receipt_id = identifier()
            support_ref = f"KP-{receipt_id[:8].upper()}"
            db.execute(
                'INSERT INTO completions(id,account_id,mission_id,mission_version,evidence_ref,created_at) VALUES(?,?,?,?,?,?)',
                (completion_id, member['id'], pending['mission_id'], pending['mission_version'], pending['evidence_id'], now),
            )
            if fail_after_step == 'completion':
                raise RuntimeError('Simulated transactional failure after completion')
            db.execute(
                'INSERT INTO ledger(id,account_id,available_delta,reserved_delta,reason,reference_id,created_at) VALUES(?,?,?,?,?,?,?)',
                (ledger_id, member['id'], pending['award_kp'], 0, 'mission', completion_id, now),
            )
            if fail_after_step == 'ledger':
                raise RuntimeError('Simulated transactional failure after ledger')
            db.execute(
                'UPDATE wallets SET available = available + ? WHERE account_id=?',
                (pending['award_kp'], member['id']),
            )
            db.execute(
                'INSERT INTO mission_receipts(id,account_id,completion_id,ledger_id,pending_id,attempt_id,mission_id,mission_version,occurrence_key,award_kp,support_ref,created_at) '
                'VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                (receipt_id, member['id'], completion_id, ledger_id, pending['id'], pending['attempt_id'], pending['mission_id'], pending['mission_version'], pending['occurrence_key'], pending['award_kp'], support_ref, now),
            )
            db.execute("UPDATE mission_attempts SET state='completed',result_code='award_success',receipt_id=? WHERE id=?", (receipt_id, pending['attempt_id']))
            db.execute('UPDATE mission_pending_claims SET receipt_id=? WHERE id=?', (receipt_id, pending['id']))
            receipt_row = db.execute('SELECT * FROM mission_receipts WHERE id=?', (receipt_id,)).fetchone()
            wallet = db.execute('SELECT available,reserved FROM wallets WHERE account_id=?', (member['id'],)).fetchone()
            res = self._format_claim_receipt(receipt_row, wallet, already_claimed=False)
            self._save_idempotent_operation(db, member['id'], 'claim', idem_key, payload_hash, res)
            return res

    def _format_claim_receipt(self, receipt_row, wallet_row, already_claimed=False):
        receipt_obj = {
            'receiptId': receipt_row['id'],
            'completionId': receipt_row['completion_id'],
            'ledgerId': receipt_row['ledger_id'],
            'pendingId': receipt_row['pending_id'],
            'attemptId': receipt_row['attempt_id'],
            'missionId': receipt_row['mission_id'],
            'missionVersion': receipt_row['mission_version'],
            'occurrenceKey': receipt_row['occurrence_key'],
            'awardKP': receipt_row['award_kp'],
            'awardedKP': receipt_row['award_kp'],
            'supportRef': receipt_row['support_ref'],
            'completedAt': iso(receipt_row['created_at']),
            'alreadyClaimed': already_claimed,
        }
        return {
            **receipt_obj,
            'receipt': receipt_obj,
            'wallet': {
                'available': wallet_row['available'],
                'reserved': wallet_row['reserved'],
                'unit': 'KP',
            },
        }

    def get_operation(self, identity, operation_id):
        if not isinstance(operation_id, str) or not SAFE_ID_RE.fullmatch(operation_id):
            reject('not_found', 'Operação não encontrada.', 404)
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            row = db.execute(
                'SELECT account_id,operation_id,operation_type,status_code,response_json,created_at FROM idempotent_operations WHERE operation_id=?',
                (operation_id,),
            ).fetchone()
            if not row or row['account_id'] != member['id']:
                reject('not_found', 'Operação não encontrada.', 404)
            return {
                'found': True,
                'status': 'completed',
                'operationId': row['operation_id'],
                'operationType': row['operation_type'],
                'createdAt': iso(row['created_at']),
                'result': json.loads(row['response_json']),
            }

    def get_operation_status_by_key(self, identity, query=None, headers=None):
        """Consult operation status by pre-known Idempotency-Key even if operationId never arrived (Test K04)."""
        op_type = (query or {}).get('type', '').strip()
        if op_type not in {'challenge', 'evidence', 'claim'}:
            reject('invalid_operation_type', 'Tipo de operação inválido.', 422)
        idem_key = validate_idempotency_key((headers or {}).get('idempotency-key'), required=True)
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            row = db.execute(
                'SELECT operation_id,operation_type,status_code,response_json,created_at FROM idempotent_operations WHERE account_id=? AND operation_type=? AND idempotency_key=?',
                (member['id'], op_type, idem_key),
            ).fetchone()
            if not row:
                return {
                    'found': False,
                    'status': 'not_started',
                    'operationType': op_type,
                }
            return {
                'found': True,
                'status': 'completed',
                'operationId': row['operation_id'],
                'operationType': row['operation_type'],
                'createdAt': iso(row['created_at']),
                'result': json.loads(row['response_json']),
            }

    # -------------------------------------------------------------------------
    # Player Dashboard (GET /api/member/dashboard)
    # -------------------------------------------------------------------------
    def get_dashboard(self, identity):
        """Return the 6-block Player Dashboard projection for the authenticated member."""
        with self.store.transaction() as db:
            member = self.require_member(db, identity)
            state = self._ensure_collection_state(db, member['id'])
            self._release_expired_pending_claims(db, member['id'])
            entitlements = self._active_entitlements(db, member['id'])
            now = self.clock()

            # 1. Interests
            interests = [
                r['category_id']
                for r in db.execute('SELECT category_id FROM member_interests WHERE account_id=? ORDER BY category_id', (member['id'],)).fetchall()
            ]
            saved_ids = {
                r['discovery_id']
                for r in db.execute('SELECT discovery_id FROM member_bookmarks WHERE account_id=?', (member['id'],)).fetchall()
            }

            # 2. Radar block (3 to 6 compatible items)
            radar_items = []
            total_matching_radar = 0
            if interests:
                compatible = [
                    {
                        **catalog.project_discovery(item),
                        'discoveryId': item['id'],
                        'available': True,
                    }
                    for item in self._catalog().values()
                    if catalog.can_access_discovery(item, is_active_member=True, active_entitlements=entitlements, now=now)
                    and item.get('category') in set(interests)
                ]
                total_matching_radar = len(compatible)
                for it in catalog.sort_discoveries(compatible)[:6]:
                    it['saved'] = it['id'] in saved_ids
                    radar_items.append(it)

            # 3. Backpack block (up to 4 latest saved items)
            bookmark_rows = db.page(
                'SELECT discovery_id,saved_at FROM member_bookmarks WHERE account_id=? ORDER BY saved_at DESC, discovery_id DESC',
                (member['id'],),
                4,
            ).fetchall()
            backpack_total = db.execute('SELECT COUNT(*) AS count FROM member_bookmarks WHERE account_id=?', (member['id'],)).fetchone()['count']
            backpack_preview = []
            for r in bookmark_rows:
                proj = self._accessible_item(db, member['id'], r['discovery_id'], entitlements)
                if proj is not None:
                    backpack_preview.append({
                        **proj,
                        'discoveryId': r['discovery_id'],
                        'available': True,
                        'savedAt': iso(r['saved_at']),
                        'item': proj,
                    })
                else:
                    backpack_preview.append({
                        'discoveryId': r['discovery_id'],
                        'available': False,
                        'savedAt': iso(r['saved_at']),
                        'item': None,
                    })

            # 4. Exploration block (up to 4 latest opened items)
            all_exp_rows = db.execute(
                'SELECT discovery_id,first_opened_at,last_opened_at,open_count FROM member_exploration WHERE account_id=? ORDER BY last_opened_at DESC, discovery_id DESC',
                (member['id'],),
            ).fetchall()
            exp_total = len(all_exp_rows)
            exp_categories = set()
            exp_preview = []
            for idx, r in enumerate(all_exp_rows):
                proj = self._accessible_item(db, member['id'], r['discovery_id'], entitlements)
                if proj is not None:
                    exp_categories.add(proj['category'])
                if idx < 4:
                    if proj is not None:
                        exp_preview.append({
                            **proj,
                            'discoveryId': r['discovery_id'],
                            'available': True,
                            'openedAt': iso(r['last_opened_at']),
                            'firstOpenedAt': iso(r['first_opened_at']),
                            'lastOpenedAt': iso(r['last_opened_at']),
                            'openCount': r['open_count'],
                            'item': proj,
                        })
                    else:
                        exp_preview.append({
                            'discoveryId': r['discovery_id'],
                            'available': False,
                            'openedAt': iso(r['last_opened_at']),
                            'firstOpenedAt': iso(r['first_opened_at']),
                            'lastOpenedAt': iso(r['last_opened_at']),
                            'openCount': r['open_count'],
                            'item': None,
                        })

            # 5. Wallet & KP block
            p_state = self.program_state()
            wallet = db.execute('SELECT available,reserved FROM wallets WHERE account_id=?', (member['id'],)).fetchone()
            earned_row = db.execute(
                'SELECT COALESCE(SUM(CASE WHEN available_delta>0 THEN available_delta ELSE 0 END),0) AS earned FROM ledger WHERE account_id=?',
                (member['id'],),
            ).fetchone()
            lifetime_earned = int(earned_row['earned'] or 0)
            pending_rows = db.execute(
                "SELECT id,mission_id,mission_version,attempt_id,award_kp,expires_at FROM mission_pending_claims WHERE account_id=? AND reservation_state='reserved' AND expires_at>? ORDER BY created_at DESC",
                (member['id'], now),
            ).fetchall()

        # 6. Next Mission block
        missions_summary = self.list_missions(identity) if p_state != 'disabled' else {'items': []}
        next_mission = None
        for m in missions_summary.get('items', []):
            if m['memberStatus'] in ('pending_claim', 'in_progress', 'available'):
                next_mission = m
                break
        if next_mission is None and missions_summary.get('items'):
            next_mission = missions_summary['items'][0]

        radar_block = {
            'state': 'ready' if radar_items else ('empty_interests' if not interests else 'empty_results'),
            'status': 'ok' if radar_items else ('interests_empty' if not interests else 'radar_empty'),
            'declaredInterests': interests,
            'interestsVersion': state['interests_version'],
            'totalMatching': total_matching_radar,
            'items': radar_items,
        }
        wallet_block = {
            'state': 'disabled' if p_state == 'disabled' else 'ready',
            'programState': p_state,
            'programStatus': p_state,
            'available': wallet['available'],
            'reserved': wallet['reserved'],
            'lifetimeEarned': lifetime_earned,
            'pendingConfirmationKP': sum(r['award_kp'] for r in pending_rows),
            'pendingClaimsCount': len(pending_rows),
            'pendingCount': len(pending_rows),
            'unit': 'KP',
        }
        backpack_block = {
            'state': 'ready' if backpack_total > 0 else 'empty',
            'totalCount': backpack_total,
            'items': backpack_preview,
        }
        next_mission_block = {
            'state': 'disabled' if p_state == 'disabled' else ('ready' if next_mission else 'empty'),
            'programState': p_state,
            'programStatus': p_state,
            'mission': next_mission,
        }
        exploration_block = {
            'state': 'ready' if exp_total > 0 else 'empty',
            'totalOpened': exp_total,
            'territoriesExplored': len(exp_categories),
            'territoriesTotal': len(INTERESTS),
            'historyGeneration': state['exploration_generation'],
            'items': exp_preview,
            'recentItems': exp_preview,
        }
        interests_block = {
            'state': 'ready' if interests else 'empty',
            'items': interests,
            'categoryIds': interests,
            'version': state['interests_version'],
            'updatedAt': iso(state['updated_at']),
            'availableCategories': sorted(INTERESTS),
        }

        return {
            'asOf': iso(now),
            'greetingName': member['display_name'],
            'member': {
                'id': member['id'],
                'displayName': member['display_name'],
                'avatarUrl': member['avatar_url'],
                'lang': member['lang'],
            },
            'radar': radar_block,
            'wallet': wallet_block,
            'backpack': backpack_block,
            'nextMission': next_mission_block,
            'exploration': exploration_block,
            'interests': interests_block,
            'blocks': {
                'radar': radar_block,
                'wallet': wallet_block,
                'backpack': backpack_block,
                'nextMission': next_mission_block,
                'exploration': exploration_block,
                'interests': interests_block,
            },
        }
