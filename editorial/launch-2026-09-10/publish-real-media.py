"""Publish reviewed real imagery to the existing visual preview with CMS history."""
import html, importlib.util, json, os, re, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'real-media-2026-09-16'
spec=importlib.util.spec_from_file_location('launch_operator',ROOT/'run-import.py')
operator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)
sys.path.insert(0,'Z:/AnderZilla/services/publisher')
from run_release import run, build
from import_snapshot import transform

def checked_build(root,directory,snapshot,marker):
    artifact=build(root,directory,snapshot,marker)
    public=transform(snapshot)
    (DEST/'public-after.json').write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding='utf-8')
    media={row['id']:row for row in public['media']}
    report=json.loads((DEST/'cms-update-report.json').read_text(encoding='utf-8'))
    expected={row['id']:row for row in report if row['status']=='approved'}
    reviewed={row['key']:row for row in json.loads((DEST/'reviewed-media.json').read_text(encoding='utf-8'))['items'] if row['status']=='ready'}
    assert len(report)==60 and len(expected)==len(reviewed)
    for row in expected.values():
        references=[row['coverMediaId']]+row['galleryMediaIds']
        originals=reviewed[row['key']]['images']
        assert len(references)==len(originals)
        for reference,original in zip(references,originals):
            actual=media[reference]
            for field in ('altPT','altEN','credit'):
                assert actual[field]==original[field],(row['key'],field)
            assert actual['sourceUrl']==original['sourcePage']
    count=0
    for item in public['discoveries']:
        cover=media[item['coverMediaId']]
        if item['id'] in expected:
            assert item['coverMediaId']==expected[item['id']]['coverMediaId']
            assert cover.get('sourceUrl'),(item['id'],'missing provenance')
            assert [value for value in item.get('mediaIds','').split(',') if value]==expected[item['id']]['galleryMediaIds']
        for lang in ('pt','en'):
            route=f"/{lang}/radar/{item['slug'+lang.upper()]}/"
            page=(artifact/(route.strip('/')+'.html')).read_text(encoding='utf-8')
            heading=re.search(r'<h1[^>]*>(.*?)</h1>',page,re.S)
            assert heading and html.unescape(re.sub('<[^>]+>','',heading[1]))==item['title'+lang.upper()]
            assert 'noindex' in page
            assert html.escape(cover['url'],quote=True) in page
            assert 'class="article-cover-link"' in page
            assert html.escape('https://anderzilla.com'+cover['previewUrl'],quote=True) in page
            if cover.get('sourceUrl'):
                assert html.escape(cover['sourceUrl'],quote=True) in page
            for image_id in item.get('mediaIds','').split(','):
                if image_id:
                    assert html.escape(media[image_id]['url'],quote=True) in page
            assert (artifact/cover['previewUrl'].lstrip('/')).is_file()
            assert '\ufffd' not in page
            count+=1
    assert count==120
    retained=Path('Z:/AnderZilla/.deploy')/('real-media-'+marker['releaseId'])
    if not retained.exists():
        shutil.copytree(artifact,retained)
    (DEST/'site-qa.json').write_text(json.dumps({'articlePages':count,'sourceImageArticles':len(expected),'releaseId':marker['releaseId'],'artifact':str(retained)},indent=2),encoding='utf-8')
    return artifact

if __name__=='__main__':
    try:
        os.environ['AZURE_CONFIG_DIR']='C:/Users/ander/.codex/anderzilla-azure'
        cms=operator.CMS(operator.configured_store())
        actor={'id':'operator:real-media-editorial','roles':['anderzilla_admin']}
        release=cms.release(actor,'real-media-editorial-2026-09-16-v1')
        (DEST/'queued-release.json').write_text(json.dumps(release,indent=2),encoding='utf-8')
        result=run(cms,release['id'],azure_cli='C:/Users/ander/.codex/tools/azure-cli/portable/bin/az.cmd',builder=checked_build)
        (DEST/'published-release.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result),flush=True)
    finally:
        os.environ.pop('CMS_SQL_PASSWORD',None)
