"""Keep python-tds hostname checks compatible with current pyOpenSSL.

python-tds 1.17.1 reads X509.get_extension(), removed in pyOpenSSL 26.
The TLS chain remains verified by python-tds/OpenSSL; this replaces only its
hostname matcher with service-identity over cryptography SANs.
Never accept the subject CN when SANs are absent or disagree.
"""


def validate_host(cert, name):
    from cryptography import x509
    from service_identity.cryptography import verify_certificate_hostname
    from service_identity.exceptions import CertificateError, VerificationError
    try:
        certificate = cert.to_cryptography()
        san = certificate.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        names = san.get_values_for_type(x509.DNSName)
        if not names:
            return False
        verify_certificate_hostname(certificate, name.decode('ascii'))
        return True
    except (x509.ExtensionNotFound, CertificateError, VerificationError, ValueError, UnicodeError):
        return False


def configure():
    import pytds.tls
    pytds.tls.validate_host = validate_host
