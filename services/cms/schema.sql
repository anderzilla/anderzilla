CREATE TABLE IF NOT EXISTS cms_records(collection TEXT NOT NULL,id TEXT NOT NULL,updated_at TEXT NOT NULL,document TEXT NOT NULL,PRIMARY KEY(collection,id));
CREATE TABLE IF NOT EXISTS cms_revisions(collection TEXT NOT NULL,id TEXT NOT NULL,version INTEGER NOT NULL,document TEXT NOT NULL,PRIMARY KEY(collection,id,version));
CREATE TABLE IF NOT EXISTS cms_audit(id TEXT PRIMARY KEY,created_at TEXT NOT NULL,document TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cms_releases(id TEXT PRIMARY KEY,request_key TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL,document TEXT NOT NULL,snapshot TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS automation_processes(id TEXT NOT NULL,version INTEGER NOT NULL,document TEXT NOT NULL,PRIMARY KEY(id,version));
CREATE TABLE IF NOT EXISTS automation_runs(id TEXT PRIMARY KEY,environment TEXT NOT NULL,process_id TEXT NOT NULL,created_at TEXT NOT NULL,status TEXT NOT NULL,document TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_automation_runs_env ON automation_runs(environment,created_at,id);
CREATE INDEX IF NOT EXISTS ix_automation_runs_list ON automation_runs(environment,process_id,status,created_at DESC,id DESC);
CREATE TABLE IF NOT EXISTS automation_commands(environment TEXT NOT NULL,actor_id TEXT NOT NULL,request_key TEXT NOT NULL,input_hash TEXT NOT NULL,document TEXT NOT NULL,PRIMARY KEY(environment,actor_id,request_key));
