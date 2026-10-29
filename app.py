import argparse, json, logging, logging.handlers, os, socket, sys, threading, time, ctypes
from pathlib import Path
from dataclasses import replace
from PIL import Image, ImageTk
from providers.base import Reading
from providers.sources import fetch, mock
from display.renderer import render, render_configured
from drivers.pixoo import Pixoo
from runtime_health import RuntimeStatus
ROOT=Path(__file__).resolve().parent
os.chdir(ROOT)
DEFAULT={'mac':'','port':1,'brightness':50,'rotation_seconds':5,'refresh_seconds':120,'enabled':['go','cx','ds'],'windows':['5H','7D','30D'],'low':20,'warning':50,'display_style':'classic','deepseek_reference_peak_cny':100}
def config():
    p=ROOT/'config.json'
    return {**DEFAULT,**(json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else {})}
def lock():
    if os.name!='nt': return True
    global mutex
    mutex=ctypes.windll.kernel32.CreateMutexW(None,False,'Local\\PixooAIMonitorSingleton')
    return bool(mutex) and ctypes.windll.kernel32.GetLastError()!=183
class Monitor:
    def __init__(self,c,mocked=False):
        self.c=c; self.mocked=mocked; self.data={}; self.guard=threading.Lock(); self.stop=threading.Event()
        self.provider_health={p:{'status':'PENDING','last_success_at':None,'last_attempt_at':None,'in_progress':False,'error_kind':None} for p in c['enabled']}
    def refresh(self):
        if self.mocked:
            for r in mock(): self.data.setdefault(r.provider_id,[]).append(r)
            return
        def worker(pid):
            while not self.stop.is_set():
                with self.guard:
                    meta=self.provider_health.setdefault(pid,{'status':'PENDING','last_success_at':None,'error_kind':None})
                    meta.update(last_attempt_at=time.time(),in_progress=True)
                try:
                    result=fetch(pid)
                    with self.guard:
                        old=self.data.get(pid,[])
                        if result[0].status!='OK' and old and old[0].status in ('OK','STALE'): result=[replace(r,status='STALE',error_message=result[0].error_message) for r in old]
                        self.data[pid]=result
                        meta=self.provider_health[pid]
                        meta.update(status=result[0].status,in_progress=False,error_kind=None if result[0].status=='OK' else result[0].status)
                        if result[0].status=='OK': meta['last_success_at']=time.time()
                except Exception as e:
                    from urllib.error import HTTPError
                    summary=f'HTTP {e.code}' if isinstance(e,HTTPError) else type(e).__name__
                    logging.warning('%s refresh failed: %s',pid,summary)
                    with self.guard:
                        old=self.data.get(pid,[])
                        message=str(e) if pid=='cx' and isinstance(e,(TimeoutError,RuntimeError)) else summary
                        self.data[pid]=[replace(r,status='STALE',error_message=message) for r in old] if old and old[0].status in ('OK','STALE') else [Reading(pid,pid.upper(),status='ERROR',error_message=message)]
                        self.provider_health[pid].update(status=self.data[pid][0].status,in_progress=False,error_kind=summary)
                self.stop.wait(max(15,float(self.c['refresh_seconds'])))
        for pid in self.c['enabled']:
            threading.Thread(target=worker,args=(pid,),daemon=True).start()
    def pages(self):
        with self.guard:
            out=[r for pid in self.c['enabled'] for r in self.data.get(pid,[]) if not r.window or r.window in self.c['windows'] or (r.provider_id=='cx' and r.window.endswith('M'))]
        return out or [Reading('go','OpenCode Go',status='NOT_CONFIGURED')]
def main():
    p=argparse.ArgumentParser(); p.add_argument('--simulate',action='store_true'); p.add_argument('--mock',action='store_true'); p.add_argument('--hardware-test',action='store_true'); p.add_argument('--diagnose',action='store_true'); p.add_argument('--previews',action='store_true'); a=p.parse_args(); c=config()
    if a.diagnose:
        print('Python:',sys.version.split()[0],'AF_BLUETOOTH:',hasattr(socket,'AF_BLUETOOTH'),'MAC configured:',bool(c['mac']))
        try:
            from bluetooth_diagnose import inventory, pnp_inventory
            print('\n'.join(inventory()))
            print('\n'.join(pnp_inventory(c['mac'])))
        except Exception as exc: print('Bluetooth inventory failed:',type(exc).__name__)
        from display.b2 import peak_ratio
        if c.get('display_style')=='b3':
            from display.time_status import price_status
            print('DeepSeek B3 price state:',price_status(rules_path=c.get('deepseek_price_rules_file')))
        elif peak_ratio(0,c.get('deepseek_reference_peak_cny',100)) is None:
            print('DeepSeek reference peak invalid: neutral bar; set deepseek_reference_peak_cny > 0 (custom reference, not official quota).')
        import shutil
        print('Codex CLI:',bool(shutil.which('codex')))
        print('Pairing is not proof of communication. Check Windows Bluetooth settings and run hardware-test.bat.')
        return
    if a.previews:
        for i,r in enumerate(mock()): render(r).save(ROOT/'previews'/f'{i}_{r.provider_id}_{r.window or r.unit}_MOCK.png')
        return
    if not lock(): print('Another monitor instance is running.'); return
    (ROOT/'stop.request').unlink(missing_ok=True)
    if a.hardware_test:
        if not c['mac']: print('Set mac in config.json first.'); return
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', handlers=[logging.StreamHandler(), logging.handlers.RotatingFileHandler(ROOT/'hardware-diagnose.log',maxBytes=500000,backupCount=2,encoding='utf-8')])
        try:
            from bluetooth_diagnose import inventory, pnp_inventory
            for line in inventory()+pnp_inventory(c['mac']): logging.info('%s',line)
        except Exception as exc: logging.warning('Bluetooth inventory unavailable: %s',type(exc).__name__)
        d=Pixoo(c['mac'],int(c['port']))
        try:
            d.connect(); d.brightness(c['brightness'])
            for col in [(255,0,0),(0,255,0),(0,0,255)]: d.show(Image.new('RGB',(16,16),col)); time.sleep(2)
            d.show(render(mock()[0])); print('Frames sent. Confirm on device: red, green, blue, then GO 72. Hardware PASS requires your visual confirmation.')
        finally: d.close()
        return
    logging.basicConfig(level=logging.INFO,handlers=[logging.handlers.RotatingFileHandler(ROOT/'monitor.log',maxBytes=500000,backupCount=2,encoding='utf-8')])
    m=Monitor(c,a.mock); m.refresh()
    if a.simulate:
        import tkinter as tk
        root=tk.Tk(); root.title('Pixoo AI Monitor'); label=tk.Label(root); label.pack(); index=[0]
        sim_next=[0];sim_current=[0]
        def tick():
            pages=m.pages()
            if c.get('display_style')=='b3':
                if time.monotonic()>=sim_next[0]:
                    sim_current[0]=index[0]%len(pages);index[0]+=1
                    sim_next[0]=time.monotonic()+max(1,float(c['rotation_seconds']))
                r=pages[sim_current[0]%len(pages)]
                wait_ms=max(100,int(min(60,max(0,sim_next[0]-time.monotonic()))*1000))
            else:
                r=pages[index[0]%len(pages)];index[0]+=1;wait_ms=max(1000,int(c['rotation_seconds']*1000))
            image=render_configured(r,c).resize((320,320),Image.Resampling.NEAREST); photo=ImageTk.PhotoImage(image); label.configure(image=photo); label.image=photo; root.title(f'{r.display_name} {r.window or r.unit} | {r.status} | {r.source}'); root.after(wait_ms,tick)
        def close(): m.stop.set(); root.destroy()
        root.protocol('WM_DELETE_WINDOW',close); tick(); root.mainloop(); return
    d=Pixoo(c['mac'],int(c['port'])); delay=1; retry=0; last=None; index=0
    runtime=RuntimeStatus(ROOT/'runtime-status.json',c)
    runtime.write(m)
    next_rotation=0; current_page=0
    try:
        while not (ROOT/'stop.request').exists():
            runtime.write(m)
            start=time.monotonic(); pages=m.pages()
            if c.get('display_style')=='b3':
                if start>=next_rotation:
                    current_page=index%len(pages);index+=1
                    next_rotation=start+max(.1,float(c['rotation_seconds']))
                img=render_configured(pages[current_page%len(pages)],c)
            else:
                img=render_configured(pages[index%len(pages)],c);index+=1
            if c['mac'] and start>=retry:
                try:
                    if d.sock is None: d.connect(); d.brightness(c['brightness']); last=None
                    raw=img.tobytes()
                    if raw!=last:
                        d.show(img); last=raw
                        runtime.data.update(last_send_at=time.time(),frame_result='sent')
                    else: runtime.data['frame_result']='unchanged'
                    runtime.data['last_bluetooth_error']=None
                    delay=1
                except Exception as e:
                    logging.warning('Bluetooth failure: %s',type(e).__name__); d.close(); retry=time.monotonic()+delay; delay=min(delay*2,60); last=None
                    runtime.data.update(last_bluetooth_error=type(e).__name__,frame_result='waiting_reconnect')
            else:
                runtime.data['frame_result']='waiting_reconnect' if c['mac'] else 'not_configured'
            runtime.write(m,last_frame_check_at=time.time(),bluetooth_connected=d.sock is not None)
            wait=max(.1,float(c['rotation_seconds'])-(time.monotonic()-start))
            if c.get('display_style')=='b3': wait=max(.1,min(60,next_rotation-time.monotonic()))
            time.sleep(wait)
    except KeyboardInterrupt: pass
    finally:
        m.stop.set(); d.close()
        runtime.write(m,state='stopped',bluetooth_connected=False,frame_result='stopped')
if __name__=='__main__': main()


