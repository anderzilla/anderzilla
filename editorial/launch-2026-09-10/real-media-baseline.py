import importlib.util, json, os
from pathlib import Path
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('operator_import',root/'run-import.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
    cms=module.CMS(module.configured_store())
    principal={'id':'operator:real-media-editorial','roles':['anderzilla_admin']}
    result={collection:cms.list(principal,collection)['items'] for collection in ['content','media']}
    dest=root/'real-media-2026-09-16'
    dest.mkdir(exist_ok=True)
    (dest/'cms-before.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'content':len(result['content']),'media':len(result['media']),'base64Bytes':sum(len(row['data'].get('assetBase64','')) for row in result['media'])}))
finally:
    os.environ.pop('CMS_SQL_PASSWORD',None)
