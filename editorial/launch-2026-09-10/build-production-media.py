import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path('Z:/AnderZilla');DATA=Path(__file__).resolve().parent/'real-media-2026-09-16'
sys.path.insert(0,str(ROOT/'services/publisher'))
from run_release import staging_directory,stage_app
qa=json.loads((DATA/'site-qa.json').read_text())
preview=Path(qa['artifact']);marker=json.loads((preview/'cms-release.json').read_text())
assert marker['containsDemo'] is False
public=json.loads((DATA/'public-after.json').read_text(encoding='utf-8'))
assert len(public['discoveries'])==60
target=ROOT/'.deploy'/('production-'+marker['releaseId']+'-launch')
assert not target.exists()
with staging_directory() as stage:
    web=stage/'web';stage_app(ROOT,web)
    (web/'src/components/hub/cms-published.json').write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding='utf-8')
    shutil.copytree(preview/'media',web/'public/media',dirs_exist_ok=True)
    shutil.copyfile(preview/'cms-release.json',web/'public/cms-release.json')
    env=dict(os.environ,NEXT_OUTPUT='export',NEXT_TELEMETRY_DISABLED='1',CMS_PREVIEW='0')
    subprocess.run([shutil.which('npm.cmd'),'run','build'],cwd=web,env=env,check=True,timeout=600)
    out=web/'out';count=0
    for item in public['discoveries']:
        for lang in ('pt','en'):
            page=(out/lang/'radar'/(item['slug'+lang.upper()]+'.html')).read_text(encoding='utf-8')
            assert 'name="robots" content="index, follow"' in page
            assert 'noindex' not in page and '\ufffd' not in page
            count+=1
    assert count==120
    assert 'HUB EM CONSTRUÇÃO' not in (out/'index.html').read_text(encoding='utf-8')
    assert 'Disallow: /' not in (out/'robots.txt').read_text()
    assert 'X-Robots-Tag' not in (out/'staticwebapp.config.json').read_text()
    for asset in (preview/'media').iterdir():
        assert hashlib.sha256(asset.read_bytes()).digest()==hashlib.sha256((out/'media'/asset.name).read_bytes()).digest()
    shutil.copytree(out,target)
result={'releaseId':marker['releaseId'],'snapshotSha256':marker['snapshotSha256'],'articlePages':count,'artifact':str(target),'indexable':True}
(DATA/'production-build.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result),flush=True)
