"""Local authorized operator; all mutations go through CMS domain and its audit."""
import json
import os
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,'Z:/AnderZilla/services/cms')
from core import CMS
from storage import AzureSQLStore
from import_newsroom import import_manifest
import certifi
import pytds

class OperatorStore(AzureSQLStore):
    def connect(self):
        # Reuse a TLS connection in this one operator process. pytds resets pooled
        # sessions with sp_reset_connection; CMS still commits/rolls back each unit.
        return pytds.connect(server=os.environ['CMS_SQL_SERVER'],database=os.environ['CMS_SQL_DATABASE'],user=os.environ['CMS_SQL_USER'],password=os.environ['CMS_SQL_PASSWORD'],cafile=certifi.where(),validate_host=True,enc_login_only=False,autocommit=False,login_timeout=40,timeout=45,disable_connect_retry=True,pooling=True)

def configured_store():
    secrets=json.loads(Path('C:/Users/ander/.codex/anderzilla-azure/cms-secrets.json').read_text(encoding='utf-8-sig'))
    os.environ.update(CMS_SQL_SERVER=secrets['server']+'.database.windows.net',CMS_SQL_DATABASE=secrets['database'],CMS_SQL_USER='anderzilla_cms_runtime',CMS_SQL_PASSWORD=secrets['runtimePassword'])
    return OperatorStore()

if __name__=='__main__':
    started=time.monotonic()
    def progress(event):
        print(json.dumps(dict(event,elapsedSeconds=round(time.monotonic()-started,1))),flush=True)
    try:
        result=import_manifest(CMS(configured_store()),json.loads((ROOT/'launch-manifest.json').read_text(encoding='utf-8')),True,progress)
        (ROOT/'cms-import-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    except Exception as error:
        print('CMS import stopped: '+type(error).__name__,file=sys.stderr)
        sys.exit(1)
    finally:
        os.environ.pop('CMS_SQL_PASSWORD',None)
