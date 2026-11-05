-- Rollback script for Member Area additive tables (002_member_area_additive.azure.sql)
-- WARNING: Never drop append-only audit_events, ledger, wallets, or mission_completions.
-- Only drops new additive member collection and campaign tracking tables if zero receipts exist.

IF EXISTS (SELECT 1 FROM dbo.mission_receipts)
BEGIN
  RAISERROR('Cannot rollback 002_member_area_additive when mission_receipts contains confirmed KP awards.', 16, 1);
  RETURN;
END;

IF OBJECT_ID('dbo.idempotent_operations', 'U') IS NOT NULL DROP TABLE dbo.idempotent_operations;
IF OBJECT_ID('dbo.mission_receipts', 'U') IS NOT NULL DROP TABLE dbo.mission_receipts;
IF OBJECT_ID('dbo.mission_pending_claims', 'U') IS NOT NULL DROP TABLE dbo.mission_pending_claims;
IF OBJECT_ID('dbo.mission_attempts', 'U') IS NOT NULL DROP TABLE dbo.mission_attempts;
IF OBJECT_ID('dbo.mission_campaigns', 'U') IS NOT NULL DROP TABLE dbo.mission_campaigns;
IF OBJECT_ID('dbo.account_entitlements', 'U') IS NOT NULL DROP TABLE dbo.account_entitlements;
IF OBJECT_ID('dbo.member_exploration_events', 'U') IS NOT NULL DROP TABLE dbo.member_exploration_events;
IF OBJECT_ID('dbo.member_exploration_tombstones', 'U') IS NOT NULL DROP TABLE dbo.member_exploration_tombstones;
IF OBJECT_ID('dbo.member_exploration', 'U') IS NOT NULL DROP TABLE dbo.member_exploration;
IF OBJECT_ID('dbo.member_bookmarks', 'U') IS NOT NULL DROP TABLE dbo.member_bookmarks;
IF OBJECT_ID('dbo.member_interests', 'U') IS NOT NULL DROP TABLE dbo.member_interests;
IF OBJECT_ID('dbo.member_collection_state', 'U') IS NOT NULL DROP TABLE dbo.member_collection_state;
