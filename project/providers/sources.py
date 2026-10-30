import json, os, shutil, subprocess, threading, queue
from pathlib import Path
from decimal import Decimal
from urllib.request import Request, urlopen
from providers.base import Reading
URLS={'go':'https://opencode.ai/zen/go/v1/usage','ds':'https://api.deepseek.com/user/balance'}
def secret(name):
    value=os.environ.get('PIXOO_'+name.upper()+'_KEY')
    if value: return value
    try:
        import keyring
        return keyring.get_password('Pixoo AI Monitor',name)
    except Exception: return None
def request(url,key):
    with urlopen(Request(url,headers={'Authorization':'Bearer '+key,'Accept':'application/json','User-Agent':'Pixoo-AI-Monitor/1'}),timeout=10) as r: return json.load(r,parse_float=Decimal)
def opencode(data):
    result=[]
    for key,label in [('rolling','5H'),('weekly','7D'),('monthly','30D')]:
        item=data.get('usage',{}).get(key)
        if not isinstance(item,dict) or item.get('status')!='ok' or item.get('percent') is None: continue
        result.append(Reading('go','OpenCode Go',source=URLS['go'],remaining_percent=max(0,min(100,100-float(item['percent']))),unit='%',reset_at=item.get('resetsAt'),window=label))
    if not result: raise ValueError('Unsupported OpenCode usage response')
    return result
def deepseek(data):
    balances=data.get('balance_infos',[])
    item=next((b for b in balances if b.get('currency')=='CNY'),None) or next((b for b in balances if b.get('currency')=='USD'),None)
    if not item: raise ValueError('No supported currency')
    value=Decimal(item['total_balance'])
    if not value.is_finite(): raise ValueError('Invalid balance')
    return [Reading('ds','DeepSeek API',source=URLS['ds'],remaining_value=value,unit=item['currency'],details={'is_available':data.get('is_available'),'granted_balance':str(Decimal(item['granted_balance'])),'topped_up_balance':str(Decimal(item['topped_up_balance']))})]
def codex_parse(result):
    # Prefer the default Codex bucket; do not add model-specific buckets to it.
    buckets=result.get('rateLimitsByLimitId') or {}
    snap=result.get('rateLimits') or buckets.get('codex') or {}; out=[]
    for name in ('primary','secondary'):
        w=snap.get(name)
        if not isinstance(w,dict) or w.get('usedPercent') is None: continue
        minutes=w.get('windowDurationMins')
        label={300:'5H',10080:'7D'}.get(minutes)
        if not label and isinstance(minutes,int) and minutes>0: label=f'{minutes}M'
        if label: out.append(Reading('cx','Codex',source='codex app-server',remaining_percent=max(0,min(100,100-float(w['usedPercent']))),unit='%',reset_at=w.get('resetsAt'),window=label,details={'credits':snap.get('credits'),'window_duration_minutes':minutes}))
    if not out: raise ValueError('No supported Codex windows')
    return out
def find_codex():
    exe=shutil.which('codex')
    if exe: return exe
    if os.name != 'nt' or not os.environ.get('LOCALAPPDATA'): return None
    root=Path(os.environ['LOCALAPPDATA'])/'OpenAI'/'Codex'/'bin'
    try:
        candidates=[p for p in root.glob('*/codex.exe') if p.is_file()]
        return str(max(candidates,key=lambda p:p.stat().st_mtime)) if candidates else None
    except OSError:
        return None
def codex():
    exe=find_codex()
    if not exe: return [Reading('cx','Codex',status='NOT_CONFIGURED',error_message='Codex CLI not found')]
    p=subprocess.Popen([exe,'app-server'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)); q=queue.Queue(); stderr_flags=set()
    def reader():
        try:
            for line in p.stdout: q.put(line)
        finally: q.put(None)
    def drain_stderr():
        for line in p.stderr:
            # Do not retain raw stderr, which may contain sensitive paths or data.
            if 'Could not find home directory' in line: stderr_flags.add('home unavailable')
    t=threading.Thread(target=reader,daemon=True); t.start()
    err_thread=threading.Thread(target=drain_stderr,daemon=True); err_thread.start()
    def rpc(i,method,params):
        import time
        p.stdin.write(json.dumps({'id':i,'method':method,'params':params})+'\n'); p.stdin.flush(); deadline=time.monotonic()+15
        while True:
            remaining=deadline-time.monotonic()
            if remaining<=0: raise TimeoutError(f'Codex {method} timeout')
            try: line=q.get(timeout=remaining)
            except queue.Empty: raise TimeoutError(f'Codex {method} timeout') from None
            if line is None:
                p.wait(timeout=2); err_thread.join(timeout=1)
                raise RuntimeError(f'Codex exited during {method}: exit={p.returncode}; ' + (', '.join(sorted(stderr_flags)) or 'see CLI diagnostics'))
            try: obj=json.loads(line)
            except json.JSONDecodeError: continue
            if obj.get('id')==i:
                if 'error' in obj: raise ValueError('Codex RPC error')
                return obj.get('result',{})
    try:
        rpc(1,'initialize',{'clientInfo':{'name':'pixoo_ai_monitor','version':'1.0.0'}})
        p.stdin.write(json.dumps({'method':'initialized'})+'\n'); p.stdin.flush()
        account=rpc(2,'account/read',{'refreshToken':False}).get('account')
        if not account or account.get('type')!='chatgpt': return [Reading('cx','Codex',status='NOT_CONFIGURED',error_message='ChatGPT Codex login required')]
        return codex_parse(rpc(3,'account/rateLimits/read',{}))
    finally:
        if p.poll() is None: p.kill()
        p.wait(timeout=5); t.join(timeout=2); err_thread.join(timeout=2)
        for stream in (p.stdin,p.stdout,p.stderr): stream.close()
def fetch(pid):
    if pid=='cx': return codex()
    key=secret(pid); name={'go':'OpenCode Go','ds':'DeepSeek API'}[pid]
    if not key: return [Reading(pid,name,status='NOT_CONFIGURED',error_message='API key not configured')]
    return (opencode if pid=='go' else deepseek)(request(URLS[pid],key))
def mock():
    return [Reading('go','OpenCode Go',source='MOCK',remaining_percent=72,window='5H'),Reading('go','OpenCode Go',source='MOCK',remaining_percent=48,window='7D'),Reading('cx','Codex',source='MOCK',remaining_percent=19,window='5H'),Reading('ds','DeepSeek API',source='MOCK',remaining_value=Decimal('35.6'),unit='CNY')]

