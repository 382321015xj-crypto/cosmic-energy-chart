from __future__ import annotations
import json, os, sys, traceback, hmac, hashlib, base64, urllib.request, urllib.error, threading, time, re
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / 'web' / 'index.html'
ASSETS = ROOT / 'web' / 'assets'
sys.path.insert(0, str(ROOT))
from app.product import calculate_product, InputError
from app.location import search_locations, LocationError

IMAGE_CACHE = {}  # Ephemeral memory cache; cleared when Render instance restarts.
IMAGE_LOCKS = {}
CACHE_MUTEX = threading.Lock()
MAX_CACHE = 30
ELEMENTS = {'金','木','水','火','土'}

def generate_jewelry(payload):
    access_code=os.environ.get('COSMIC_AI_ACCESS_CODE','').strip()
    if not access_code: raise RuntimeError('尚未配置 COSMIC_AI_ACCESS_CODE，AI 生图暂不可用')
    if not hmac.compare_digest(str(payload.get('access_code','')),access_code): raise PermissionError('AI 生图访问码错误')
    key = os.environ.get('OPENAI_API_KEY','').strip()
    if not key: raise RuntimeError('尚未配置 OPENAI_API_KEY')
    if os.environ.get('COSMIC_AI_IMAGES_ENABLED','true').lower() != 'true': raise RuntimeError('AI 图片功能已关闭')
    kind=payload.get('kind')
    if kind not in ('natal','annual'): raise ValueError('手串类型无效')
    spec=payload.get('spec') or {}
    names=('cord','primary','secondary')
    elems={k:str((spec.get(k) or {}).get('element','')) for k in names}
    if any(x not in ELEMENTS for x in elems.values()): raise ValueError('五行搭配数据不完整')
    mats={k:str((spec.get(k) or {}).get('material',''))[:60] for k in names}
    forbidden=spec.get('avoid') or []
    if not isinstance(forbidden,list): forbidden=[]
    forbidden=[str(x)[:20] for x in forbidden[:5] if str(x) in ELEMENTS]
    design={'kind':kind,'elements':elems,'materials':mats,'avoid':forbidden}
    fingerprint=hashlib.sha256(json.dumps(design,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    with CACHE_MUTEX:
        if fingerprint not in IMAGE_LOCKS: IMAGE_LOCKS[fingerprint]=threading.Lock()
        lock=IMAGE_LOCKS[fingerprint]
    with lock:
        if fingerprint in IMAGE_CACHE: return fingerprint, IMAGE_CACHE[fingerprint], True
        color={'金':'silver-white or champagne metallic','木':'jade green','水':'deep blue-black','火':'warm red','土':'earthy amber-brown'}
        prompt=(f'Create a photorealistic luxury ecommerce jewelry product photograph of ONE wearable Chinese braided-cord gemstone bracelet, {"natal" if kind=="natal" else "annual"} edition. '
                f'Exact design specifications: bracelet CORD has element {elems["cord"]}, color {color[elems["cord"]]}, material {mats["cord"] or "braided silk cord"}. '
                f'The MAIN focal gemstone beads have element {elems["primary"]}, color {color[elems["primary"]]}, material {mats["primary"] or "natural polished gemstone"}. '
                f'SECONDARY accent beads have element {elems["secondary"]}, color {color[elems["secondary"]]}, material {mats["secondary"] or "natural polished gemstone"}. '
                f'Never use colors associated with forbidden elements: {", ".join(color[x] for x in forbidden) if forbidden else "none"}. '
                'Visible braided cord and realistic bead holes, physically plausible bracelet assembly, natural gem inclusions and subtle translucency, high-end professional studio macro photography, centered bracelet on ivory neutral backdrop, soft natural shadows, no hands, no person, no text, no watermark, no diagrams, no illustration, no extra jewelry. Keep cord, main beads, and accent beads visually distinct. Square composition.')
        req_data={'model':os.environ.get('OPENAI_IMAGE_MODEL','gpt-image-1.5'),'prompt':prompt,'size':'1024x1024','quality':'medium','n':1,'output_format':'jpeg'}
        req=urllib.request.Request('https://api.openai.com/v1/images/generations',data=json.dumps(req_data).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=175) as response: result=json.loads(response.read())
        except urllib.error.HTTPError as exc:
            body=exc.read().decode('utf-8','replace')
            print('[AI IMAGE API ERROR]',exc.code,body[:800])
            raise RuntimeError('OpenAI 图片生成请求失败（HTTP '+str(exc.code)+'），请检查 API 额度、模型权限或 Render Logs')
        images=result.get('data') or []
        if not images or not images[0].get('b64_json'): raise RuntimeError('图片生成服务没有返回图片数据')
        raw=base64.b64decode(images[0]['b64_json'],validate=True)
        if len(raw)>12_000_000: raise RuntimeError('生成图片过大')
        with CACHE_MUTEX:
            if len(IMAGE_CACHE)>=MAX_CACHE: IMAGE_CACHE.pop(next(iter(IMAGE_CACHE)))
            IMAGE_CACHE[fingerprint]=raw
        return fingerprint,raw,False

class Handler(BaseHTTPRequestHandler):
    server_version = 'BaZiCosmic/5.8'
    def log_message(self, fmt, *args):
        print('[HTTP] ' + fmt % args)
    def send_json(self, status, obj):
        data=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode('utf-8')
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        p=urlparse(self.path)
        if p.path.startswith('/api/v1/bracelet/image/'):
            image_id=p.path.rsplit('/',1)[-1]
            data=IMAGE_CACHE.get(image_id) if re.fullmatch(r'[a-f0-9]{64}',image_id) else None
            if not data: self.send_json(404,{'detail':'图片已过期，请重新生成'}); return
            self.send_response(200); self.send_header('Content-Type','image/jpeg'); self.send_header('Cache-Control','private, max-age=3600'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
        if p.path.startswith('/assets/'):
            f=(ASSETS / unquote(p.path[len('/assets/'):])).resolve()
            if ASSETS.resolve() in f.parents and f.is_file():
                data=f.read_bytes(); ctype='image/jpeg' if f.suffix.lower() in ('.jpg','.jpeg') else 'application/octet-stream'
                self.send_response(200); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
        if p.path=='/':
            data=WEB.read_bytes(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
        if p.path=='/health':
            self.send_json(200,{'ok':True,'version':'5.8-COSMIC-WEB','address_scope':'global','runtime':'python-stdlib'}); return
        if p.path=='/api/v1/location/search':
            qs=parse_qs(p.query); q=(qs.get('q') or [''])[0]
            try: limit=int((qs.get('limit') or ['5'])[0])
            except Exception: limit=5
            try: self.send_json(200,{'results':search_locations(q,limit)})
            except LocationError as e: self.send_json(422,{'detail':str(e)})
            return
        self.send_json(404,{'detail':'Not Found'})
    def do_POST(self):
        path=urlparse(self.path).path
        if path=='/api/v1/bracelet/generate':
            try:
                n=int(self.headers.get('Content-Length','0'))
                if n<1 or n>8000: self.send_json(413,{'detail':'请求过大'}); return
                payload=json.loads(self.rfile.read(n))
                ident,raw,cached=generate_jewelry(payload)
                self.send_json(200,{'image_url':'/api/v1/bracelet/image/'+ident,'cached':cached,'format':'jpeg','ai_generated':True})
            except PermissionError as e: self.send_json(403,{'detail':str(e)})
            except ValueError as e: self.send_json(422,{'detail':str(e)})
            except Exception as e:
                traceback.print_exc(); self.send_json(503,{'detail':str(e)})
            return
        if path!='/api/v1/bazi/calculate': self.send_json(404,{'detail':'Not Found'}); return
        try:
            n=int(self.headers.get('Content-Length','0')); payload=json.loads(self.rfile.read(n).decode('utf-8') or '{}')
            self.send_json(200,calculate_product(payload))
        except InputError as e: self.send_json(422,{'detail':str(e)})
        except Exception as e:
            traceback.print_exc(); self.send_json(500,{'detail':'系统计算异常：'+str(e)})

def main():
    host=os.environ.get('HOST','0.0.0.0'); port=int(os.environ.get('PORT', os.environ.get('BAZI_PORT','8000')))
    print('东方能量命盘 COSMIC 5.8 WEB')
    print('服务监听：%s:%s' % (host,port))
    print('运行核心：Python 标准库（启动不需要 pip 安装）')
    ThreadingHTTPServer((host,port),Handler).serve_forever()
if __name__=='__main__': main()
