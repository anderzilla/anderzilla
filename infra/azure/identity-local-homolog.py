"""Loopback-only UI test server; forwards API requests to isolated homolog."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
from urllib.request import Request, urlopen
from urllib.error import HTTPError
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/'): self.proxy()
        else: super().do_GET()
    def do_POST(self): self.proxy()
    def do_PATCH(self): self.proxy()
    def do_OPTIONS(self): self.proxy()
    def proxy(self):
        if not self.path.startswith('/api/'):
            self.send_error(404); return
        headers={k:v for k,v in self.headers.items() if k.lower() in {'content-type','x-anderzilla-authorization','origin','access-control-request-method','access-control-request-headers'}}
        size=int(self.headers.get('Content-Length','0'))
        if size>64000: self.send_error(413); return
        request=Request('https://blue-coast-0c287a20f.2.azurestaticapps.net'+self.path,data=self.rfile.read(size) if size else None,headers=headers,method=self.command)
        try: response=urlopen(request,timeout=55)
        except HTTPError as exc: response=exc
        self.send_response(response.status)
        self.send_header('Content-Type',response.headers.get('Content-Type','application/json'))
        self.send_header('Cache-Control','no-store')
        self.end_headers(); self.wfile.write(response.read())
ThreadingHTTPServer(('127.0.0.1',4027),partial(Handler,directory='apps/web/out')).serve_forever()
