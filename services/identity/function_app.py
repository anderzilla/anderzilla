"""Standalone visitor API. No authority is accepted from SWA identity headers."""
import json
import azure.functions as func
from urllib.parse import urlsplit
from .api import dispatch
from .core import IdentityService
from .storage import AzureSQLStore
from .email_adapter import SmtpEmailSender

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="account/{*path}", methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"])
@app.route(route="points/{*path}", methods=["GET", "POST", "OPTIONS"])
def identity_api(req: func.HttpRequest) -> func.HttpResponse:
    base = {'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'}
    try:
        raw = req.get_body() or b''
        if len(raw) > 64000:
            return func.HttpResponse('{"error":{"code":"too_large","message":"Requisição muito grande."}}', status_code=413, mimetype='application/json', headers=base)
        # Use the actual URL, preserving account/points; route_params only has tail.
        parsed = urlsplit(req.url)
        path = parsed.path + ('?' + parsed.query if parsed.query else '')
        if raw and req.headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
            return func.HttpResponse('{"error":{"code":"unsupported_media_type"}}', status_code=415, mimetype='application/json', headers=base)
        try:
            body = json.loads(raw) if raw else None
        except (UnicodeDecodeError, ValueError):
            return func.HttpResponse('{"error":{"code":"invalid_json","message":"JSON inválido."}}', status_code=400, mimetype='application/json', headers=base)
        service = IdentityService(AzureSQLStore(), SmtpEmailSender())
        result = dispatch(service, req.method.upper(), path, dict(req.headers), body)
        return func.HttpResponse('' if result['status'] == 204 else json.dumps(result['body'], ensure_ascii=False),
                                 status_code=result['status'], mimetype='application/json', headers={**base, **result['headers']})
    except Exception:
        # Database/SMTP/JWT exceptions may carry PII or credentials; do not log them.
        return func.HttpResponse('{"error":{"code":"temporarily_unavailable","message":"Serviço temporariamente indisponível."}}',
                                 status_code=503, mimetype='application/json', headers=base)
