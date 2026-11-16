"""Local, editable motion timeline. Binds only to 127.0.0.1; no external upload."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
from pathlib import Path
import json,io,sys,subprocess,threading
import render
ROOT=Path(__file__).resolve().parent
job=None;lock=threading.Lock()
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def do_GET(self):
  parsed=urlparse(self.path)
  if parsed.path=='/api/frame':
   q=parse_qs(parsed.query)
   try:
    t=max(0,min(59.966666,float(q.get('t',['0'])[0])));hidden=q.get('hidden',[''])[0].split(',');caption=q.get('caption',['0'])[0]=='1'
    with lock:im=render.frame(t,caption,hidden)
    b=io.BytesIO();im.save(b,format='JPEG',quality=92);data=b.getvalue();self.send_response(200);self.send_header('Content-Type','image/jpeg');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
   except Exception as e:self.send_error(400,str(e))
  elif parsed.path=='/api/status':self.json_out({'rendering':job is not None and job.poll() is None,'exit_code':None if job is None else job.poll()})
  else:super().do_GET()
 def json_out(self,value):
  data=json.dumps(value).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
 def do_POST(self):
  global job
  if self.path=='/api/headlines':
   try:
    obj=json.loads(self.rfile.read(min(int(self.headers.get('Content-Length','0')),10000)))
    values=obj['headlines'];assert len(values)==10 and all(isinstance(v,str) and len(v)<=150 for v in values)
    with lock:
     for scene,value in zip(render.CFG['scenes'],values):scene['headline']=value
     (ROOT/'film.json').write_text(json.dumps(render.CFG,indent=2))
    self.json_out({'saved':True})
   except Exception as e:self.send_error(400,str(e))
  elif self.path=='/api/render':
   if job is not None and job.poll() is None:self.json_out({'rendering':True});return
   log=open(ROOT/'render.log','w');job=subprocess.Popen([sys.executable,str(ROOT/'render.py')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT);self.json_out({'rendering':True})
  else:self.send_error(404)
if __name__=='__main__':
 print('AtlasIQ editor: http://127.0.0.1:8768/project.html',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8768),Handler).serve_forever()
