"""Publish the reviewed CMS snapshot using the existing isolated visual release flow."""
import html
import importlib.util
import json
import os
import re
import shutil
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('launch_operator',ROOT/'run-import.py')
operator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)
sys.path.insert(0,'Z:/AnderZilla/services/publisher')
from core import CMS
from run_release import run,build
from import_snapshot import transform

def checked_build(root,directory,snapshot,marker):
    artifact=build(root,directory,snapshot,marker)
    public=transform(snapshot)
    count=0
    for item in public['discoveries']:
        for lang in ('pt','en'):
            suffix=lang.upper()
            route=f"/{lang}/radar/{item['slug'+suffix]}/"
            page=(artifact/(route.strip('/')+'.html')).read_text(encoding='utf-8')
            heading=re.search(r'<h1[^>]*>(.*?)</h1>',page,re.S)
            assert heading and html.unescape(re.sub('<[^>]+>','',heading[1]))==item['title'+suffix],(route,'title')
            canonical=re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"',page)
            assert canonical and html.unescape(canonical[1])=='https://anderzilla.com'+route,(route,'canonical')
            assert 'noindex' in page,(route,'preview robots')
            image=re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',page)
            assert image and image[1].endswith('-social.jpg'),(route,'share image')
            assert (artifact/image[1].split('https://anderzilla.com/')[-1]).is_file(),(route,'missing image')
            structured=re.search(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',page,re.S)
            assert structured and json.loads(structured[1])['headline']==item['title'+suffix],(route,'structured data')
            assert '\ufffd' not in page,(route,'replacement character')
            count+=1
    assert count==120 and len(public['media'])>=120
    retained=Path('Z:/AnderZilla/.deploy')/('editorial-launch-'+marker['releaseId'])
    if not retained.exists():
        shutil.copytree(artifact,retained)
    (ROOT/'site-qa.json').write_text(json.dumps({'articlePages':count,'checks':['titles','canonical','noindex preview','JPEG share asset','JSON-LD','UTF-8'],'artifact':str(retained),'releaseId':marker['releaseId']},indent=2),encoding='utf-8')
    return artifact

try:
    os.environ['AZURE_CONFIG_DIR']='C:/Users/ander/.codex/anderzilla-azure'
    release=json.loads((ROOT/'cms-launch-audit.json').read_text(encoding='utf-8'))['release']
    result=run(CMS(operator.configured_store()),release['id'],azure_cli='C:/Users/ander/.codex/tools/azure-cli/portable/bin/az.cmd',builder=checked_build)
    (ROOT/'published-release.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
finally:
    os.environ.pop('CMS_SQL_PASSWORD',None)
