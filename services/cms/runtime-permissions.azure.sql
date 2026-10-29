-- Run after creating the contained SQL user anderzilla_cms_runtime securely.
-- Never grant db_owner/db_datawriter to the application user.
GRANT SELECT, INSERT, UPDATE ON OBJECT::dbo.cms_records TO anderzilla_cms_runtime;
GRANT SELECT, INSERT ON OBJECT::dbo.cms_revisions TO anderzilla_cms_runtime;
GRANT SELECT, INSERT ON OBJECT::dbo.cms_audit TO anderzilla_cms_runtime;
GRANT SELECT, INSERT ON OBJECT::dbo.cms_releases TO anderzilla_cms_runtime;
GRANT UPDATE ON OBJECT::dbo.cms_releases(document) TO anderzilla_cms_runtime;
DENY DELETE ON OBJECT::dbo.cms_records TO anderzilla_cms_runtime;
DENY UPDATE, DELETE ON OBJECT::dbo.cms_revisions TO anderzilla_cms_runtime;
DENY UPDATE, DELETE ON OBJECT::dbo.cms_audit TO anderzilla_cms_runtime;
DENY DELETE ON OBJECT::dbo.cms_releases TO anderzilla_cms_runtime;
GRANT SELECT, INSERT ON OBJECT::dbo.automation_processes TO anderzilla_cms_runtime;
GRANT SELECT, INSERT, UPDATE ON OBJECT::dbo.automation_runs TO anderzilla_cms_runtime;
GRANT SELECT, INSERT ON OBJECT::dbo.automation_commands TO anderzilla_cms_runtime;
DENY UPDATE, DELETE ON OBJECT::dbo.automation_processes TO anderzilla_cms_runtime;
DENY DELETE ON OBJECT::dbo.automation_runs TO anderzilla_cms_runtime;
DENY UPDATE, DELETE ON OBJECT::dbo.automation_commands TO anderzilla_cms_runtime;
GRANT SELECT, INSERT ON OBJECT::dbo.agent_keys TO anderzilla_cms_runtime;
GRANT UPDATE ON OBJECT::dbo.agent_keys(document) TO anderzilla_cms_runtime;
DENY DELETE ON OBJECT::dbo.agent_keys TO anderzilla_cms_runtime;
GRANT SELECT, INSERT ON OBJECT::dbo.agent_requests TO anderzilla_cms_runtime;
DENY UPDATE, DELETE ON OBJECT::dbo.agent_requests TO anderzilla_cms_runtime;
GRANT SELECT, INSERT, UPDATE ON OBJECT::dbo.submissions TO anderzilla_cms_runtime;
DENY DELETE ON OBJECT::dbo.submissions TO anderzilla_cms_runtime;
GRANT SELECT, INSERT ON OBJECT::dbo.submission_comments TO anderzilla_cms_runtime;
GRANT UPDATE ON OBJECT::dbo.submission_comments(document) TO anderzilla_cms_runtime;
DENY DELETE ON OBJECT::dbo.submission_comments TO anderzilla_cms_runtime;