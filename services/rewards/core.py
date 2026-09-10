"""Offline domain foundation. No HTTP listener, authentication adapter or production rewards.

Principal must be constructed by a future trusted session adapter, never from request JSON.
SQLite is a local transaction reference, NOT persistent storage for a scaled Azure Function.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from typing import Callable
from uuid import uuid4


class Rejected(ValueError):
    pass


@dataclass(frozen=True)
class Principal:
    account_id: str
    roles: frozenset[str] = frozenset()


@dataclass(frozen=True)
class VerifiedCompletion:
    # Both values originate in server verification; browser cannot choose occurrence.
    occurrence: str
    evidence_ref: str


def reject_unverified(*_args):
    raise Rejected('Mission verification is not configured')


class Rewards:
    def __init__(self, path: str, verifier: Callable = reject_unverified, clock=time.time):
        self.db = sqlite3.connect(path, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript(Path(__file__).with_name('schema.sql').read_text())
        self.verifier, self.clock = verifier, clock

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def account(self, principal):
        row = self.db.execute("SELECT * FROM accounts WHERE id=? AND state='active'", (principal.account_id,)).fetchone()
        if not row:
            raise Rejected('Active authenticated account required')
        return row

    def wallet(self, principal):
        self.account(principal)
        return dict(self.db.execute('SELECT available,reserved FROM wallets WHERE account_id=?', (principal.account_id,)).fetchone())

    def redemption(self, principal, redemption_id):
        self.account(principal)
        row = self.db.execute('SELECT * FROM redemptions WHERE id=? AND account_id=?', (redemption_id, principal.account_id)).fetchone()
        if not row:
            raise Rejected('Redemption not found')
        return dict(row)

    def replay(self, principal, key, payload):
        if not isinstance(key, str) or not 8 <= len(key) <= 128:
            raise Rejected('Idempotency key must have 8–128 characters')
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        row = self.db.execute('SELECT * FROM requests WHERE account_id=? AND key=?', (principal.account_id, key)).fetchone()
        if row and row['payload_hash'] != digest:
            raise Rejected('Idempotency key reused with a different payload')
        return digest, row['result_id'] if row else None

    def remember(self, principal, key, digest, result):
        self.db.execute('INSERT INTO requests VALUES (?,?,?,?)', (principal.account_id, key, digest, result))

    def post(self, account_id, available, reserved, reason, reference):
        self.db.execute('UPDATE wallets SET available=available+?,reserved=reserved+? WHERE account_id=?', (available, reserved, account_id))
        self.db.execute('INSERT INTO ledger VALUES (?,?,?,?,?,?,?)', (str(uuid4()), account_id, available, reserved, reason, reference, int(self.clock())))

    def complete(self, principal, mission_id, version, evidence, key):
        with self.transaction():
            self.account(principal)
            digest, replay = self.replay(principal, key, ['complete', mission_id, version, evidence])
            if replay:
                return replay
            now = int(self.clock())
            mission = self.db.execute('SELECT * FROM missions WHERE id=? AND version=? AND active=1 AND starts_at<=? AND ends_at>?', (mission_id, version, now, now)).fetchone()
            if not mission:
                raise Rejected('Mission unavailable')
            verified = self.verifier(principal, dict(mission), evidence)
            if not isinstance(verified, VerifiedCompletion) or not verified.occurrence or not verified.evidence_ref:
                raise Rejected('Valid server evidence required')
            existing = self.db.execute('SELECT id FROM completions WHERE account_id=? AND mission_id=? AND mission_version=? AND occurrence=?', (principal.account_id, mission_id, version, verified.occurrence)).fetchone()
            completion_id = existing['id'] if existing else str(uuid4())
            if not existing:
                self.db.execute('INSERT INTO completions VALUES (?,?,?,?,?,?,?)', (completion_id, principal.account_id, mission_id, version, verified.occurrence, verified.evidence_ref, now))
                self.post(principal.account_id, mission['award'], 0, 'mission', completion_id)
            self.remember(principal, key, digest, completion_id)
            return completion_id

    def reserve(self, principal, reward_id, version, key):
        with self.transaction():
            account = self.account(principal)
            digest, replay = self.replay(principal, key, ['reserve', reward_id, version])
            if replay:
                return replay
            reward = self.db.execute("SELECT * FROM rewards WHERE id=? AND version=? AND state='active'", (reward_id, version)).fetchone()
            if not reward or reward['stock'] < 1 or reward['country'] != account['country']:
                raise Rejected('Reward unavailable for this account')
            if self.wallet(principal)['available'] < reward['cost']:
                raise Rejected('Insufficient points')
            redemption_id = str(uuid4())
            self.db.execute('UPDATE rewards SET stock=stock-1 WHERE id=?', (reward_id,))
            self.db.execute('INSERT INTO redemptions VALUES (?,?,?,?,?,?,?)', (redemption_id, principal.account_id, reward_id, version, reward['cost'], 'pending_review', int(self.clock())))
            self.post(principal.account_id, -reward['cost'], reward['cost'], 'reserve', redemption_id)
            self.remember(principal, key, digest, redemption_id)
            return redemption_id

    def transition(self, principal, redemption_id, target, reason):
        with self.transaction():
            self.account(principal)
            if 'rewards_operator' not in principal.roles or not reason.strip():
                raise Rejected('Operator role and audit reason required')
            row = self.db.execute('SELECT * FROM redemptions WHERE id=?', (redemption_id,)).fetchone()
            if not row:
                raise Rejected('Redemption not found')
            if target == row['state']:
                return
            # Once delivery starts, uncertainty requires manual reconciliation, not automatic refund.
            allowed = {'pending_review': {'fulfilling', 'cancelled'}, 'fulfilling': {'fulfilled'}}
            if target not in allowed.get(row['state'], set()):
                raise Rejected('Invalid state transition')
            if target == 'cancelled':
                self.post(row['account_id'], row['cost'], -row['cost'], 'refund', redemption_id)
                self.db.execute('UPDATE rewards SET stock=stock+1 WHERE id=?', (row['reward_id'],))
            elif target == 'fulfilled':
                self.post(row['account_id'], 0, -row['cost'], 'consume', redemption_id)
            self.db.execute('UPDATE redemptions SET state=? WHERE id=?', (target, redemption_id))
            self.db.execute('INSERT INTO audit VALUES (?,?,?,?,?,?,?)', (str(uuid4()), principal.account_id, redemption_id, row['state'], target, reason, int(self.clock())))
