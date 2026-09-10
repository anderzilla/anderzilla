import importlib.util,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('launch_operator',ROOT/'run-import.py')
operator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)
from core import CMS
try:
    audit=json.loads((ROOT/'cms-launch-audit.json').read_text(encoding='utf-8'))
    cms=CMS(operator.configured_store())
    principal={'id':'operator:editorial-launch','roles':['anderzilla_admin']}
    previous=cms.releases(principal,audit['release']['id'])
    assert previous['status']=='failed'
    audit.setdefault('previousReleases',[]).append(previous)
    audit['release']=cms.release(principal,'editorial-launch-2026-09-10-reviewed-v2')
    (ROOT/'cms-launch-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(audit['release']),flush=True)
finally:
    os.environ.pop('CMS_SQL_PASSWORD',None)
