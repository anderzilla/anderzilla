"""Hostname verification remains strict with current TLS dependencies."""
import datetime as dt
import unittest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from OpenSSL.crypto import X509
from services.identity.tds_tls import validate_host


class HostnameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def certificate(self, names):
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'wanted.example.invalid')])
        now = dt.datetime.now(dt.timezone.utc)
        builder = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
                   .public_key(self.key.public_key()).serial_number(x509.random_serial_number())
                   .not_valid_before(now - dt.timedelta(minutes=1)).not_valid_after(now + dt.timedelta(days=1)))
        if names is not None:
            builder = builder.add_extension(x509.SubjectAlternativeName([x509.DNSName(v) for v in names]), critical=False)
        return X509.from_cryptography(builder.sign(self.key, hashes.SHA256()))

    def test_valid_dns_and_wrong_hostname(self):
        cert = self.certificate(['database.example.invalid'])
        self.assertTrue(validate_host(cert, b'database.example.invalid'))
        self.assertFalse(validate_host(cert, b'attacker.example.invalid'))

    def test_wildcard_matches_one_label_only(self):
        cert = self.certificate(['*.database.windows.net'])
        self.assertTrue(validate_host(cert, b'anderzilla.database.windows.net'))
        self.assertFalse(validate_host(cert, b'database.windows.net'))
        self.assertFalse(validate_host(cert, b'evil.anderzilla.database.windows.net'))

    def test_cn_cannot_override_missing_or_different_san(self):
        self.assertFalse(validate_host(self.certificate(None), b'wanted.example.invalid'))
        self.assertFalse(validate_host(self.certificate(['other.example.invalid']), b'wanted.example.invalid'))
