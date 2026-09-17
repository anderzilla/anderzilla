"""Dynamic fail-closed configuration. Credentials are never returned."""
import os
from urllib.parse import urlsplit

POLICY_VERSION = '2026-09-17'
SQL_KEYS = ('IDENTITY_SQL_SERVER', 'IDENTITY_SQL_DATABASE', 'IDENTITY_SQL_USER', 'IDENTITY_SQL_PASSWORD')

def https_origin(value):
    try:
        p = urlsplit(value or '')
        return bool(p.scheme == 'https' and p.hostname and not p.username and not p.password and p.path in {'', '/'} and not p.query and not p.fragment)
    except ValueError:
        return False

def check_config():
    origin = os.environ.get('IDENTITY_ALLOWED_ORIGIN', '').rstrip('/')
    env = os.environ.get('IDENTITY_ENV', '')
    missing = [name for name in SQL_KEYS if not os.environ.get(name)]
    if env not in {'homolog', 'production'}:
        missing.append('IDENTITY_ENV')
    if not https_origin(origin):
        missing.append('IDENTITY_ALLOWED_ORIGIN')
    same_site = os.environ.get('IDENTITY_COOKIE_SAMESITE', 'Lax')
    if same_site not in {'Lax', 'None', 'Strict'}:
        missing.append('IDENTITY_COOKIE_SAMESITE')
    google_keys = ('IDENTITY_GOOGLE_CLIENT_ID', 'IDENTITY_GOOGLE_CLIENT_SECRET', 'IDENTITY_GOOGLE_REDIRECT_URI')
    google = all(os.environ.get(k) for k in google_keys)
    try:
        redirect = urlsplit(os.environ.get('IDENTITY_GOOGLE_REDIRECT_URI', ''))
        google = google and redirect.scheme == 'https' and f'{redirect.scheme}://{redirect.netloc}' == origin and not redirect.fragment and not redirect.username
    except ValueError:
        google = False
    return {'ok': not missing, 'missing': missing, 'origin': origin, 'sameSite': same_site, 'env': env,
            'google': bool(google), 'rewards': os.environ.get('IDENTITY_REWARDS_ENABLED') == 'true'}
