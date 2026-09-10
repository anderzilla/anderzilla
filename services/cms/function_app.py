import json
import logging
import os
import azure.functions as func
from api import dispatch, swa_principal
from core import CMS, Error
from storage import AzureSQLStore

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route='{*path}', methods=['GET', 'POST', 'PUT'])
def cms_api(req: func.HttpRequest) -> func.HttpResponse:
    # Deploy ONLY as managed SWA API with role-restricted routes. SWA strips
    # client-supplied identity headers; this must never be a standalone public Function.
    headers = {'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'}
    try:
        if req.method in {'POST', 'PUT'} and req.headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
            raise Error(415, 'unsupported_media_type', 'Use application/json.')
        configured_origin = os.environ.get('CMS_ADMIN_ORIGIN')
        if req.headers.get('origin') and configured_origin and req.headers['origin'] != configured_origin:
            raise Error(403, 'invalid_origin', 'Origem não permitida.')
        raw = req.get_body()
        maximum = 2900000 if req.route_params.get('path', '') == 'admin/media-upload' else 300000
        if len(raw) > maximum:
            raise Error(413, 'too_large', 'Requisição muito grande.')
        from urllib.parse import urlsplit
        query = urlsplit(req.url).query
        route = '/api/' + req.route_params.get('path', '') + ('?' + query if query else '')
        is_worker = route.startswith('/api/worker/')
        if is_worker:
            # Worker auth: Bearer only, no query/cookie token, no x-ms-client-principal trust
            from worker_auth import authenticate_worker

            header_dict = {k: v for k, v in req.headers.items()}
            principal = authenticate_worker(header_dict, url=req.url)
            result = dispatch(CMS(AzureSQLStore()), principal, req.method, route, json.loads(raw) if raw else {}, os.environ.get('CMS_ENVIRONMENT', 'homolog'))
        else:
            principal = swa_principal(req.headers.get('x-ms-client-principal'))
            result = dispatch(CMS(AzureSQLStore()), principal, req.method, route, json.loads(raw) if raw else {}, os.environ.get('CMS_ENVIRONMENT', 'homolog'))
        return func.HttpResponse(json.dumps(result, ensure_ascii=False), mimetype='application/json', headers=headers)
    except Error as error:
        return func.HttpResponse(json.dumps({'error': {'code': error.code, 'message': str(error)}}), status_code=error.status, mimetype='application/json', headers=headers)
    except (ValueError, UnicodeDecodeError):
        return func.HttpResponse('{"error":{"code":"invalid_json","message":"JSON inválido."}}', status_code=400, mimetype='application/json', headers=headers)
    except Exception:
        logging.error('CMS operation unavailable; inspect infrastructure health without logging request data.')
        return func.HttpResponse('{"error":{"code":"unavailable","message":"Serviço temporariamente indisponível."}}', status_code=503, mimetype='application/json', headers=headers)
