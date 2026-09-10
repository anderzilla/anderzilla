import importlib.util,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('launch_operator',ROOT/'run-import.py')
operator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)
from core import CMS
try:
    release=json.loads((ROOT/'published-release.json').read_text(encoding='utf-8'))
    assert release['status']=='deployed'
    snapshot=CMS(operator.configured_store()).releases({'id':'operator:editorial-launch','roles':['anderzilla_admin']},release['id'],snapshot=True)
    snapshot['releaseId']=release['id']
    assert len(snapshot['collections']['content'])==60
    (ROOT/'cms-snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False),encoding='utf-8')
    audit=json.loads((ROOT/'cms-launch-audit.json').read_text(encoding='utf-8'))
    audit['release']=release
    (ROOT/'cms-launch-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    quality=json.loads((ROOT/'quality-summary.json').read_text(encoding='utf-8-sig'))
    quality.update(status='approved_in_cms_deployed_visual_preview',releaseId=release['id'],previewUrl=release['url'],productionPromoted=False)
    (ROOT/'quality-summary.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':quality['status'],'releaseId':release['id']}),flush=True)
finally:
    os.environ.pop('CMS_SQL_PASSWORD',None)
