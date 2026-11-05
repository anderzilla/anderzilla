"""CPF format checking and keyed comparison; does not prove document ownership."""
import hashlib
import hmac
import re
from .core import reject


def normalize_cpf(value):
    if not isinstance(value, str) or not re.fullmatch(r'(?:[0-9]{11}|[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2})', value):
        reject('invalid_cpf', 'Informe um CPF válido.')
    digits = re.sub(r'[^0-9]', '', value)
    if len(set(digits)) == 1:
        reject('invalid_cpf', 'Informe um CPF válido.')
    for size in (9, 10):
        digit = (sum(int(digits[i]) * (size + 1 - i) for i in range(size)) * 10 % 11) % 10
        if digit != int(digits[size]):
            reject('invalid_cpf', 'Informe um CPF válido.')
    return digits


def fingerprint(value, key, purpose='cpf'):
    if not isinstance(key, str) or len(key) < 32:
        reject('temporarily_unavailable', 'Serviço de cadastro indisponível.', 503)
    return hmac.new(key.encode(), (purpose + ':' + value).encode(), hashlib.sha256).hexdigest()
