"""Operator tool for per-agent API keys. Runs on the owner's machine, never as an HTTP endpoint.

  list    read-only: id, name, scopes, dates and revoked flag (the stored hash is never read)
  create  dry run unless --apply; with --apply the new key is shown ONCE (or copied with --clipboard) and never stored
  revoke  dry run unless --apply

Database credentials come from CMS_SQL_* environment variables, set only for this process by content-key.ps1.
Keys are minted under the explicit operator identity `operator:key-issuer`, which the audit trail records."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
for candidate in (HERE, HERE.parent / 'cms'):
    if (candidate / 'agent_api.py').is_file() or (candidate / 'core.py').is_file():
        sys.path.insert(0, str(candidate))
from agent_api import AGENT_COLLECTIONS, AgentGateway
from core import CMS, Error

OPERATOR = {'id': 'operator:key-issuer', 'name': 'Key issuer (local operator)', 'roles': ['anderzilla_admin']}


def default_store(environment):
    expected = f'anderzilla-cms-{environment}'
    if os.environ.get('CMS_SQL_DATABASE') != expected:
        raise SystemExit(f'Refusing to run: CMS_SQL_DATABASE must be {expected} for the {environment} environment.')
    from storage import AzureSQLStore
    return AzureSQLStore()


def copy_to_clipboard(text):
    if sys.platform != 'win32':
        raise SystemExit('--clipboard is only supported on Windows.')
    subprocess.run(['clip'], input=text.encode('ascii'), check=True)


def run(argv, store_factory=default_store, out=print, clipboard=copy_to_clipboard):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['list', 'create', 'revoke'])
    parser.add_argument('--environment', choices=['homolog', 'production'], required=True)
    parser.add_argument('--name')
    parser.add_argument('--days', type=int, default=90)
    parser.add_argument('--collections', default=','.join(AGENT_COLLECTIONS), help='comma separated subset of ' + ', '.join(AGENT_COLLECTIONS))
    parser.add_argument('--id')
    parser.add_argument('--clipboard', action='store_true', help='copy the key instead of printing it')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    if args.action == 'create':
        if not args.name:
            parser.error('create needs --name')
        scopes = sorted({item.strip() for item in args.collections.split(',') if item.strip()})
        if not 1 <= args.days <= 365 or not scopes or set(scopes) - set(AGENT_COLLECTIONS):
            parser.error('days must be 1-365 and collections a subset of ' + ', '.join(AGENT_COLLECTIONS))
        out(f'Plan: create an agent key named "{args.name}" for {args.environment}, scopes {", ".join(scopes)}, valid {args.days} days. The key cannot approve or publish.')
        if not args.apply:
            out('Dry run only. No database connection was opened.')
            return 0
        gateway = AgentGateway(CMS(store_factory(args.environment)))
        issued = gateway.create_key(OPERATOR, args.name, args.days, scopes)
        out(f'Created key {issued["id"]} (expires {issued["expiresAt"][:10]}).')
        if args.clipboard:
            clipboard(issued['key'])
            out('The key is in your clipboard and was NOT printed. Paste it where the agent reads it, then clear the clipboard.')
        else:
            out('SHOW-ONCE KEY (it is not stored anywhere and cannot be recovered):')
            out(issued['key'])
        return 0
    if args.action == 'list':
        with store_factory(args.environment).transaction() as db:
            keys = db.agent_keys()
        if not keys:
            out('No agent keys.')
        for key in keys:
            out(f'{key["id"]}  {key["name"]}  scopes={",".join(key["scopes"])}  expires={key["expiresAt"][:10]}  revoked={key["revoked"]}')
        return 0
    if not args.id:
        parser.error('revoke needs --id')
    out(f'Plan: revoke key {args.id} in {args.environment}.')
    if not args.apply:
        out('Dry run only. No database connection was opened.')
        return 0
    try:
        AgentGateway(CMS(store_factory(args.environment))).revoke_key(OPERATOR, args.id)
    except Error as error:
        out(f'Not revoked: {error}')
        return 1
    out(f'Revoked {args.id}.')
    return 0


if __name__ == '__main__':
    sys.exit(run(sys.argv[1:]))
