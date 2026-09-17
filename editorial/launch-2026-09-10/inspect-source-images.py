"""Read-only source inventory with DOM ancestry for editorial image selection."""
import concurrent.futures, html, json, subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'real-media-2026-09-16'

class Images(HTMLParser):
    def __init__(self,url):
        super().__init__(convert_charrefs=True)
        self.url=url; self.stack=[]; self.images=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        node=tag+('#'+attrs['id'] if attrs.get('id') else '')+('.'+attrs['class'].replace(' ','.') if attrs.get('class') else '')
        if tag=='img':
            src=attrs.get('data-src') or attrs.get('src') or ''
            if src and not src.startswith('data:'):
                self.images.append({'url':urljoin(self.url,src),'alt':attrs.get('alt',''),'path':' > '.join(self.stack[-8:]),'srcset':attrs.get('srcset','')})
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
            self.stack.append(node)
    def handle_endtag(self,tag):
        for index in range(len(self.stack)-1,-1,-1):
            if self.stack[index].split('#')[0].split('.')[0]==tag:
                del self.stack[index:]
                break

def fetch(item):
    key=item['key']; url=item['data']['sourceUrl']
    try:
        response=subprocess.run(['curl.exe','-sL','--max-time','25','--compressed','-A','Mozilla/5.0',url],capture_output=True,timeout=30)
        body=response.stdout.decode('utf-8',errors='replace')
        (DEST/'source-html'/(key+'.html')).write_text(body,encoding='utf-8')
        parser=Images(url); parser.feed(body)
        return {'key':key,'sourcePage':url,'images':parser.images}
    except Exception as error:
        return {'key':key,'sourcePage':url,'images':[],'error':str(error)}

if __name__=='__main__':
    items=json.loads((ROOT/'launch-manifest.json').read_text(encoding='utf-8'))['items']
    (DEST/'source-html').mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        result=list(pool.map(fetch,items))
    (DEST/'source-image-inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'pages':len(result),'images':sum(len(row['images']) for row in result)}))
