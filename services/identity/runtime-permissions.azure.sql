-- Contained runtime user created separately, no DDL rights.
GRANT SELECT, INSERT, UPDATE ON OBJECT::dbo.accounts TO anderzilla_identity_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON OBJECT::dbo.email_verifications TO anderzilla_identity_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON OBJECT::dbo.oauth_identities TO anderzilla_identity_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON OBJECT::dbo.oauth_nonces TO anderzilla_identity_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON OBJECT::dbo.sessions TO anderzilla_identity_runtime;
GRANT SELECT, INSERT, UPDATE ON OBJECT::dbo.wallets TO anderzilla_identity_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON OBJECT::dbo.preferences_bookmarks TO anderzilla_identity_runtime;
GRANT SELECT ON OBJECT::dbo.missions TO anderzilla_identity_runtime;
GRANT SELECT, INSERT, UPDATE ON OBJECT::dbo.challenges TO anderzilla_identity_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON OBJECT::dbo.mission_evidence TO anderzilla_identity_runtime;
GRANT SELECT, INSERT, UPDATE ON OBJECT::dbo.pending_rewards TO anderzilla_identity_runtime;
GRANT SELECT, INSERT ON OBJECT::dbo.completions TO anderzilla_identity_runtime;
GRANT SELECT, INSERT ON OBJECT::dbo.ledger TO anderzilla_identity_runtime;
GRANT SELECT, INSERT ON OBJECT::dbo.requests TO anderzilla_identity_runtime;
GRANT SELECT, INSERT, UPDATE ON OBJECT::dbo.rate_limits TO anderzilla_identity_runtime;
GRANT SELECT, INSERT ON OBJECT::dbo.consents TO anderzilla_identity_runtime;
DENY UPDATE, DELETE ON OBJECT::dbo.ledger TO anderzilla_identity_runtime;
DENY UPDATE, DELETE ON OBJECT::dbo.completions TO anderzilla_identity_runtime;

-- No visitor permission to create bans; operator uses a separate privileged SQL identity.
GRANT SELECT, INSERT ON OBJECT::dbo.managed_identities TO anderzilla_identity_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON OBJECT::dbo.managed_profiles TO anderzilla_identity_runtime;
GRANT SELECT ON OBJECT::dbo.managed_bans TO anderzilla_identity_runtime;
GRANT SELECT, INSERT ON OBJECT::dbo.managed_audit TO anderzilla_identity_runtime;
GRANT SELECT, INSERT, UPDATE ON OBJECT::dbo.managed_deletions TO anderzilla_identity_runtime;
GRANT SELECT, INSERT ON OBJECT::dbo.managed_webhook_receipts TO anderzilla_identity_runtime;
