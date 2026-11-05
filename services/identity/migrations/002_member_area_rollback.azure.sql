-- Application rollback only: retain all additive tables, user collections and ledger.
-- Schema removal needs a separate reviewed migration and backup.
THROW 51002, 'Destructive schema rollback disabled. Restore a compatible application release and retain member data.', 1;
