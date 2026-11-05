"""Comprehensive test suite for Member Area & Single Wallet (A01-A09, N01-N03, P01-P05, K01-K09, O01-O04)."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

from .clerk_api import dispatch_clerk
from .clerk_auth import ClerkIdentity
from .clerk_service import ClerkAccountService, POLICY_VERSION
from .core import Rejected
from .managed_operator import (
    backfill_collections,
    reconcile_wallets,
    release_expired_claims,
)
from .member_service import MemberAreaService
from .storage import SQLiteStore
from .test_clerk import cpf


class MultiTokenClerkGateway:
    def __init__(self):
        self.tokens: dict[str, ClerkIdentity] = {}
        self.deleted_subjects: set[str] = set()

    def verify(self, auth_header: str | None) -> ClerkIdentity:
        if not auth_header or not auth_header.startswith('Bearer '):
            raise Rejected('authentication_required', 'Entre para continuar.', 401)
        tok = auth_header[7:].strip()
        ident = self.tokens.get(tok)
        if not ident or ident.subject in self.deleted_subjects:
            raise Rejected('invalid_token', 'Sessão inválida ou expirada.', 401)
        return ident

    def delete_user(self, subject: str):
        self.deleted_subjects.add(subject)

    def revoke_session(self, session_id: str):
        pass

    def ban_user(self, subject: str):
        pass


class MemberAreaScenarioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.store = SQLiteStore(Path(self.tmp.name) / 'member_area.sqlite')
        self.now = int(dt.datetime(2026, 11, 5, 12, 0, 0, tzinfo=dt.timezone.utc).timestamp())
        self.gateway = MultiTokenClerkGateway()
        self.cfg = {
            'ok': True,
            'origins': {'https://anderzilla.com'},
            'cpfKey': 'offline-member-area-key-' * 3,
            'programState': 'active',
            'rewards': True,
        }
        self._seed_missions(budget_kp=500, per_account_limit_kp=500)

    def tearDown(self):
        self.tmp.cleanup()

    def _seed_missions(self, budget_kp: int = 500, per_account_limit_kp: int = 500):
        starts = self.now - 86400
        ends = self.now + 86400 * 30
        questions = [
            {
                'id': 'q1',
                'promptPT': 'Qual recurso exige validação do servidor?',
                'promptEN': 'Which feature requires server validation?',
                'options': [
                    {'id': 'a', 'textPT': 'KP oficial', 'textEN': 'Official KP'},
                    {'id': 'b', 'textPT': 'Cache local', 'textEN': 'Local cache'},
                ],
                'correctOption': 'a',
            }
        ]
        with self.store.transaction() as db:
            db.execute(
                'INSERT OR REPLACE INTO mission_campaigns('
                'id,total_budget_kp,reserved_kp,consumed_kp,per_account_limit_kp,starts_at,ends_at,state'
                ') VALUES(?,?,0,0,?,?,?,?)',
                ('camp-main-2026', budget_kp, per_account_limit_kp, starts, ends, 'active'),
            )
            db.execute(
                'INSERT OR REPLACE INTO missions('
                'id,version,award,starts_at,ends_at,active,verifier,definition_json,coverage_reference'
                ') VALUES(?,?,?,?,?,1,?,?,?)',
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
                        'questions': questions,
                    }),
                    'camp-main-2026',
                ),
            )
            db.execute(
                'INSERT OR REPLACE INTO missions('
                'id,version,award,starts_at,ends_at,active,verifier,definition_json,coverage_reference'
                ') VALUES(?,?,?,?,?,1,?,?,?)',
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
                        'minimumInterests': 3,
                    }),
                    'camp-main-2026',
                ),
            )

    def _create_member(
        self,
        token: str,
        subject: str,
        email: str,
        cpf_num: int,
        display_name: str = 'GhostPlayer',
        complete_onboarding: bool = True,
        email_verified: bool = True,
        auth_age_seconds: int = 0,
    ) -> dict:
        ident = ClerkIdentity(subject, f'sess_{subject}', email, self.now - auth_age_seconds)
        self.gateway.tokens[token] = ident
        if not complete_onboarding:
            return {'token': token, 'identity': ident, 'subject': subject}
        res = self._call(
            'POST',
            '/api/account/onboarding',
            token=token,
            body={
                'cpf': cpf(cpf_num),
                'displayName': display_name,
                'birthDate': '1994-06-15',
                'termsAccepted': True,
                'termsVersion': POLICY_VERSION,
                'privacyVersion': POLICY_VERSION,
                'marketingOptIn': False,
                'lang': 'pt-BR',
            },
        )
        self.assertEqual(res['status'], 200)
        account_id = res['body']['account']['id']
        if not email_verified:
            with self.store.transaction() as db:
                db.execute('UPDATE accounts SET email_verified=0 WHERE id=?', (account_id,))
        return {'token': token, 'identity': ident, 'subject': subject, 'accountId': account_id}

    def _call(
        self,
        method: str,
        path: str,
        token: str | None = None,
        body: dict | None = None,
        headers: dict | None = None,
        query: dict | None = None,
    ) -> dict:
        hdrs = {'Origin': 'https://anderzilla.com', 'Content-Type': 'application/json'}
        if token:
            hdrs['Authorization'] = f'Bearer {token}'
        if headers:
            hdrs.update(headers)
        full_path = f'{path}?{urlencode(query)}' if query else path
        return dispatch_clerk(
            self.store,
            method,
            full_path,
            headers=hdrs,
            body=body,
            gateway=self.gateway,
            cfg=self.cfg,
            clock=lambda: self.now,
        )

    # --- A01: Anonymous & Origin protection on all /api/member/* and /api/points/* ---
    def test_a01_anonymous_and_origin_protection(self):
        routes = [
            ('GET', '/api/member/dashboard'),
            ('GET', '/api/member/radar'),
            ('GET', '/api/member/interests'),
            ('PUT', '/api/member/interests'),
            ('GET', '/api/member/backpack'),
            ('PUT', '/api/member/backpack/airpods-live-translation'),
            ('DELETE', '/api/member/backpack/airpods-live-translation'),
            ('GET', '/api/member/exploration'),
            ('POST', '/api/member/exploration/events'),
            ('DELETE', '/api/member/exploration/airpods-live-translation'),
            ('POST', '/api/member/exploration/clear'),
            ('GET', '/api/points/wallet'),
            ('GET', '/api/points/ledger'),
            ('GET', '/api/points/missions'),
            ('POST', '/api/points/challenge'),
            ('GET', '/api/points/challenges/att_123'),
            ('POST', '/api/points/evidence'),
            ('POST', '/api/points/pending/claim'),
            ('GET', '/api/points/operations/op_123'),
            ('GET', '/api/points/operation-status'),
        ]
        for method, path in routes:
            res = self._call(method, path, token=None, body={})
            self.assertEqual(res['status'], 401, f'Expected 401 on {method} {path}')
            self.assertEqual(res['body']['error']['code'], 'authentication_required')

            evil = self._call(
                method,
                path,
                token=None,
                body={},
                headers={'Origin': 'https://evil.example'},
            )
            self.assertEqual(evil['status'], 403, f'Expected 403 on evil Origin for {method} {path}')

    # --- A02: Incomplete onboarding & unverified email blocked on /api/member/* and /api/points/* ---
    def test_a02_incomplete_and_unverified_blocked_from_member_and_points(self):
        inc = self._create_member(
            'tok-inc',
            'user_inc_1',
            'inc@example.invalid',
            111222333,
            complete_onboarding=False,
        )
        unv = self._create_member(
            'tok-unv',
            'user_unv_1',
            'unv@example.invalid',
            222333444,
            complete_onboarding=True,
            email_verified=False,
        )

        me_res = self._call('GET', '/api/account/me', token=inc['token'])
        self.assertEqual(me_res['status'], 200)
        self.assertTrue(me_res['body']['onboardingRequired'])

        for path in [
            '/api/member/dashboard',
            '/api/member/radar',
            '/api/member/interests',
            '/api/member/backpack',
            '/api/member/exploration',
            '/api/points/wallet',
            '/api/points/ledger',
            '/api/points/missions',
        ]:
            res = self._call('GET', path, token=inc['token'])
            self.assertEqual(res['status'], 403, f'Expected 403 onboarding_required on {path}')
            self.assertEqual(res['body']['error']['code'], 'onboarding_required')

            res_unv = self._call('GET', path, token=unv['token'])
            self.assertEqual(res_unv['status'], 403)
            self.assertEqual(res_unv['body']['error']['code'], 'email_unverified')

    # --- A03: Suspended/banned account & invalid token rejected server-side ---
    def test_a03_suspended_account_and_invalid_token_rejected(self):
        member = self._create_member('tok-a03', 'user_a03', 'a03@example.invalid', 333444555)
        bad_tok = self._call('GET', '/api/member/dashboard', token='expired-or-forged')
        self.assertEqual(bad_tok['status'], 401)

        ClerkAccountService(self.store, self.cfg, clock=lambda: self.now).ban_account(
            member['accountId'], 'operator_test', 'fraud_check'
        )
        banned_res = self._call('GET', '/api/member/dashboard', token=member['token'])
        self.assertEqual(banned_res['status'], 403)
        self.assertEqual(banned_res['body']['error']['code'], 'account_unavailable')

    # --- A04 & A05: IDOR / BOLA isolation between Account A and Account B ---
    def test_a04_a05_idor_and_cross_account_isolation(self):
        user_a = self._create_member('tok-a', 'user_a', 'a@example.invalid', 123456789, 'PlayerA')
        user_b = self._create_member('tok-b', 'user_b', 'b@example.invalid', 987654321, 'PlayerB')

        self._call('PUT', '/api/member/backpack/airpods-live-translation', token=user_b['token'], body={})
        ch_b = self._call(
            'POST',
            '/api/points/challenge',
            token=user_b['token'],
            body={'missionId': 'checkpoint-curiosidade', 'missionVersion': 1},
        )['body']
        att_id_b = ch_b['attemptId']

        # Account A tries to read Account B's challenge attempt -> 404 not_found
        idor_att = self._call(
            'GET', f'/api/points/challenges/{att_id_b}', token=user_a['token']
        )
        self.assertEqual(idor_att['status'], 404)

        # Account A tries to submit evidence for Account B's challengeId -> 404 not_found
        idor_ev = self._call(
            'POST',
            '/api/points/evidence',
            token=user_a['token'],
            body={'challengeId': ch_b['challengeId'], 'answers': {'q1': 'a'}},
        )
        self.assertEqual(idor_ev['status'], 404)

        # Account B submits evidence and claims
        ev_b = self._call(
            'POST',
            '/api/points/evidence',
            token=user_b['token'],
            body={'challengeId': ch_b['challengeId'], 'answers': {'q1': 'a'}},
        )['body']
        claim_b = self._call(
            'POST',
            '/api/points/pending/claim',
            token=user_b['token'],
            headers={'Idempotency-Key': 'key-b-claim-1'},
            body={'pendingToken': ev_b['pendingToken']},
        )['body']
        op_id_b = claim_b['operationId']

        # Account A tries to read Account B's operationId -> 404 not_found
        idor_op = self._call(
            'GET', f'/api/points/operations/{op_id_b}', token=user_a['token']
        )
        self.assertEqual(idor_op['status'], 404)

        # Account A tries to delete Account B's bookmark -> does not affect Account B
        self._call(
            'DELETE', '/api/member/backpack/airpods-live-translation', token=user_a['token'], body={}
        )
        bp_b = self._call('GET', '/api/member/backpack', token=user_b['token'])['body']
        self.assertEqual(bp_b['totalCount'], 1)
        self.assertEqual(bp_b['items'][0]['discoveryId'], 'airpods-live-translation')

    # --- A06, N01, N02, N03, K01, K07: Logout/Session Epoch & Header Disclosure & Return Path Sanitization ---
    def test_a06_n01_n02_n03_k01_k07_session_epoch_header_disclosure_and_return_path_contracts(self):
        repo_root = Path(__file__).resolve().parents[2]
        account_provider = (repo_root / 'apps/web/src/components/account/AccountProvider.tsx').read_text(encoding='utf-8')
        account_ui = (repo_root / 'apps/web/src/components/account/AccountUI.tsx').read_text(encoding='utf-8')
        hub_tsx = (repo_root / 'apps/web/src/components/hub/Hub.tsx').read_text(encoding='utf-8')
        rewards_tsx = (repo_root / 'apps/web/src/components/hub/Rewards.tsx').read_text(encoding='utf-8')
        swa_config = json.loads((repo_root / 'apps/web/public/staticwebapp.config.json').read_text(encoding='utf-8'))

        # A06: Session epoch increment, AbortController abort, URL.revokeObjectURL, BroadcastChannel invalidation, logout_unconfirmed
        self.assertIn('sessionEpochRef', account_provider)
        self.assertIn('controllersRef.current', account_provider)
        self.assertIn('URL.revokeObjectURL', account_provider)
        self.assertIn('session_invalidated', account_provider)
        self.assertIn('logout_unconfirmed', account_provider)

        # N01 & N03: Internal return path sanitizer rejects external URLs, //evil.com, javascript:, and unknown paths
        self.assertIn('sanitizeInternalReturnPath', account_provider)
        self.assertIn("trimmed.startsWith('//')", account_provider)
        self.assertIn('savePostLoginIntent', account_provider)
        self.assertIn('consumePostLoginIntent', account_provider)

        # N02: Accessible disclosure button (not role="menu"), aria-expanded, Escape closes and returns focus
        self.assertIn('aria-expanded={menuOpen}', account_ui)
        self.assertIn('aria-controls="member-navigation-disclosure"', account_ui)
        self.assertIn("e.key === 'Escape'", account_ui)
        self.assertNotIn('role="menu"', account_ui)
        self.assertIn('/conta/radar/', account_ui)
        self.assertIn('/conta/mochila/', hub_tsx)

        # K01 & K07: Single wallet source of truth; zero localStorage/sessionStorage wallet or fake guest claims
        self.assertNotIn("localStorage.getItem('anderzilla-wallet", account_provider)
        self.assertNotIn("sessionStorage.getItem('anderzilla-pending-reward')", account_provider)
        self.assertIn('purgeLegacyVisitorStorage', account_provider)
        self.assertIn('OfficialMissions', rewards_tsx)

        # Static Web Apps config headers for /pt/conta/*, /en/conta/*, and /account/ redirect
        route_rules = {r['route']: r for r in swa_config.get('routes', [])}
        self.assertIn('/account/', route_rules)
        self.assertEqual(route_rules['/account/'].get('redirect'), '/pt/conta/')
        for r_key in ('/pt/conta/*', '/en/conta/*'):
            self.assertIn(r_key, route_rules)
            hdrs = route_rules[r_key].get('headers', {})
            self.assertIn('no-store', hdrs.get('Cache-Control', ''))
            self.assertEqual(hdrs.get('X-Robots-Tag'), 'noindex, nofollow')

    # --- A07: Static export privacy & noindex/sitemap/robots audit ---
    def test_a07_static_export_privacy_and_sitemap_audit(self):
        repo_root = Path(__file__).resolve().parents[2]
        out_dir = repo_root / 'apps/web/out'
        if not out_dir.exists():
            self.skipTest('apps/web/out not built yet')

        sitemap_xml = (out_dir / 'sitemap.xml').read_text(encoding='utf-8')
        self.assertNotIn('/pt/conta', sitemap_xml)
        self.assertNotIn('/en/conta', sitemap_xml)
        self.assertNotIn('/account', sitemap_xml)

        robots_txt = (out_dir / 'robots.txt').read_text(encoding='utf-8')
        self.assertIn('Disallow: /pt/conta/', robots_txt)
        self.assertIn('Disallow: /en/conta/', robots_txt)
        self.assertIn('Disallow: /account/', robots_txt)

        expected_html_paths = [
            'pt/conta/index.html',
            'pt/conta/radar/index.html',
            'pt/conta/mochila/index.html',
            'pt/conta/interesses/index.html',
            'pt/conta/exploracao/index.html',
            'pt/conta/kp/index.html',
            'pt/conta/carteira/index.html',
            'pt/conta/missoes/index.html',
            'pt/conta/missoes/checkpoint-curiosidade/index.html',
            'pt/conta/perfil/index.html',
            'en/conta/index.html',
            'en/conta/radar/index.html',
            'en/conta/mochila/index.html',
            'en/conta/interesses/index.html',
            'en/conta/exploracao/index.html',
            'en/conta/kp/index.html',
            'en/conta/carteira/index.html',
            'en/conta/missoes/index.html',
            'en/conta/missoes/checkpoint-curiosidade/index.html',
            'en/conta/perfil/index.html',
            'account/index.html',
        ]
        forbidden_markers = [
            'GhostPlayer',
            'example.invalid',
            'cpf_hmac',
            'correctOption',
            'pending_token_hash',
        ]
        for rel in expected_html_paths:
            f_path = out_dir / rel
            self.assertTrue(f_path.exists(), f'Missing static export file: {rel}')
            html = f_path.read_text(encoding='utf-8')
            self.assertIn('noindex', html, f'Missing noindex in {rel}')
            for marker in forbidden_markers:
                self.assertNotIn(marker, html, f'Private/secret marker {marker} leaked into {rel}')

    # --- A08: Unpublished or unentitled items in Backpack return safe placeholder ---
    def test_a08_unavailable_and_entitled_items_never_leak_metadata(self):
        user = self._create_member('tok-a08', 'user_a08', 'a08@example.invalid', 444555666)
        overrides = {
            'secret-draft': {
                'category': 'games',
                'publicationStatus': 'draft',
                'visibility': 'public',
                'titlePT': 'Rascunho Secreto Embargado',
                'titleEN': 'Embargoed Secret Draft',
                'summaryPT': 'Segredo nao publicado',
                'summaryEN': 'Unpublished secret',
                'slugPT': 'rascunho-secreto',
                'slugEN': 'secret-draft',
            },
            'vip-story': {
                'category': 'gadgets',
                'publicationStatus': 'published',
                'visibility': 'entitled',
                'requiredEntitlement': 'site_plan',
                'requiredEntitlementTarget': 'founder',
                'titlePT': 'Artigo Exclusivo Founder',
                'titleEN': 'Founder Exclusive Article',
                'summaryPT': 'Resumo exclusivo',
                'summaryEN': 'Exclusive summary',
                'slugPT': 'vip-story',
                'slugEN': 'vip-story',
            },
        }
        svc = MemberAreaService(self.store, self.cfg, clock=lambda: self.now, catalog_overrides=overrides)

        # Attempting to save a draft item directly is rejected with 404
        with self.assertRaises(Rejected) as ctx:
            svc.put_backpack_item(user['identity'], 'secret-draft')
        self.assertEqual(ctx.exception.status, 404)

        # Simulate an item that was saved when public/published and later became draft or entitled
        with self.store.transaction() as db:
            db.execute(
                'INSERT INTO member_bookmarks(account_id,discovery_id,saved_at) VALUES(?,?,?)',
                (user['accountId'], 'secret-draft', self.now),
            )
            db.execute(
                'INSERT INTO member_bookmarks(account_id,discovery_id,saved_at) VALUES(?,?,?)',
                (user['accountId'], 'vip-story', self.now - 1),
            )

        bp = svc.get_backpack(user['identity'])
        self.assertEqual(bp['totalCount'], 2)
        for item in bp['items']:
            self.assertFalse(item['available'])
            self.assertNotIn('titlePT', item)
            self.assertNotIn('summaryPT', item)
            self.assertNotIn('slugPT', item)

        # Grant entitlement to vip-story -> now vip-story becomes available while secret-draft stays unavailable
        with self.store.transaction() as db:
            db.execute(
                'INSERT INTO account_entitlements(id,account_id,kind,target_id,state,created_at) VALUES(?,?,?,?,?,?)',
                ('ent-1', user['accountId'], 'site_plan', 'founder', 'active', self.now),
            )
        bp_after = svc.get_backpack(user['identity'])
        by_id = {x['discoveryId']: x for x in bp_after['items']}
        self.assertTrue(by_id['vip-story']['available'])
        self.assertEqual(by_id['vip-story']['titlePT'], 'Artigo Exclusivo Founder')
        self.assertFalse(by_id['secret-draft']['available'])

        # User can still remove unavailable item from backpack
        del_res = svc.delete_backpack_item(user['identity'], 'secret-draft')
        self.assertTrue(del_res['removed'])

    # --- A09: Client-supplied authority/privilege fields rejected ---
    def test_a09_rejects_client_authority_and_privilege_fields(self):
        user = self._create_member('tok-a09', 'user_a09', 'a09@example.invalid', 555666777)
        for forbidden_field, value in [
            ('role', 'admin'),
            ('isAdmin', True),
            ('plan', 'enterprise'),
            ('entitlements', ['site_plan:founder']),
            ('award', 9999),
            ('balance', 9999),
            ('cpf', '12345678901'),
            ('birthDate', '2000-01-01'),
            ('accountId', 'acc_other'),
        ]:
            res_int = self._call(
                'PUT',
                '/api/member/interests',
                token=user['token'],
                body={'interests': ['ia'], forbidden_field: value},
            )
            self.assertEqual(res_int['status'], 422)
            self.assertEqual(res_int['body']['error']['code'], 'invalid_fields')

            res_prof = self._call(
                'PATCH',
                '/api/account/profile',
                token=user['token'],
                body={'displayName': 'ValidName', forbidden_field: value},
            )
            self.assertIn(res_prof['status'], (400, 422))
            self.assertEqual(res_prof['body']['error']['code'], 'invalid_fields')

    # --- P01: Backpack idempotent PUT/DELETE & undo ---
    def test_p01_backpack_idempotent_save_remove_and_undo(self):
        user = self._create_member('tok-p01', 'user_p01', 'p01@example.invalid', 666777888)
        r1 = self._call('PUT', '/api/member/backpack/airpods-live-translation', token=user['token'], body={})
        r2 = self._call('PUT', '/api/member/backpack/airpods-live-translation', token=user['token'], body={})
        self.assertEqual(r1['status'], 200)
        self.assertEqual(r2['status'], 200)
        bp = self._call('GET', '/api/member/backpack', token=user['token'])['body']
        self.assertEqual(bp['totalCount'], 1)

        d1 = self._call('DELETE', '/api/member/backpack/airpods-live-translation', token=user['token'], body={})
        d2 = self._call('DELETE', '/api/member/backpack/airpods-live-translation', token=user['token'], body={})
        self.assertEqual(d1['status'], 200)
        self.assertEqual(d2['status'], 200)
        self.assertEqual(
            self._call('GET', '/api/member/backpack', token=user['token'])['body']['totalCount'],
            0,
        )

        # Undo re-saves the item cleanly
        undo = self._call('PUT', '/api/member/backpack/airpods-live-translation', token=user['token'], body={})
        self.assertEqual(undo['status'], 200)
        self.assertEqual(
            self._call('GET', '/api/member/backpack', token=user['token'])['body']['totalCount'],
            1,
        )

    # --- P02: Versioned PUT /api/member/interests & optimistic concurrency ---
    def test_p02_interests_version_concurrency_and_empty_valid(self):
        user = self._create_member('tok-p02', 'user_p02', 'p02@example.invalid', 777888999)
        init = self._call('GET', '/api/member/interests', token=user['token'])['body']
        v1 = init['version']

        up1 = self._call(
            'PUT',
            '/api/member/interests',
            token=user['token'],
            body={'interests': ['ia', 'games'], 'expectedVersion': v1},
        )
        self.assertEqual(up1['status'], 200)
        self.assertEqual(up1['body']['version'], v1 + 1)
        self.assertEqual(set(up1['body']['interests']), {'ia', 'games'})

        # Concurrent/stale tab tries to save with old expectedVersion=v1 -> 409 interests_conflict
        conflict = self._call(
            'PUT',
            '/api/member/interests',
            token=user['token'],
            body={'interests': ['gadgets'], 'expectedVersion': v1},
        )
        self.assertEqual(conflict['status'], 409)
        self.assertEqual(conflict['body']['error']['code'], 'interests_conflict')

        # Saving 0 topics with current version succeeds cleanly
        empty_ok = self._call(
            'PUT',
            '/api/member/interests',
            token=user['token'],
            body={'interests': [], 'expectedVersion': v1 + 1},
        )
        self.assertEqual(empty_ok['status'], 200)
        self.assertEqual(empty_ok['body']['interests'], [])

    # --- P03: Radar with 0 topics, temporary category filter outside declared topics ---
    def test_p03_member_radar_empty_and_temporary_filter_does_not_mutate_interests(self):
        user = self._create_member('tok-p03', 'user_p03', 'p03@example.invalid', 888999111)
        r0 = self._call('GET', '/api/member/radar', token=user['token'])['body']
        self.assertEqual(r0['status'], 'interests_empty')
        self.assertEqual(r0['items'], [])

        self._call(
            'PUT',
            '/api/member/interests',
            token=user['token'],
            body={'interests': ['ia']},
        )
        r_ia = self._call('GET', '/api/member/radar', token=user['token'])['body']
        self.assertEqual(r_ia['status'], 'ok')
        self.assertTrue(all(item['category'] == 'ia' for item in r_ia['items']))

        # Apply temporary filter category=games (outside declared interests ['ia'])
        r_temp = self._call(
            'GET',
            '/api/member/radar',
            token=user['token'],
            query={'category': 'games'},
        )['body']
        self.assertTrue(r_temp['temporaryFilterOutsideInterests'])
        self.assertTrue(all(item['category'] == 'games' for item in r_temp['items']))

        # Verify declared interests in DB were NOT mutated by temporary filter
        saved_int = self._call('GET', '/api/member/interests', token=user['token'])['body']
        self.assertEqual(saved_int['interests'], ['ia'])

    # --- P04: Exploration deduplication, generation increment on clear, stale event rejection, zero KP ---
    def test_p04_exploration_deduplication_clear_generation_and_zero_kp(self):
        user = self._create_member('tok-p04', 'user_p04', 'p04@example.invalid', 999111222)
        ev1 = self._call(
            'POST',
            '/api/member/exploration/events',
            token=user['token'],
            body={'discoveryId': 'airpods-live-translation', 'itemVersion': 'v1', 'historyGeneration': 1},
        )
        self.assertEqual(ev1['status'], 200)
        self.assertEqual(ev1['body']['awardedKP'], 0)

        ev2 = self._call(
            'POST',
            '/api/member/exploration/events',
            token=user['token'],
            body={'discoveryId': 'airpods-live-translation', 'itemVersion': 'v1', 'historyGeneration': 1},
        )
        self.assertEqual(ev2['status'], 200)
        self.assertTrue(ev2['body']['deduplicated'])

        exp = self._call('GET', '/api/member/exploration', token=user['token'])['body']
        self.assertEqual(exp['totalOpened'], 1)
        self.assertEqual(exp['items'][0]['openCount'], 1)

        clr = self._call('POST', '/api/member/exploration/clear', token=user['token'], body={'confirm': True})
        self.assertEqual(clr['status'], 200)
        self.assertEqual(clr['body']['historyGeneration'], 2)

        # Stale in-transit event with old historyGeneration=1 is rejected with 409 stale_exploration_event
        stale = self._call(
            'POST',
            '/api/member/exploration/events',
            token=user['token'],
            body={'discoveryId': 'airpods-live-translation', 'itemVersion': 'v1', 'historyGeneration': 1},
        )
        self.assertEqual(stale['status'], 409)
        self.assertEqual(stale['body']['error']['code'], 'stale_exploration_event')

        # Subsequent open with current historyGeneration=2 succeeds
        ev_after = self._call(
            'POST',
            '/api/member/exploration/events',
            token=user['token'],
            body={'discoveryId': 'airpods-live-translation', 'itemVersion': 'v1', 'historyGeneration': 2},
        )
        self.assertEqual(ev_after['status'], 200)
        self.assertFalse(ev_after['body']['deduplicated'])

        wallet = self._call('GET', '/api/points/wallet', token=user['token'])['body']
        self.assertEqual(wallet['available'], 0)

    # --- P05: Deterministic pagination for >1000 items without duplicates or omissions ---
    def test_p05_backpack_pagination_over_1000_items(self):
        user = self._create_member('tok-p05', 'user_p05', 'p05@example.invalid', 121314151)
        with self.store.transaction() as db:
            for idx in range(1050):
                ts = self.now - (idx // 5)
                did = f'synthetic-item-{idx:04d}'
                db.execute(
                    'INSERT INTO member_bookmarks(account_id,discovery_id,saved_at) VALUES(?,?,?)',
                    (user['accountId'], did, ts),
                )

        seen_ids = []
        cursor = None
        pages = 0
        while True:
            q = {'limit': '50'}
            if cursor:
                q['cursor'] = cursor
            res = self._call('GET', '/api/member/backpack', token=user['token'], query=q)
            self.assertEqual(res['status'], 200)
            self.assertEqual(res['body']['totalCount'], 1050)
            batch = [x['discoveryId'] for x in res['body']['items']]
            seen_ids.extend(batch)
            cursor = res['body']['nextCursor']
            pages += 1
            if not cursor:
                break

        self.assertEqual(pages, 21)
        self.assertEqual(len(seen_ids), 1050)
        self.assertEqual(len(set(seen_ids)), 1050)

        bad_cursor = self._call(
            'GET',
            '/api/member/backpack',
            token=user['token'],
            query={'cursor': 'not-a-valid-cursor!!!'},
        )
        self.assertEqual(bad_cursor['status'], 422)
        self.assertEqual(bad_cursor['body']['error']['code'], 'invalid_cursor')

    # --- K02, K03, K04: Idempotency, concurrency, conflict, and pre-operationId status recovery ---
    def test_k02_k03_k04_single_wallet_claim_idempotency_conflict_and_status_recovery(self):
        user = self._create_member('tok-k02', 'user_k02', 'k02@example.invalid', 232425262)
        ch = self._call(
            'POST',
            '/api/points/challenge',
            token=user['token'],
            body={'missionId': 'checkpoint-curiosidade', 'missionVersion': 1},
        )['body']
        ev = self._call(
            'POST',
            '/api/points/evidence',
            token=user['token'],
            body={'challengeId': ch['challengeId'], 'answers': {'q1': 'a'}},
        )['body']
        pending_token = ev['pendingToken']

        def claim_call(idem_key: str):
            return self._call(
                'POST',
                '/api/points/pending/claim',
                token=user['token'],
                headers={'Idempotency-Key': idem_key},
                body={'pendingToken': pending_token},
            )

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [
                pool.submit(claim_call, 'claim-key-1'),
                pool.submit(claim_call, 'claim-key-1'),
                pool.submit(claim_call, 'claim-key-2'),
            ]
            results = [f.result() for f in futures]

        for r in results:
            self.assertEqual(r['status'], 200)
            self.assertEqual(r['body']['wallet']['available'], 25)

        receipt_ids = {r['body']['receipt']['receiptId'] for r in results}
        self.assertEqual(len(receipt_ids), 1, 'Must produce exactly 1 receipt across concurrent calls')

        # K03: Reusing 'claim-key-1' with a different payload -> 409 idempotency_conflict
        conflict = self._call(
            'POST',
            '/api/points/pending/claim',
            token=user['token'],
            headers={'Idempotency-Key': 'claim-key-1'},
            body={'pendingToken': f'{pending_token}-different'},
        )
        self.assertEqual(conflict['status'], 409)
        self.assertEqual(conflict['body']['error']['code'], 'idempotency_conflict')

        # K04: Recover status by pre-known Idempotency-Key without knowing operationId
        rec_by_key = self._call(
            'GET',
            '/api/points/operation-status',
            token=user['token'],
            headers={'Idempotency-Key': 'claim-key-1'},
            query={'type': 'claim'},
        )
        self.assertEqual(rec_by_key['status'], 200)
        self.assertEqual(rec_by_key['body']['status'], 'completed')
        self.assertEqual(
            rec_by_key['body']['result']['receipt']['receiptId'],
            next(iter(receipt_ids)),
        )

        # Also verify attempt lookup returns completed receipt
        att_res = self._call(
            'GET',
            f"/api/points/challenges/{ch['attemptId']}",
            token=user['token'],
        )
        self.assertEqual(att_res['status'], 200)
        self.assertEqual(att_res['body']['status'], 'completed')
        self.assertEqual(att_res['body']['receipt']['awardedKP'], 25)

        rec = reconcile_wallets(self.store)
        self.assertTrue(rec['ok'])

    # --- K05: Expiry, single reservation release, and program states (new_activity_paused, maintenance) ---
    def test_k05_expiry_reservation_release_and_program_states(self):
        user = self._create_member('tok-k05', 'user_k05', 'k05@example.invalid', 343536373)
        ch = self._call(
            'POST',
            '/api/points/challenge',
            token=user['token'],
            body={'missionId': 'checkpoint-curiosidade', 'missionVersion': 1},
        )['body']
        ev = self._call(
            'POST',
            '/api/points/evidence',
            token=user['token'],
            body={'challengeId': ch['challengeId'], 'answers': {'q1': 'a'}},
        )['body']

        with self.store.transaction() as db:
            camp = db.execute(
                "SELECT reserved_kp,consumed_kp FROM mission_campaigns WHERE id='camp-main-2026'"
            ).fetchone()
            self.assertEqual(int(camp['reserved_kp']), 25)

        # Force pending claim to expire in the past
        with self.store.transaction() as db:
            db.execute(
                'UPDATE mission_pending_claims SET expires_at=? WHERE id=?',
                (self.now - 600, ev['pendingId']),
            )

        exp_claim = self._call(
            'POST',
            '/api/points/pending/claim',
            token=user['token'],
            headers={'Idempotency-Key': 'exp-claim-1'},
            body={'pendingToken': ev['pendingToken']},
        )
        self.assertEqual(exp_claim['status'], 410)
        self.assertEqual(exp_claim['body']['error']['code'], 'claim_expired')

        release_expired_claims(self.store, self.cfg, clock=lambda: self.now)
        with self.store.transaction() as db:
            camp_after = db.execute(
                "SELECT reserved_kp,consumed_kp FROM mission_campaigns WHERE id='camp-main-2026'"
            ).fetchone()
            self.assertEqual(int(camp_after['reserved_kp']), 0)
            self.assertEqual(int(camp_after['consumed_kp']), 0)

        # Issue a fresh challenge and evidence while active, then pause new activity
        ch2 = self._call(
            'POST',
            '/api/points/challenge',
            token=user['token'],
            body={'missionId': 'checkpoint-curiosidade', 'missionVersion': 1},
        )['body']
        ev2 = self._call(
            'POST',
            '/api/points/evidence',
            token=user['token'],
            body={'challengeId': ch2['challengeId'], 'answers': {'q1': 'a'}},
        )['body']

        self.cfg['programState'] = 'new_activity_paused'
        paused_ch = self._call(
            'POST',
            '/api/points/challenge',
            token=user['token'],
            body={'missionId': 'monte-seu-radar', 'missionVersion': 1},
        )
        self.assertEqual(paused_ch['status'], 409)
        self.assertEqual(paused_ch['body']['error']['code'], 'program_paused')

        # Existing valid pending claim with reserved budget can still be confirmed during new_activity_paused
        paused_claim = self._call(
            'POST',
            '/api/points/pending/claim',
            token=user['token'],
            headers={'Idempotency-Key': 'paused-claim-ok'},
            body={'pendingToken': ev2['pendingToken']},
        )
        self.assertEqual(paused_claim['status'], 200)
        self.assertEqual(paused_claim['body']['wallet']['available'], 25)

        self.cfg['programState'] = 'maintenance'
        maint_res = self._call(
            'POST',
            '/api/points/challenge',
            token=user['token'],
            body={'missionId': 'monte-seu-radar', 'missionVersion': 1},
        )
        self.assertEqual(maint_res['status'], 503)

    # --- K06: Transactional rollback on partial failure between completion/ledger/wallet ---
    def test_k06_transactional_atomicity_on_mid_claim_failure(self):
        user = self._create_member('tok-k06', 'user_k06', 'k06@example.invalid', 454647484)
        ch = self._call(
            'POST',
            '/api/points/challenge',
            token=user['token'],
            body={'missionId': 'checkpoint-curiosidade', 'missionVersion': 1},
        )['body']
        ev = self._call(
            'POST',
            '/api/points/evidence',
            token=user['token'],
            body={'challengeId': ch['challengeId'], 'answers': {'q1': 'a'}},
        )['body']

        svc = MemberAreaService(self.store, self.cfg, clock=lambda: self.now)
        for fail_step in ('completion', 'ledger'):
            with self.assertRaises(RuntimeError):
                svc.claim_pending(
                    user['identity'],
                    {'pendingToken': ev['pendingToken']},
                    {'idempotency-key': f'fail-{fail_step}'},
                    fail_after_step=fail_step,
                )

        wallet = self._call('GET', '/api/points/wallet', token=user['token'])['body']
        self.assertEqual(wallet['available'], 0)
        self.assertEqual(wallet['entries'], [])
        rec = reconcile_wallets(self.store)
        self.assertTrue(rec['ok'])

        ok_res = self._call(
            'POST',
            '/api/points/pending/claim',
            token=user['token'],
            headers={'Idempotency-Key': 'claim-after-rollback'},
            body={'pendingToken': ev['pendingToken']},
        )
        self.assertEqual(ok_res['status'], 200)
        self.assertEqual(ok_res['body']['wallet']['available'], 25)
        self.assertTrue(reconcile_wallets(self.store)['ok'])

    # --- K08: Additive backfill from preferences_bookmarks & zero demo import ---
    def test_k08_additive_backfill_from_preferences_bookmarks(self):
        user = self._create_member('tok-k08', 'user_k08', 'k08@example.invalid', 565758595)
        with self.store.transaction() as db:
            db.execute(
                'DELETE FROM member_collection_state WHERE account_id=?',
                (user['accountId'],),
            )
            db.execute(
                'UPDATE preferences_bookmarks SET interests=?,saved=?,opened=? WHERE account_id=?',
                (
                    json.dumps(['ia', 'games']),
                    json.dumps(['airpods-live-translation']),
                    json.dumps(['webb-neptune-auroras']),
                    user['accountId'],
                ),
            )

        res = backfill_collections(self.store, self.cfg, clock=lambda: self.now)
        self.assertTrue(res['ok'])

        interests = self._call('GET', '/api/member/interests', token=user['token'])['body']
        self.assertEqual(set(interests['interests']), {'ia', 'games'})
        backpack = self._call('GET', '/api/member/backpack', token=user['token'])['body']
        self.assertEqual(backpack['totalCount'], 1)
        exploration = self._call('GET', '/api/member/exploration', token=user['token'])['body']
        self.assertEqual(exploration['totalOpened'], 1)
        wallet = self._call('GET', '/api/points/wallet', token=user['token'])['body']
        self.assertEqual(wallet['available'], 0)

    # --- K09: Multi-account contention for last remaining campaign budget ---
    def test_k09_campaign_budget_contention_between_accounts(self):
        self._seed_missions(budget_kp=25, per_account_limit_kp=500)
        u1 = self._create_member('tok-u1', 'user_u1', 'u1@example.invalid', 676869606, 'Player1')
        u2 = self._create_member('tok-u2', 'user_u2', 'u2@example.invalid', 787970717, 'Player2')

        ch1 = self._call(
            'POST',
            '/api/points/challenge',
            token=u1['token'],
            body={'missionId': 'checkpoint-curiosidade', 'missionVersion': 1},
        )['body']
        ch2 = self._call(
            'POST',
            '/api/points/challenge',
            token=u2['token'],
            body={'missionId': 'checkpoint-curiosidade', 'missionVersion': 1},
        )['body']

        ev1 = self._call(
            'POST',
            '/api/points/evidence',
            token=u1['token'],
            body={'challengeId': ch1['challengeId'], 'answers': {'q1': 'a'}},
        )
        ev2 = self._call(
            'POST',
            '/api/points/evidence',
            token=u2['token'],
            body={'challengeId': ch2['challengeId'], 'answers': {'q1': 'a'}},
        )
        statuses = sorted([ev1['status'], ev2['status']])
        self.assertEqual(statuses, [200, 409])
        rejected = ev2 if ev2['status'] == 409 else ev1
        self.assertEqual(rejected['body']['error']['code'], 'reward_capacity')
        self.assertTrue(reconcile_wallets(self.store)['ok'])

    # --- O01-O04: Export/delete with pending claims, step-up reauth, and production KP gate ---
    def test_o01_o04_export_delete_releases_reservation_and_production_gate(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('IDENTITY_REWARDS_ENABLED', None)
            os.environ.pop('IDENTITY_KP_PROGRAM_STATE', None)
            default_svc = MemberAreaService(self.store, {'ok': True, 'origins': set(), 'cpfKey': 'k' * 32})
            self.assertEqual(default_svc.program_state(), 'disabled')
            self.assertFalse(default_svc.rewards_enabled())

        user = self._create_member('tok-o01', 'user_o01', 'o01@example.invalid', 898081828)
        self._call('PUT', '/api/member/backpack/airpods-live-translation', token=user['token'], body={})
        ch = self._call(
            'POST',
            '/api/points/challenge',
            token=user['token'],
            body={'missionId': 'checkpoint-curiosidade', 'missionVersion': 1},
        )['body']
        self._call(
            'POST',
            '/api/points/evidence',
            token=user['token'],
            body={'challengeId': ch['challengeId'], 'answers': {'q1': 'a'}},
        )

        export_res = self._call('GET', '/api/account/export', token=user['token'])
        self.assertEqual(export_res['status'], 200)
        self.assertIn('backpack', export_res['body'])
        self.assertEqual(len(export_res['body']['backpack']), 1)

        # If session is older than 5 minutes -> 403 reauth_required
        self.gateway.tokens[user['token']] = ClerkIdentity(
            user['subject'], f"sess_{user['subject']}", 'o01@example.invalid', self.now - 600
        )
        old_del = self._call(
            'POST',
            '/api/account/delete',
            token=user['token'],
            body={'confirm': 'DELETE'},
        )
        self.assertEqual(old_del['status'], 403)
        self.assertEqual(old_del['body']['error']['code'], 'reauth_required')

        # Refresh session authenticated_at -> delete succeeds (204) and releases reserved_kp on campaign
        self.gateway.tokens[user['token']] = ClerkIdentity(
            user['subject'], f"sess_{user['subject']}", 'o01@example.invalid', self.now
        )
        del_res = self._call(
            'POST',
            '/api/account/delete',
            token=user['token'],
            body={'confirm': 'DELETE'},
        )
        self.assertEqual(del_res['status'], 204)
        self.assertTrue(reconcile_wallets(self.store)['ok'])


if __name__ == '__main__':
    unittest.main()
