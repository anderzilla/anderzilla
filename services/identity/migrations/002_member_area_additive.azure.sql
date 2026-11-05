-- Additive Azure SQL migration for Member Area & Single Wallet (Lotes 2-4)
-- Prepared for operator execution after homolog validation; do NOT auto-run in production without operator gate.

IF OBJECT_ID('dbo.member_collection_state', 'U') IS NULL
CREATE TABLE dbo.member_collection_state (
  account_id VARCHAR(64) PRIMARY KEY REFERENCES dbo.accounts(id),
  interests_version INT NOT NULL DEFAULT 1,
  exploration_generation INT NOT NULL DEFAULT 1,
  backfilled_at VARCHAR(40) NULL,
  updated_at VARCHAR(40) NOT NULL
);

IF OBJECT_ID('dbo.member_interests', 'U') IS NULL
CREATE TABLE dbo.member_interests (
  account_id VARCHAR(64) NOT NULL REFERENCES dbo.accounts(id),
  category VARCHAR(40) NOT NULL,
  created_at VARCHAR(40) NOT NULL,
  CONSTRAINT PK_member_interests PRIMARY KEY (account_id, category)
);

IF OBJECT_ID('dbo.member_bookmarks', 'U') IS NULL
CREATE TABLE dbo.member_bookmarks (
  account_id VARCHAR(64) NOT NULL REFERENCES dbo.accounts(id),
  discovery_id VARCHAR(120) NOT NULL,
  saved_at VARCHAR(40) NOT NULL,
  updated_at VARCHAR(40) NOT NULL,
  CONSTRAINT PK_member_bookmarks PRIMARY KEY (account_id, discovery_id)
);

IF OBJECT_ID('dbo.member_exploration', 'U') IS NULL
CREATE TABLE dbo.member_exploration (
  account_id VARCHAR(64) NOT NULL REFERENCES dbo.accounts(id),
  discovery_id VARCHAR(120) NOT NULL,
  first_opened_at VARCHAR(40) NOT NULL,
  last_opened_at VARCHAR(40) NOT NULL,
  last_item_version VARCHAR(64) NOT NULL,
  open_count INT NOT NULL DEFAULT 1,
  history_generation INT NOT NULL DEFAULT 1,
  CONSTRAINT PK_member_exploration PRIMARY KEY (account_id, discovery_id)
);

IF OBJECT_ID('dbo.member_exploration_tombstones', 'U') IS NULL
CREATE TABLE dbo.member_exploration_tombstones (
  account_id VARCHAR(64) NOT NULL REFERENCES dbo.accounts(id),
  discovery_id VARCHAR(120) NOT NULL,
  deleted_at VARCHAR(40) NOT NULL,
  min_generation INT NOT NULL,
  CONSTRAINT PK_member_exploration_tombstones PRIMARY KEY (account_id, discovery_id)
);

IF OBJECT_ID('dbo.member_exploration_events', 'U') IS NULL
CREATE TABLE dbo.member_exploration_events (
  account_id VARCHAR(64) NOT NULL REFERENCES dbo.accounts(id),
  event_key VARCHAR(160) NOT NULL,
  discovery_id VARCHAR(120) NOT NULL,
  item_version VARCHAR(64) NOT NULL,
  history_generation INT NOT NULL,
  recorded_at VARCHAR(40) NOT NULL,
  CONSTRAINT PK_member_exploration_events PRIMARY KEY (account_id, event_key)
);

IF OBJECT_ID('dbo.account_entitlements', 'U') IS NULL
CREATE TABLE dbo.account_entitlements (
  account_id VARCHAR(64) NOT NULL REFERENCES dbo.accounts(id),
  entitlement_key VARCHAR(120) NOT NULL,
  status VARCHAR(32) NOT NULL,
  granted_at VARCHAR(40) NOT NULL,
  expires_at VARCHAR(40) NULL,
  CONSTRAINT PK_account_entitlements PRIMARY KEY (account_id, entitlement_key)
);

IF OBJECT_ID('dbo.mission_campaigns', 'U') IS NULL
CREATE TABLE dbo.mission_campaigns (
  mission_id VARCHAR(80) NOT NULL,
  mission_version INT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  total_budget_kp INT NOT NULL,
  reserved_kp INT NOT NULL DEFAULT 0,
  consumed_kp INT NOT NULL DEFAULT 0,
  per_account_limit INT NOT NULL DEFAULT 1,
  starts_at VARCHAR(40) NULL,
  ends_at VARCHAR(40) NULL,
  updated_at VARCHAR(40) NOT NULL,
  CONSTRAINT PK_mission_campaigns PRIMARY KEY (mission_id, mission_version),
  CONSTRAINT CK_mission_campaigns_budget CHECK (
    total_budget_kp >= 0 AND reserved_kp >= 0 AND consumed_kp >= 0 AND reserved_kp + consumed_kp <= total_budget_kp
  )
);

IF OBJECT_ID('dbo.mission_attempts', 'U') IS NULL
CREATE TABLE dbo.mission_attempts (
  attempt_id VARCHAR(64) PRIMARY KEY,
  account_id VARCHAR(64) NOT NULL REFERENCES dbo.accounts(id),
  mission_id VARCHAR(80) NOT NULL,
  mission_version INT NOT NULL,
  challenge_id VARCHAR(120) NOT NULL UNIQUE,
  status VARCHAR(32) NOT NULL,
  questions_json NVARCHAR(MAX) NOT NULL,
  issued_at VARCHAR(40) NOT NULL,
  expires_at VARCHAR(40) NOT NULL,
  updated_at VARCHAR(40) NOT NULL
);

IF OBJECT_ID('dbo.mission_pending_claims', 'U') IS NULL
CREATE TABLE dbo.mission_pending_claims (
  pending_id VARCHAR(64) PRIMARY KEY,
  attempt_id VARCHAR(64) NOT NULL UNIQUE REFERENCES dbo.mission_attempts(attempt_id),
  account_id VARCHAR(64) NOT NULL REFERENCES dbo.accounts(id),
  mission_id VARCHAR(80) NOT NULL,
  mission_version INT NOT NULL,
  occurrence_key VARCHAR(80) NOT NULL,
  award_kp INT NOT NULL CHECK (award_kp >= 0),
  pending_token NVARCHAR(MAX) NOT NULL,
  evidence_ref VARCHAR(120) NOT NULL UNIQUE,
  status VARCHAR(32) NOT NULL,
  reservation_state VARCHAR(32) NOT NULL,
  issued_at VARCHAR(40) NOT NULL,
  expires_at VARCHAR(40) NOT NULL,
  updated_at VARCHAR(40) NOT NULL
);

IF OBJECT_ID('dbo.mission_receipts', 'U') IS NULL
CREATE TABLE dbo.mission_receipts (
  receipt_id VARCHAR(64) PRIMARY KEY,
  account_id VARCHAR(64) NOT NULL REFERENCES dbo.accounts(id),
  mission_id VARCHAR(80) NOT NULL,
  mission_version INT NOT NULL,
  occurrence_key VARCHAR(80) NOT NULL,
  pending_id VARCHAR(64) NOT NULL UNIQUE,
  ledger_entry_id VARCHAR(64) NOT NULL UNIQUE,
  awarded_kp INT NOT NULL CHECK (awarded_kp >= 0),
  completed_at VARCHAR(40) NOT NULL,
  CONSTRAINT UQ_mission_receipt_occurrence UNIQUE (account_id, mission_id, mission_version, occurrence_key)
);

IF OBJECT_ID('dbo.idempotent_operations', 'U') IS NULL
CREATE TABLE dbo.idempotent_operations (
  operation_id VARCHAR(64) PRIMARY KEY,
  account_id VARCHAR(64) NOT NULL REFERENCES dbo.accounts(id),
  operation_type VARCHAR(40) NOT NULL,
  idempotency_key VARCHAR(120) NOT NULL,
  payload_hash CHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL,
  response_status INT NOT NULL,
  response_json NVARCHAR(MAX) NOT NULL,
  created_at VARCHAR(40) NOT NULL,
  updated_at VARCHAR(40) NOT NULL,
  CONSTRAINT UQ_idempotent_account_op UNIQUE (account_id, operation_type, idempotency_key)
);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_member_bookmarks_account_saved' AND object_id = OBJECT_ID('dbo.member_bookmarks'))
CREATE INDEX idx_member_bookmarks_account_saved ON dbo.member_bookmarks(account_id, saved_at DESC, discovery_id ASC);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_member_exploration_account_opened' AND object_id = OBJECT_ID('dbo.member_exploration'))
CREATE INDEX idx_member_exploration_account_opened ON dbo.member_exploration(account_id, last_opened_at DESC, discovery_id ASC);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_mission_attempts_account' AND object_id = OBJECT_ID('dbo.mission_attempts'))
CREATE INDEX idx_mission_attempts_account ON dbo.mission_attempts(account_id, mission_id, mission_version, status);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_mission_pending_claims_account' AND object_id = OBJECT_ID('dbo.mission_pending_claims'))
CREATE INDEX idx_mission_pending_claims_account ON dbo.mission_pending_claims(account_id, status, expires_at);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'idx_ledger_account_created' AND object_id = OBJECT_ID('dbo.ledger'))
CREATE INDEX idx_ledger_account_created ON dbo.ledger(account_id, created_at DESC, id ASC);
