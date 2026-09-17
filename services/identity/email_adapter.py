"""Email delivery adapter: SMTP TLS. Never logs secrets or tokens. Returns unavailable if not configured."""
import os
import smtplib
import ssl
from urllib.parse import urlsplit
from email.message import EmailMessage

class EmailUnavailable(RuntimeError):
    pass

def _smtp_config():
    host = os.environ.get("IDENTITY_SMTP_HOST")
    if not host:
        return None
    return {
        "host": host,
        "port": int(os.environ.get("IDENTITY_SMTP_PORT", "587")),
        "user": os.environ.get("IDENTITY_SMTP_USER") or "",
        "password": os.environ.get("IDENTITY_SMTP_PASSWORD") or "",
        "from_addr": os.environ.get("IDENTITY_SMTP_FROM") or "",
        "use_tls": os.environ.get("IDENTITY_SMTP_TLS", "true").lower() != "false",
    }

class SmtpEmailSender:
    def __init__(self, capturer=None):
        # capturer is callable(to,subject,html) injected ONLY in tests with explicit injection
        self.capturer = capturer
        self.cfg = _smtp_config()

    def is_configured(self) -> bool:
        if self.capturer is not None:
            return True
        base = urlsplit(os.environ.get('IDENTITY_VERIFY_URL_BASE', ''))
        origin = os.environ.get('IDENTITY_ALLOWED_ORIGIN', '').rstrip('/')
        return bool(self.cfg and self.cfg['from_addr'] and self.cfg['use_tls'] and
                    base.scheme == 'https' and f'{base.scheme}://{base.netloc}' == origin and
                    not base.username and not base.password and not base.fragment)

    def send_verification(self, to_email: str, verify_url: str, lang: str = "pt-BR"):
        if self.capturer is not None:
            # test-only path with explicit injection
            self.capturer(to_email, verify_url, lang)
            return
        if not self.is_configured():
            raise EmailUnavailable("SMTP not configured")
        subject = "Confirme seu e-mail — AnderZilla" if lang == "pt-BR" else "Confirm your email — AnderZilla"
        body_text = (
            f"Olá! Confirme seu e-mail em: {verify_url}\nEste link expira em 24h e só pode ser usado uma vez.\n"
            if lang == "pt-BR"
            else f"Hello! Confirm your email at: {verify_url}\nThis link expires in 24h and is single-use.\n"
        )
        html = f'<p><a href="{verify_url}">Confirmar e-mail / Confirm email</a></p><p>Link expira em 24h / expires in 24h.</p>'
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.cfg["from_addr"]
        msg["To"] = to_email
        msg.set_content(body_text)
        msg.add_alternative(f"<html><body>{html}</body></html>", subtype="html")
        ctx = ssl.create_default_context()
        with smtplib.SMTP(self.cfg["host"], self.cfg["port"], timeout=15) as server:
            if self.cfg["use_tls"]:
                server.starttls(context=ctx)
            if self.cfg["user"]:
                server.login(self.cfg["user"], self.cfg["password"])
            server.send_message(msg)
