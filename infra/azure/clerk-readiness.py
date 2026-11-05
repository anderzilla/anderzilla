"""Read-only Clerk release gate. Reads private settings; never prints their values.

python infra/azure/clerk-readiness.py --environment production --settings C:/private/settings.json
The private file may be a flat JSON object or an ARM {"properties": {...}} object.
This command does not configure Azure, create accounts, or deploy anything.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = (
    'IDENTITY_AUTH_PROVIDER', 'IDENTITY_ENV', 'IDENTITY_ALLOWED_ORIGIN',
    'IDENTITY_SQL_SERVER', 'IDENTITY_SQL_DATABASE', 'IDENTITY_SQL_USER',
    'IDENTITY_SQL_PASSWORD', 'IDENTITY_CPF_HMAC_KEY', 'CLERK_ISSUER',
    'CLERK_SECRET_KEY', 'CLERK_JWT_KEY', 'CLERK_WEBHOOK_SIGNING_SECRET',
    'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY', 'NEXT_PUBLIC_ACCOUNT_API_BASE',
)


def origin(value):
    try:
        p = urlsplit(value)
        return p.scheme == 'https' and bool(p.hostname) and not any(
            (p.username, p.password, p.query, p.fragment, p.path not in ('', '/')))
    except (ValueError, TypeError):
        return False


def inspect(values, environment):
    errors = []
    if not isinstance(values, dict):
        return ['settings_object_required']
    missing = [key for key in REQUIRED if not isinstance(values.get(key), str) or not values[key]]
    errors.extend('missing:' + key for key in missing)
    if missing:
        return errors
    if values['IDENTITY_AUTH_PROVIDER'] != 'clerk' or values['IDENTITY_ENV'] != environment:
        errors.append('wrong_provider_or_environment')
    if values['IDENTITY_SQL_SERVER'] != 'anderzilla-sql-44b76346-cus.database.windows.net':
        errors.append('unexpected_sql_server')
    if values['IDENTITY_SQL_DATABASE'] != 'anderzilla-identity-' + environment:
        errors.append('unexpected_sql_database')
    if values['IDENTITY_SQL_USER'] != 'anderzilla_identity_runtime':
        errors.append('dedicated_runtime_user_required')
    if len(values['IDENTITY_CPF_HMAC_KEY']) < 32:
        errors.append('cpf_secret_too_short')
    for key in ('CLERK_ISSUER', 'NEXT_PUBLIC_ACCOUNT_API_BASE'):
        if not origin(values[key]):
            errors.append('invalid_https_origin:' + key)
    origins = {v.strip().rstrip('/') for v in values['IDENTITY_ALLOWED_ORIGIN'].split(',')}
    if not origins or not all(origin(v) for v in origins):
        errors.append('invalid_allowed_origins')
    if environment == 'production' and 'https://anderzilla.com' not in origins:
        errors.append('production_origin_missing')
    prefix = 'live' if environment == 'production' else 'test'
    if not values['CLERK_SECRET_KEY'].startswith('sk_' + prefix + '_'):
        errors.append('wrong_clerk_secret_environment')
    if not values['NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY'].startswith('pk_' + prefix + '_'):
        errors.append('wrong_clerk_public_environment')
    try:
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
        key = load_pem_public_key(values['CLERK_JWT_KEY'].replace('\\n', '\n').encode())
        if not isinstance(key, RSAPublicKey) or key.key_size < 2048:
            errors.append('invalid_clerk_rsa_key')
    except Exception:
        errors.append('invalid_clerk_public_key_or_crypto_dependency')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--environment', choices=('homolog', 'production'), required=True)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--check-azure', action='store_true')
    args = parser.parse_args()
    path = args.settings.resolve()
    if path.is_relative_to(ROOT):
        print(json.dumps({'ready': False, 'errors': ['private_settings_must_be_outside_repository']}))
        return 1
    try:
        raw = json.loads(path.read_text(encoding='utf-8-sig'))
        values = raw.get('properties', raw) if isinstance(raw, dict) else raw
        errors = inspect(values, args.environment)
    except Exception:
        errors = ['private_settings_unreadable']
    if args.check_azure:
        try:
            result = subprocess.run(['az.cmd', 'account', 'show', '--subscription',
                '44b76346-26bd-4cd3-a529-627e47e99e5a', '--output', 'json', '--only-show-errors'],
                capture_output=True, text=True, check=True, timeout=30)
            account = json.loads(result.stdout)
            if (account.get('id'), account.get('tenantId'), account.get('user', {}).get('name')) != (
                '44b76346-26bd-4cd3-a529-627e47e99e5a',
                '3fdcb773-0842-4fb9-925e-bea17d681f83', 'anderzilla@ymail.com'):
                errors.append('wrong_azure_identity')
        except Exception:
            errors.append('azure_identity_not_verified')
    print(json.dumps({'ready': not errors, 'environment': args.environment,
                      'errors': errors, 'deployed': False}))
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
