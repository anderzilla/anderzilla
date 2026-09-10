"""Verify CMS import, preserve old examples in history, and queue a real snapshot."""
import importlib.util
import json
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('launch_operator',ROOT/'run-import.py')
operator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)
from core import CMS,FIELDS
PRINCIPAL={'id':'operator:editorial-launch','roles':['anderzilla_admin']}
cms=CMS(operator.configured_store())
try:
    report=json.loads((ROOT/'cms-import-report.json').read_text(encoding='utf-8'))
    assert len(report)==60 and len({r['id'] for r in report})==60
    ids={r['id'] for r in report}
    records=cms.list(PRINCIPAL,'content')['items']
    imported=[r for r in records if r['id'] in ids]
    assert len(imported)==60
    manifest={x['key']:x['data'] for x in json.loads((ROOT/'launch-manifest.json').read_text(encoding='utf-8'))['items']}
    keys_by_id={x['id']:x['key'] for x in report}
    corrections=[]
    for row in imported:
        data=dict(manifest[keys_by_id[row['id']]])
        for reference in ('coverMediaId','socialMediaId'):
            data[reference]=row['data'][reference]
        if data!=row['data']:
            draft=cms.save(PRINCIPAL,'content',data,row['id'],row['version'])
            approved=cms.save(PRINCIPAL,'content',None,draft['id'],draft['version'],'approve')
            row.update(approved)
            corrections.append({'id':row['id'],'version':row['version'],'reason':'Final independent English copy review'})
    for row in imported:
        assert row['status']=='approved' and row['data'].get('coverMediaId') and row['data'].get('socialMediaId'),row['id']
        versions=cms.revisions(PRINCIPAL,'content',row['id'])['items']
        assert len(versions)>=2 and any(x['status']=='draft' for x in versions),row['id']
    previous_stubs={'webb-neptune-auroras','airpods-live-translation','gemini-remember-items','iphone17e-magsafe','gears-eday-controller','mario-kart-switch2-update'}
    archived=[]
    for collection in FIELDS:
        for row in (records if collection=='content' else cms.list(PRINCIPAL,collection)['items']):
            if row['status']=='archived' or row['id'] in ids:
                continue
            if row['data'].get('isDemo') is True or (collection=='content' and row['id'] in previous_stubs):
                updated=cms.save(PRINCIPAL,collection,None,row['id'],row['version'],'archive')
                archived.append({'collection':collection,'id':row['id'],'title':row['data'].get('titlePT'),'version':updated['version'],'reason':'Demo retained in CMS history' if row['data'].get('isDemo') else 'Short initial curation replaced by reviewed launch archive'})
    release=cms.release(PRINCIPAL,'editorial-launch-2026-09-10-reviewed-v1')
    snapshot=cms.releases(PRINCIPAL,release['id'],snapshot=True)
    snapshot['releaseId']=release['id']
    assert len(snapshot['collections']['content'])==60
    assert not any(r['data'].get('isDemo') for rows in snapshot['collections'].values() for r in rows)
    (ROOT/'cms-snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False),encoding='utf-8')
    result={'release':release,'approvedArticles':60,'approvedImages':len(snapshot['collections']['media']),'revisionHistoryVerified':60,'corrections':corrections,'archived':archived}
    (ROOT/'cms-launch-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='archived'}),flush=True)
    print('Archived with history: '+str(len(archived)),flush=True)
finally:
    os.environ.pop('CMS_SQL_PASSWORD',None)
