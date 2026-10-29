import json
from urllib.parse import parse_qs
import azure.functions as func
from content_api import process

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route='v1/{*path}', methods=['GET', 'POST'])
def content_api(req: func.HttpRequest) -> func.HttpResponse:
    query = {key: values[-1] for key, values in parse_qs(req.url.partition('?')[2]).items()}
    headers = {name.lower(): value for name, value in req.headers.items()}
    status, payload, response_headers = process(req.method, req.route_params.get('path', ''), query, headers, req.get_body())
    return func.HttpResponse(json.dumps(payload, ensure_ascii=False), status_code=status, mimetype='application/json', headers=response_headers)
