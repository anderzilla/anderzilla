"""Raw Svix-authenticated Clerk events, isolated from visitor authentication."""
import json
import re

from .api import response
from .clerk_auth import ClerkGateway, settings
from .clerk_service import ClerkAccountService
from .core import Rejected, reject


def dispatch_webhook(store, raw, headers, cfg=None, gateway=None, clock=None):
    from svix.webhooks import Webhook, WebhookVerificationError
    cfg = cfg or settings()
    headers = {k.lower(): v for k, v in headers.items()}
    try:
        if not cfg['ok'] or not cfg.get('webhookKey'):
            reject('temporarily_unavailable', 'Webhook não configurado.', 503)
        if len(raw) > 64000:
            reject('too_large', 'Evento muito grande.', 413)
        try:
            # Current Svix verifies the signature but intentionally returns None.
            # Parse only after authenticity and timestamp verification succeeds.
            Webhook(cfg['webhookKey']).verify(raw, headers)
            event = json.loads(raw)
        except (WebhookVerificationError, ValueError, TypeError):
            reject('invalid_webhook', 'Evento inválido.', 400)
        message_id = headers.get('svix-id', '')
        if not isinstance(event, dict) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', message_id):
            reject('invalid_webhook', 'Evento inválido.', 400)
        if event.get('type') not in {'user.deleted', 'user.updated'}:
            return response({'received': True, 'ignored': True})
        data = event.get('data')
        if not isinstance(data, dict) or not isinstance(data.get('id'), str) or not re.fullmatch(r'user_[A-Za-z0-9]+', data['id']):
            reject('invalid_webhook', 'Evento inválido.', 400)
        email = None
        if event['type'] == 'user.updated':
            # Re-fetch current provider state so out-of-order events cannot restore an old email.
            try:
                email = (gateway or ClerkGateway(cfg)).verified_email(data['id'])
            except Rejected as exc:
                if exc.status not in (401, 403):
                    raise
        return response(ClerkAccountService(store, cfg, clock).apply_webhook(message_id, event, email))
    except Rejected as exc:
        return response({'error': {'code': exc.code, 'message': str(exc)}}, exc.status)
