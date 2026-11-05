"""Operator-only commands. Use separate privileged SQL credentials, never visitor HTTP.

Run with python -m services.identity.managed_operator ban ACCOUNT_ID --actor NAME
--reason TEXT. Account IDs are opaque; never provide CPF, email or tokens in arguments.
Environment configuration is supplied out of band. This command never prints credentials.
"""
import argparse
import json

from .clerk_auth import ClerkGateway, settings
from .clerk_service import ClerkAccountService
from .core import Rejected
from .storage import AzureSQLStore


def run_ban(store, gateway, cfg, account_id, actor, reason):
    service = ClerkAccountService(store, cfg)
    # Local state and blocked identifiers are authoritative even if Clerk is unavailable.
    service.ban_account(account_id, actor, reason)
    with store.transaction() as db:
        row = db.execute('SELECT subject FROM managed_identities WHERE account_id=?', (account_id,)).fetchone()
    gateway.ban_user(row['subject'])
    return {'accountId': account_id, 'localAccessBlocked': True, 'providerBanned': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    ban = commands.add_parser('ban')
    ban.add_argument('account_id')
    ban.add_argument('--actor', required=True)
    ban.add_argument('--reason', required=True)
    commands.add_parser('pending-deletions')
    retry = commands.add_parser('finish-deletion')
    retry.add_argument('account_id')
    args = parser.parse_args()
    cfg = settings()
    if not cfg['ok']:
        parser.error('Operator environment is not configured; no values were printed.')
    store, gateway = AzureSQLStore(), ClerkGateway(cfg)
    try:
        if args.command == 'ban':
            result = run_ban(store, gateway, cfg, args.account_id, args.actor, args.reason)
        elif args.command == 'pending-deletions':
            with store.transaction() as db:
                result = db.execute('SELECT account_id,requested_at FROM managed_deletions WHERE completed_at IS NULL').fetchall()
        else:
            with store.transaction() as db:
                row = db.execute('SELECT subject FROM managed_deletions WHERE account_id=? AND completed_at IS NULL', (args.account_id,)).fetchone()
            if not row:
                parser.error('No pending deletion for this account.')
            try:
                gateway.delete_user(row['subject'])
            except Rejected as exc:
                # A user already absent from Clerk is a completed remote deletion.
                if exc.status != 401:
                    raise
            ClerkAccountService(store, cfg).finish_delete(args.account_id)
            result = {'accountId': args.account_id, 'completed': True}
        print(json.dumps(result))
    except Exception:
        # Preserve the actionable local blocking state without printing PII/provider errors.
        print(json.dumps({'completed': False, 'message': 'Operator command incomplete. Check local state and retry; no credentials were printed.'}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
