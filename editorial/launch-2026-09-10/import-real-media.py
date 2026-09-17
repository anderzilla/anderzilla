"""Apply reviewed local photos exclusively through the CMS audited domain."""
import base64, importlib.util, json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'real-media-2026-09-16'
spec=importlib.util.spec_from_file_location('launch_operator',ROOT/'run-import.py')
operator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)

def main():
    review=json.loads((DEST/'reviewed-media.json').read_text(encoding='utf-8'))
    assert review['approvedForImport'] is True
    original={row['key']:row['id'] for row in json.loads((ROOT/'cms-import-report.json').read_text(encoding='utf-8'))}
    cms=operator.CMS(operator.configured_store())
    actor={'id':'operator:real-media-editorial','roles':['anderzilla_admin']}
    existing=cms.list(actor,'media')['items']
    by_title={row['data'].get('titlePT'):row for row in existing}
    content={row['id']:row for row in cms.list(actor,'content')['items']}
    report=[]
    for item in review['items']:
        key=item['key']
        if item['status']!='ready':
            report.append({'key':key,'status':'fallback','reason':item['reason']})
            continue
        media_ids=[]
        for image in item['images']:
            title=image['cmsTitle']
            row=by_title.get(title)
            if not row:
                raw=Path(image['localPath']).read_bytes()
                row=cms.upload_media(actor,{'filename':title,'contentBase64':base64.b64encode(raw).decode(),'altPT':image['altPT'],'altEN':image['altEN'],'credit':image['credit'],'license':image['licenseLabel']})
                by_title[title]=row
            metadata={'sourceUrl':image['sourcePage'],'altPT':image['altPT'],'altEN':image['altEN'],'credit':image['credit'],'license':image['licenseLabel']}
            if any(row['data'].get(field)!=value for field,value in metadata.items()):
                row=cms.save(actor,'media',{**row['data'],**metadata},row['id'],row['version'])
            if row['status']!='approved':
                row=cms.save(actor,'media',{},row['id'],row['version'],'approve')
            by_title[title]=row
            media_ids.append(row['id'])
        current=content[original[key]]
        assert current['status']=='approved',(key,'unexpected article state')
        payload={**current['data'],'coverMediaId':media_ids[0],'mediaIds':','.join(media_ids[1:]),'socialMediaId':media_ids[0]}
        if item.get('articleSourceUrl'):
            sources=json.loads(payload.get('sources','[]'))
            for source in sources:
                if source['url']==payload['sourceUrl']:
                    source['url']=item['articleSourceUrl']
            payload.update(sourceUrl=item['articleSourceUrl'],sources=json.dumps(sources,ensure_ascii=False))
        if payload!=current['data']:
            current=cms.save(actor,'content',payload,current['id'],current['version'])
            current=cms.save(actor,'content',{},current['id'],current['version'],'approve')
            content[current['id']]=current
        report.append({'key':key,'id':current['id'],'version':current['version'],'status':'approved','coverMediaId':media_ids[0],'galleryMediaIds':media_ids[1:]})
        (DEST/'cms-update-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report[-1]),flush=True)
    (DEST/'cms-update-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'reviewed':len(report),'updated':sum(row['status']=='approved' for row in report)}))

if __name__=='__main__':
    try:
        main()
    finally:
        os.environ.pop('CMS_SQL_PASSWORD',None)
