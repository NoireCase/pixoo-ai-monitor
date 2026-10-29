"""Validated worker-owned commands; all Bluetooth actions run on its main loop."""
import json, os, re, threading, queue, time
from pathlib import Path
from page_selection import PAGE_KEYS, validate_pages

def validate(c):
    if c.get('display_style') not in ('classic','b2','b3'): raise ValueError('显示样式无效')
    for key,lo,hi in [('brightness',0,100),('port',1,30),('rotation_seconds',1,3600),('refresh_seconds',15,86400)]:
        v=c.get(key)
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not lo<=v<=hi: raise ValueError(key+' 超出允许范围')
    if c.get('mac') and not re.fullmatch(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}',c['mac']): raise ValueError('设备地址格式应为 AA:BB:CC:DD:EE:FF')
    if not isinstance(c.get('enabled'),list) or any(p not in ('go','cx','ds') for p in c['enabled']): raise ValueError('服务配置无效')
    validate_pages(c['enabled'], c.get('enabled_pages',list(PAGE_KEYS)))
    if any(re.search('key|token|password',k,re.I) for k in c): raise ValueError('配置禁止保存密钥')
    return c

def save(root,c):
    validate(c); p=Path(root)/'config.json'; temp=p.with_suffix('.tmp'); temp.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8'); os.replace(temp,p)

class Commands:
    def __init__(self): self.q=queue.Queue(); self.wake=threading.Event()
    def request(self,cmd,args):
        item={'cmd':cmd,'args':args,'done':threading.Event(),'result':None,'deadline':time.monotonic()+4}
        self.q.put(item); self.wake.set()
        if not item['done'].wait(5): return {'ok':False,'error':'后台响应超时；请重新读取状态，勿重复执行硬件测试'}
        return item['result']
    def process(self,c,d,root,runtime):
        while not self.q.empty():
            item=self.q.get()
            try:
                if time.monotonic()>item['deadline']: raise ValueError('命令已超时，未执行')
                cmd=item['cmd']; args=item['args']
                if cmd=='apply':
                    updated={**c,**args}; validate(updated)
                    if updated['mac']!=c['mac'] or updated['port']!=c['port']: d.close(); d.mac=updated['mac']; d.port=int(updated['port'])
                    if d.sock is not None and updated['brightness']!=c['brightness']: d.brightness(updated['brightness'])
                    save(root,updated); c.update(updated)
                elif cmd=='reconnect': d.close()
                elif cmd=='hardware':
                    if d.sock is None: raise ValueError('请先连接 Pixoo')
                    from PIL import Image
                    for color in ('red','green','blue'): d.show(Image.new('RGB',(16,16),color)); time.sleep(.4)
                    # Restore the last successful frame before resuming rotation.
                    if getattr(runtime,'last_frame_png',None):
                        import base64,io
                        d.show(Image.open(io.BytesIO(base64.b64decode(runtime.last_frame_png))).convert('RGB'))
                else: raise ValueError('未知命令')
                item['result']={'ok':True}
            except Exception as e:
                item['result']={'ok':False,'error':str(e) if isinstance(e,ValueError) else type(e).__name__+'；请检查设备及文件权限'}
            finally: item['done'].set()
        self.wake.clear()
