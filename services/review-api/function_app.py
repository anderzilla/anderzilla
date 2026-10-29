import json
from urllib.parse import parse_qs
import azure.functions as func
from review_api import process, process_roles

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route='v1/{*path}', methods=['GET', 'POST'])
def review_api(req: func.HttpRequest) -> func.HttpResponse:
    # Served at /api/v1/... as the managed API of the review Static Web App; never deploy this as a standalone public Function.
    query = {key: values[-1] for key, values in parse_qs(req.url.partition('?')[2]).items()}
    headers = {name.lower(): value for name, value in req.headers.items()}
    status, payload, response_headers = process(req.method, req.route_params.get('path', ''), query, headers, req.get_body())
    return func.HttpResponse(json.dumps(payload, ensure_ascii=False), status_code=status, mimetype='application/json', headers=response_headers)


@app.route(route='GetRoles', methods=['POST'])
def get_roles(req: func.HttpRequest) -> func.HttpResponse:
    # Role source of the Static Web App (`auth.rolesSource` in staticwebapp.config.json), called by the platform after each sign-in.
    status, payload, response_headers = process_roles(req.get_body())
    return func.HttpResponse(json.dumps(payload), status_code=status, mimetype='application/json', headers=response_headers)
