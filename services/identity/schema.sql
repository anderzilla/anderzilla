PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS accounts (id TEXT PRIMARY KEY,email TEXT NOT NULL UNIQUE,email_verified INTEGER NOT NULL DEFAULT 0 CHECK(email_verified IN(0,1)),display_name TEXT NOT NULL,password_hash TEXT,state TEXT NOT NULL CHECK(state IN('active','suspended','deleted')),lang TEXT NOT NULL DEFAULT 'pt-BR',timezone TEXT NOT NULL DEFAULT 'America/Sao_Paulo',marketing_opt_in INTEGER NOT NULL DEFAULT 0,age_confirmed_at INTEGER NOT NULL,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,avatar_url TEXT);
CREATE TABLE IF NOT EXISTS email_verifications (id TEXT PRIMARY KEY,account_id TEXT NOT NULL REFERENCES accounts(id),token_hash TEXT NOT NULL UNIQUE,expires_at INTEGER NOT NULL,used_at INTEGER,created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS oauth_identities (provider TEXT NOT NULL,subject TEXT NOT NULL,account_id TEXT NOT NULL REFERENCES accounts(id),created_at INTEGER NOT NULL,PRIMARY KEY(provider,subject),UNIQUE(provider,account_id));
CREATE TABLE IF NOT EXISTS oauth_nonces (state TEXT PRIMARY KEY,nonce TEXT NOT NULL,verifier TEXT NOT NULL,browser_hash TEXT NOT NULL,consent_json TEXT NOT NULL,expires_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY,account_id TEXT NOT NULL REFERENCES accounts(id),token_hash TEXT NOT NULL UNIQUE,created_at INTEGER NOT NULL,expires_at INTEGER NOT NULL,revoked_at INTEGER);
CREATE TABLE IF NOT EXISTS wallets (account_id TEXT PRIMARY KEY REFERENCES accounts(id),available INTEGER NOT NULL DEFAULT 0 CHECK(available>=0),reserved INTEGER NOT NULL DEFAULT 0 CHECK(reserved>=0));
CREATE TABLE IF NOT EXISTS preferences_bookmarks (account_id TEXT PRIMARY KEY REFERENCES accounts(id),interests TEXT NOT NULL DEFAULT '[]',saved TEXT NOT NULL DEFAULT '[]',opened TEXT NOT NULL DEFAULT '[]');
CREATE TABLE IF NOT EXISTS missions (id TEXT NOT NULL,version INTEGER NOT NULL CHECK(version>0),award INTEGER NOT NULL CHECK(award>0 AND award<=500),starts_at INTEGER NOT NULL,ends_at INTEGER NOT NULL CHECK(ends_at>starts_at),active INTEGER NOT NULL DEFAULT 0,verifier TEXT NOT NULL CHECK(verifier IN('quiz','interests')),definition_json TEXT NOT NULL,coverage_reference TEXT NOT NULL,PRIMARY KEY(id,version));
CREATE TABLE IF NOT EXISTS challenges (id TEXT PRIMARY KEY,browser_hash TEXT NOT NULL,account_id TEXT REFERENCES accounts(id),mission_id TEXT NOT NULL,mission_version INTEGER NOT NULL,definition_hash TEXT NOT NULL,expires_at INTEGER NOT NULL,used_at INTEGER,FOREIGN KEY(mission_id,mission_version) REFERENCES missions(id,version));
CREATE TABLE IF NOT EXISTS mission_evidence (id TEXT PRIMARY KEY,challenge_id TEXT NOT NULL UNIQUE REFERENCES challenges(id),browser_hash TEXT NOT NULL,account_id TEXT REFERENCES accounts(id),mission_id TEXT NOT NULL,mission_version INTEGER NOT NULL,payload TEXT NOT NULL,created_at INTEGER NOT NULL,FOREIGN KEY(mission_id,mission_version) REFERENCES missions(id,version));
CREATE TABLE IF NOT EXISTS pending_rewards (id TEXT PRIMARY KEY,token_hash TEXT NOT NULL UNIQUE,browser_hash TEXT NOT NULL,evidence_id TEXT NOT NULL REFERENCES mission_evidence(id),expires_at INTEGER NOT NULL,claimed_at INTEGER,claimed_by TEXT REFERENCES accounts(id));
CREATE TABLE IF NOT EXISTS completions (id TEXT PRIMARY KEY,account_id TEXT NOT NULL REFERENCES accounts(id),mission_id TEXT NOT NULL,mission_version INTEGER NOT NULL,evidence_ref TEXT NOT NULL REFERENCES mission_evidence(id),created_at INTEGER NOT NULL,UNIQUE(account_id,mission_id,mission_version),FOREIGN KEY(mission_id,mission_version) REFERENCES missions(id,version));
CREATE TABLE IF NOT EXISTS ledger (id TEXT PRIMARY KEY,account_id TEXT NOT NULL REFERENCES accounts(id),available_delta INTEGER NOT NULL,reserved_delta INTEGER NOT NULL,reason TEXT NOT NULL,reference_id TEXT NOT NULL,created_at INTEGER NOT NULL,UNIQUE(reason,reference_id));
CREATE TABLE IF NOT EXISTS requests (account_id TEXT NOT NULL REFERENCES accounts(id),request_key TEXT NOT NULL,payload_hash TEXT NOT NULL,result_id TEXT NOT NULL,PRIMARY KEY(account_id,request_key));
CREATE TABLE IF NOT EXISTS rate_limits (scope TEXT NOT NULL,bucket TEXT NOT NULL,window_start INTEGER NOT NULL,count INTEGER NOT NULL,PRIMARY KEY(scope,bucket));
CREATE TABLE IF NOT EXISTS consents (id TEXT PRIMARY KEY,account_id TEXT NOT NULL REFERENCES accounts(id),purpose TEXT NOT NULL,version TEXT NOT NULL,granted INTEGER NOT NULL,created_at INTEGER NOT NULL);
CREATE TRIGGER IF NOT EXISTS ledger_no_update BEFORE UPDATE ON ledger BEGIN SELECT RAISE(ABORT,'append-only ledger'); END;
CREATE TRIGGER IF NOT EXISTS ledger_no_delete BEFORE DELETE ON ledger BEGIN SELECT RAISE(ABORT,'append-only ledger'); END;

-- Managed identity tables are additive; old native identities are never auto-linked.
CREATE TABLE IF NOT EXISTS managed_identities (subject TEXT PRIMARY KEY,account_id TEXT NOT NULL UNIQUE REFERENCES accounts(id),created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS managed_profiles (account_id TEXT PRIMARY KEY REFERENCES accounts(id),cpf_fingerprint TEXT NOT NULL UNIQUE,cpf_last_two TEXT NOT NULL,birth_date TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS managed_bans (cpf_fingerprint TEXT PRIMARY KEY,email_fingerprint TEXT NOT NULL,account_id TEXT NOT NULL REFERENCES accounts(id),created_at INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS managed_bans_email ON managed_bans(email_fingerprint);
CREATE TABLE IF NOT EXISTS managed_audit (id TEXT PRIMARY KEY,account_id TEXT NOT NULL REFERENCES accounts(id),actor TEXT NOT NULL,action TEXT NOT NULL,reason TEXT NOT NULL,created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS managed_deletions (account_id TEXT PRIMARY KEY REFERENCES accounts(id),subject TEXT NOT NULL,requested_at INTEGER NOT NULL,completed_at INTEGER);
CREATE TABLE IF NOT EXISTS managed_webhook_receipts (message_id TEXT PRIMARY KEY,event_type TEXT NOT NULL,received_at INTEGER NOT NULL);

-- Member Area relational collections, entitlements and transactional KP/missions tables.
CREATE TABLE IF NOT EXISTS member_collection_state (
    account_id TEXT PRIMARY KEY REFERENCES accounts(id),
    interests_version INTEGER NOT NULL DEFAULT 1 CHECK(interests_version>=1),
    exploration_generation INTEGER NOT NULL DEFAULT 1 CHECK(exploration_generation>=1),
    exploration_paused INTEGER NOT NULL DEFAULT 0 CHECK(exploration_paused IN (0,1)),
    backfilled_at INTEGER,
    updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS member_interests (
    account_id TEXT NOT NULL REFERENCES accounts(id),
    category_id TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    PRIMARY KEY(account_id, category_id)
);
CREATE TABLE IF NOT EXISTS member_bookmarks (
    account_id TEXT NOT NULL REFERENCES accounts(id),
    discovery_id TEXT NOT NULL,
    saved_at INTEGER NOT NULL,
    PRIMARY KEY(account_id, discovery_id)
);
CREATE INDEX IF NOT EXISTS idx_member_bookmarks_order ON member_bookmarks(account_id, saved_at DESC, discovery_id DESC);
CREATE TABLE IF NOT EXISTS member_exploration (
    account_id TEXT NOT NULL REFERENCES accounts(id),
    discovery_id TEXT NOT NULL,
    first_opened_at INTEGER NOT NULL,
    last_opened_at INTEGER NOT NULL,
    open_count INTEGER NOT NULL DEFAULT 1 CHECK(open_count>=1),
    generation INTEGER NOT NULL DEFAULT 1 CHECK(generation>=1),
    item_version INTEGER NOT NULL DEFAULT 1 CHECK(item_version>=1),
    PRIMARY KEY(account_id, discovery_id)
);
CREATE INDEX IF NOT EXISTS idx_member_exploration_order ON member_exploration(account_id, last_opened_at DESC, discovery_id DESC);
CREATE TABLE IF NOT EXISTS member_exploration_tombstones (
    account_id TEXT NOT NULL REFERENCES accounts(id),
    discovery_id TEXT NOT NULL,
    removed_at INTEGER NOT NULL,
    removed_generation INTEGER NOT NULL CHECK(removed_generation>=1),
    item_version INTEGER NOT NULL CHECK(item_version>=1),
    PRIMARY KEY(account_id, discovery_id)
);
CREATE TABLE IF NOT EXISTS member_exploration_events (
    account_id TEXT NOT NULL REFERENCES accounts(id),
    event_id TEXT NOT NULL,
    discovery_id TEXT NOT NULL,
    history_generation INTEGER NOT NULL CHECK(history_generation>=1),
    created_at INTEGER NOT NULL,
    PRIMARY KEY(account_id, event_id)
);
CREATE TABLE IF NOT EXISTS account_entitlements (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    kind TEXT NOT NULL CHECK(kind IN ('site_plan','purchase','live_channel')),
    target_id TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('active','revoked','expired')),
    starts_at INTEGER,
    ends_at INTEGER,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_account_entitlements_lookup ON account_entitlements(account_id, kind, state);
CREATE TABLE IF NOT EXISTS mission_campaigns (
    id TEXT PRIMARY KEY,
    total_budget_kp INTEGER NOT NULL CHECK(total_budget_kp>=0),
    reserved_kp INTEGER NOT NULL DEFAULT 0 CHECK(reserved_kp>=0),
    consumed_kp INTEGER NOT NULL DEFAULT 0 CHECK(consumed_kp>=0),
    per_account_limit_kp INTEGER NOT NULL CHECK(per_account_limit_kp>=0),
    starts_at INTEGER NOT NULL,
    ends_at INTEGER NOT NULL CHECK(ends_at>starts_at),
    state TEXT NOT NULL CHECK(state IN ('draft','active','new_activity_paused','maintenance','closed')),
    CHECK(reserved_kp + consumed_kp <= total_budget_kp)
);
CREATE TABLE IF NOT EXISTS mission_attempts (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    mission_id TEXT NOT NULL,
    mission_version INTEGER NOT NULL,
    occurrence_key TEXT NOT NULL,
    campaign_id TEXT NOT NULL REFERENCES mission_campaigns(id),
    definition_hash TEXT NOT NULL,
    award_kp INTEGER NOT NULL CHECK(award_kp>0 AND award_kp<=500),
    state TEXT NOT NULL CHECK(state IN ('active','submitted','failed','expired','completed')),
    attempt_number INTEGER NOT NULL CHECK(attempt_number>=1),
    expires_at INTEGER NOT NULL,
    submitted_at INTEGER,
    result_code TEXT,
    pending_id TEXT,
    receipt_id TEXT,
    created_at INTEGER NOT NULL,
    FOREIGN KEY(mission_id, mission_version) REFERENCES missions(id, version)
);
CREATE INDEX IF NOT EXISTS idx_mission_attempts_account ON mission_attempts(account_id, mission_id, created_at DESC);
CREATE TABLE IF NOT EXISTS mission_pending_claims (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    attempt_id TEXT NOT NULL UNIQUE REFERENCES mission_attempts(id),
    mission_id TEXT NOT NULL,
    mission_version INTEGER NOT NULL,
    occurrence_key TEXT NOT NULL,
    campaign_id TEXT NOT NULL REFERENCES mission_campaigns(id),
    evidence_id TEXT NOT NULL UNIQUE REFERENCES mission_evidence(id),
    award_kp INTEGER NOT NULL CHECK(award_kp>0 AND award_kp<=500),
    reservation_state TEXT NOT NULL CHECK(reservation_state IN ('reserved','consumed','released')),
    expires_at INTEGER NOT NULL,
    claimed_at INTEGER,
    released_at INTEGER,
    receipt_id TEXT,
    created_at INTEGER NOT NULL,
    FOREIGN KEY(mission_id, mission_version) REFERENCES missions(id, version)
);
CREATE INDEX IF NOT EXISTS idx_mission_pending_account ON mission_pending_claims(account_id, reservation_state, expires_at);
CREATE TABLE IF NOT EXISTS mission_receipts (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    completion_id TEXT NOT NULL UNIQUE REFERENCES completions(id),
    ledger_id TEXT NOT NULL UNIQUE REFERENCES ledger(id),
    pending_id TEXT NOT NULL UNIQUE REFERENCES mission_pending_claims(id),
    attempt_id TEXT NOT NULL UNIQUE REFERENCES mission_attempts(id),
    mission_id TEXT NOT NULL,
    mission_version INTEGER NOT NULL,
    occurrence_key TEXT NOT NULL,
    award_kp INTEGER NOT NULL CHECK(award_kp>0 AND award_kp<=500),
    support_ref TEXT NOT NULL UNIQUE,
    created_at INTEGER NOT NULL,
    UNIQUE(account_id, mission_id, occurrence_key)
);
CREATE TABLE IF NOT EXISTS idempotent_operations (
    account_id TEXT NOT NULL REFERENCES accounts(id),
    operation_type TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    operation_id TEXT NOT NULL UNIQUE,
    payload_hash TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    response_json TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    PRIMARY KEY(account_id, operation_type, idempotency_key)
);
