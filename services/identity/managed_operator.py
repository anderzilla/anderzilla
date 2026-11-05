"""Operator-only commands. Use separate privileged SQL credentials, never visitor HTTP.

Run with python -m services.identity.managed_operator <command>.
Account IDs are opaque; never provide CPF, email or tokens in arguments.
Environment configuration is supplied out of band. This command never prints credentials.
"""
import argparse
import json

from .clerk_auth import ClerkGateway, settings
from .clerk_service import ClerkAccountService
from .core import Rejected
from .member_service import MemberAreaService
from .storage import AzureSQLStore


def run_ban(store, gateway, cfg, account_id, actor, reason):
    service = ClerkAccountService(store, cfg)
    service.ban_account(account_id, actor, reason)
    with store.transaction() as db:
        row = db.execute(
            'SELECT subject FROM managed_identities WHERE account_id=?',
            (account_id,),
        ).fetchone()
    gateway.ban_user(row['subject'])
    return {'accountId': account_id, 'localAccessBlocked': True, 'providerBanned': True}


def reconcile_wallets(store) -> dict:
    """Verify wallet balances against append-only ledger and campaign budgets against pending/receipts."""
    wallet_mismatches = []
    campaign_mismatches = []
    with store.transaction() as db:
        wallets = db.execute(
            'SELECT account_id,available,reserved FROM wallets'
        ).fetchall()
        for w in wallets:
            aid = w['account_id']
            sums = db.execute(
                'SELECT COALESCE(SUM(available_delta),0) AS avail_sum,'
                'COALESCE(SUM(reserved_delta),0) AS res_sum '
                'FROM ledger WHERE account_id=?',
                (aid,),
            ).fetchone()
            avail_sum = int(sums['avail_sum'] or 0)
            res_sum = int(sums['res_sum'] or 0)
            if int(w['available']) != avail_sum or int(w['reserved']) != res_sum:
                wallet_mismatches.append({
                    'accountId': aid,
                    'walletAvailable': int(w['available']),
                    'ledgerAvailable': avail_sum,
                    'walletReserved': int(w['reserved']),
                    'ledgerReserved': res_sum,
                })

        campaigns = db.execute(
            'SELECT id,total_budget_kp,reserved_kp,consumed_kp FROM mission_campaigns'
        ).fetchall()
        for c in campaigns:
            cid = c['id']
            res_row = db.execute(
                "SELECT COALESCE(SUM(award_kp),0) AS c FROM mission_pending_claims "
                "WHERE campaign_id=? AND reservation_state='reserved'",
                (cid,),
            ).fetchone()
            con_row = db.execute(
                "SELECT COALESCE(SUM(award_kp),0) AS c FROM mission_pending_claims "
                "WHERE campaign_id=? AND reservation_state='consumed'",
                (cid,),
            ).fetchone()
            expected_res = int(res_row['c'] or 0)
            expected_con = int(con_row['c'] or 0)
            if int(c['reserved_kp']) != expected_res or int(c['consumed_kp']) != expected_con:
                campaign_mismatches.append({
                    'campaignId': cid,
                    'campaignReserved': int(c['reserved_kp']),
                    'expectedReserved': expected_res,
                    'campaignConsumed': int(c['consumed_kp']),
                    'expectedConsumed': expected_con,
                })

    return {
        'ok': len(wallet_mismatches) == 0 and len(campaign_mismatches) == 0,
        'walletsChecked': len(wallets),
        'campaignsChecked': len(campaigns),
        'walletMismatches': wallet_mismatches,
        'campaignMismatches': campaign_mismatches,
    }


def release_expired_claims(store, cfg, clock=None) -> dict:
    """Release expired pending claim reservations across all accounts."""
    member_svc = MemberAreaService(store, cfg, clock=clock)
    with store.transaction() as db:
        released_now = member_svc._release_expired_pending_claims(db)
        released_count = db.execute(
            "SELECT COUNT(*) AS c FROM mission_pending_claims WHERE reservation_state='released'"
        ).fetchone()
    return {
        'ok': True,
        'releasedNow': released_now,
        'expiredReleasedTotal': int(released_count['c'] or 0),
    }


def backfill_collections(store, cfg, clock=None) -> dict:
    """Run idempotent additive backfill from preferences_bookmarks to relational member tables."""
    member_svc = MemberAreaService(store, cfg, clock=clock)
    backfilled = 0
    with store.transaction() as db:
        rows = db.execute('SELECT id FROM accounts').fetchall()
        for r in rows:
            member_svc._ensure_collection_state(db, r['id'])
            backfilled += 1
    return {
        'ok': True,
        'accountsProcessed': backfilled,
    }


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
    commands.add_parser('reconcile-wallets')
    commands.add_parser('release-expired-claims')
    commands.add_parser('backfill-collections')
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
                result = db.execute(
                    'SELECT account_id,requested_at FROM managed_deletions WHERE completed_at IS NULL'
                ).fetchall()
        elif args.command == 'finish-deletion':
            with store.transaction() as db:
                row = db.execute(
                    'SELECT subject FROM managed_deletions WHERE account_id=? AND completed_at IS NULL',
                    (args.account_id,),
                ).fetchone()
            if not row:
                parser.error('No pending deletion for this account.')
            try:
                gateway.delete_user(row['subject'])
            except Rejected as exc:
                if exc.status != 401:
                    raise
            ClerkAccountService(store, cfg).finish_delete(args.account_id)
            result = {'accountId': args.account_id, 'completed': True}
        elif args.command == 'reconcile-wallets':
            result = reconcile_wallets(store)
        elif args.command == 'release-expired-claims':
            result = release_expired_claims(store, cfg)
        else:
            result = backfill_collections(store, cfg)
        print(json.dumps(result))
    except Exception:
        print(json.dumps({
            'completed': False,
            'message': 'Operator command incomplete. Check local state and retry; no credentials were printed.',
        }))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
