PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS accounts (
 id TEXT PRIMARY KEY, country TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('active','suspended'))
);
CREATE TABLE IF NOT EXISTS wallets (
 account_id TEXT PRIMARY KEY REFERENCES accounts(id),
 available INTEGER NOT NULL DEFAULT 0 CHECK(available >= 0),
 reserved INTEGER NOT NULL DEFAULT 0 CHECK(reserved >= 0)
);
CREATE TABLE IF NOT EXISTS missions (
 id TEXT NOT NULL, version INTEGER NOT NULL CHECK(version > 0), award INTEGER NOT NULL CHECK(award > 0),
 starts_at INTEGER NOT NULL, ends_at INTEGER NOT NULL CHECK(ends_at > starts_at),
 active INTEGER NOT NULL DEFAULT 0 CHECK(active IN (0,1)), PRIMARY KEY(id, version)
);
CREATE TABLE IF NOT EXISTS completions (
 id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id), mission_id TEXT NOT NULL,
 mission_version INTEGER NOT NULL, occurrence TEXT NOT NULL, evidence_ref TEXT NOT NULL, created_at INTEGER NOT NULL,
 UNIQUE(account_id, mission_id, mission_version, occurrence),
 FOREIGN KEY(mission_id, mission_version) REFERENCES missions(id,version)
);
CREATE TABLE IF NOT EXISTS rewards (
 id TEXT PRIMARY KEY, version INTEGER NOT NULL CHECK(version > 0), cost INTEGER NOT NULL CHECK(cost > 0),
 stock INTEGER NOT NULL CHECK(stock >= 0), country TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('draft','active','paused'))
);
CREATE TABLE IF NOT EXISTS redemptions (
 id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id), reward_id TEXT NOT NULL REFERENCES rewards(id),
 reward_version INTEGER NOT NULL, cost INTEGER NOT NULL CHECK(cost > 0),
 state TEXT NOT NULL CHECK(state IN ('pending_review','fulfilling','fulfilled','cancelled')),
 created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS ledger (
 id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id), available_delta INTEGER NOT NULL,
 reserved_delta INTEGER NOT NULL, reason TEXT NOT NULL, reference_id TEXT NOT NULL,
 created_at INTEGER NOT NULL, UNIQUE(reason, reference_id)
);
CREATE TRIGGER IF NOT EXISTS ledger_no_update BEFORE UPDATE ON ledger BEGIN SELECT RAISE(ABORT,'append-only ledger'); END;
CREATE TRIGGER IF NOT EXISTS ledger_no_delete BEFORE DELETE ON ledger BEGIN SELECT RAISE(ABORT,'append-only ledger'); END;
CREATE TABLE IF NOT EXISTS requests (
 account_id TEXT NOT NULL REFERENCES accounts(id), key TEXT NOT NULL, payload_hash TEXT NOT NULL,
 result_id TEXT NOT NULL, PRIMARY KEY(account_id,key)
);
CREATE TABLE IF NOT EXISTS audit (
 id TEXT PRIMARY KEY, actor TEXT NOT NULL, redemption_id TEXT NOT NULL REFERENCES redemptions(id),
 old_state TEXT NOT NULL, new_state TEXT NOT NULL, reason TEXT NOT NULL, created_at INTEGER NOT NULL
);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'append-only audit'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'append-only audit'); END;
