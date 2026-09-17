"""Explicit homolog-only real-SQL smoke; injected mail capture never sends email.

Caller supplies the configured runtime store. Retains a deleted, anonymized test
account as an audit trace; never prints or returns credentials, emails or tokens.
Optional mission_id must identify an administrator-seeded test-only mission.
"""
import os
import uuid
from urllib.parse import urlsplit, parse_qs
from .core import IdentityService
from .config import POLICY_VERSION


def run_live_smoke(store, mission_id=None):
    if os.environ.get('IDENTITY_ENV') != 'homolog':
        raise RuntimeError('Homolog-only smoke')
    deliveries = []

    class Capture:
        def is_configured(self):
            return True
        def send_verification(self, to, url, lang):
            deliveries.append(url)

    service = IdentityService(store, Capture())
    suffix = uuid.uuid4().hex
    email = f'integration-{suffix}@example.invalid'
    password = uuid.uuid4().hex + '!Aa'
    browser_hash = suffix * 2
    account = service.register({'email': email, 'password': password, 'displayName': 'Integration test',
                                'ageConfirmed': True, 'termsAccepted': True, 'termsVersion': POLICY_VERSION,
                                'privacyVersion': POLICY_VERSION}, browser_hash)
    principal = None
    try:
        service.verify_email(parse_qs(urlsplit(deliveries[-1]).query)['token'][0], browser_hash)
        session = service.login(email, password, browser_hash)
        principal = service.authenticate(session['sessionToken'])
        assert principal and principal.account_id == account['accountId']
        profile = service.update_profile(principal, {'displayName': 'Integration checked', 'interests': ['games', 'ia', 'gadgets']})
        assert profile['account']['displayName'] == 'Integration checked'
        assert service.wallet(principal)['available'] == 0
        assert service.ledger(principal)['items'] == []
        rewards = False
        if mission_id:
            challenge = service.challenge(browser_hash, principal, mission_id, 1)
            evidence = service.evidence(browser_hash, principal, challenge['challengeId'], {'interests': ['games', 'ia', 'gadgets']})
            key = 'smoke-' + suffix
            first = service.claim(principal, browser_hash, key, pending_token=evidence['pendingToken'])
            second = service.claim(principal, browser_hash, key, pending_token=evidence['pendingToken'])
            assert first == second
            assert len(service.ledger(principal)['items']) == 1
            rewards = True
        service.logout_all(principal)
        assert service.authenticate(session['sessionToken']) is None
        # Fresh login proves revocation did not remove the account.
        new_session = service.login(email, password, browser_hash)
        principal = service.authenticate(new_session['sessionToken'])
        service.delete_account(principal, 'DELETE', password)
        assert service.authenticate(new_session['sessionToken']) is None
        return {'registration': True, 'emailVerification': True, 'login': True, 'profile': True,
                'walletAndLedger': True, 'revocation': True, 'deletion': True, 'missionReplay': rewards,
                'emailDelivery': 'explicit test capture; no SMTP'}
    finally:
        if principal:
            with store.transaction() as db:
                row = db.execute('SELECT state FROM accounts WHERE id=?', (principal.account_id,)).fetchone()
            if row and row['state'] == 'active':
                service.delete_account(principal, 'DELETE', password)
