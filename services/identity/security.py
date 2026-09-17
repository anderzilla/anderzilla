"""Security primitives; passwords and tokens are never logged."""
import base64
import hashlib
import hmac
import secrets
import time
from http.cookies import SimpleCookie

def random_token():
    return secrets.token_urlsafe(32)

def token_hash(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def equal(a, b):
    return isinstance(a, str) and isinstance(b, str) and hmac.compare_digest(a, b)

def hash_password(value):
    from argon2 import PasswordHasher
    return PasswordHasher().hash(value)

def verify_password(encoded, value):
    from argon2 import PasswordHasher
    from argon2.exceptions import VerificationError, InvalidHashError
    if not isinstance(value, str) or len(value) > 128 or not encoded:
        return False
    try:
        return PasswordHasher().verify(encoded, value)
    except (VerificationError, InvalidHashError):
        return False

def cookies(header):
    parsed = SimpleCookie()
    try:
        parsed.load(header or '')
        return {name: item.value for name, item in parsed.items()}
    except Exception:
        return {}

def cookie(name, value, max_age, same_site='Lax'):
    if same_site not in {'Lax', 'None', 'Strict'}:
        raise ValueError('Invalid cookie policy')
    return f'{name}={value}; Path=/; HttpOnly; Secure; SameSite={same_site}; Max-Age={max_age}'

def pkce_challenge(verifier):
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')

def verify_google_id_token(encoded, audience, nonce):
    from google.oauth2.id_token import verify_oauth2_token
    from google.auth.transport.requests import Request
    if not audience or not nonce or not isinstance(encoded, str):
        raise ValueError('Invalid OIDC input')
    claims = verify_oauth2_token(encoded, Request(), audience=audience)
    if claims.get('iss') not in {'https://accounts.google.com', 'accounts.google.com'}:
        raise ValueError('Invalid issuer')
    if claims.get('aud') != audience or not equal(claims.get('nonce'), nonce):
        raise ValueError('Invalid audience or nonce')
    if claims.get('email_verified') is not True or not isinstance(claims.get('sub'), str) or not claims['sub']:
        raise ValueError('Unverified identity')
    if int(claims.get('exp', 0)) <= int(time.time()):
        raise ValueError('Expired identity')
    return claims
