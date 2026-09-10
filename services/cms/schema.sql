CREATE TABLE IF NOT EXISTS cms_records(collection TEXT NOT NULL,id TEXT NOT NULL,updated_at TEXT NOT NULL,document TEXT NOT NULL,PRIMARY KEY(collection,id));
CREATE TABLE IF NOT EXISTS cms_revisions(collection TEXT NOT NULL,id TEXT NOT NULL,version INTEGER NOT NULL,document TEXT NOT NULL,PRIMARY KEY(collection,id,version));
CREATE TABLE IF NOT EXISTS cms_audit(id TEXT PRIMARY KEY,created_at TEXT NOT NULL,document TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cms_releases(id TEXT PRIMARY KEY,request_key TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL,document TEXT NOT NULL,snapshot TEXT NOT NULL);
