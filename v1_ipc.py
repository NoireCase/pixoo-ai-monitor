"""Current-user local socket for the V1 worker; no credentials leave the worker."""
import base64
import json
import os
import threading
from pathlib import Path
from PySide6.QtNetwork import QLocalServer

from v1_security import scope, token
import hmac,time
from v1_wire import valid,response
NAME = scope()+'PixooAIMonitorV1_' + str(os.getlogin()).replace(' ', '_')

def snapshot(monitor, runtime):
    with monitor.guard:
        readings = {p: [{'window': r.window, 'value': str(r.remaining_value) if r.remaining_value is not None else None,
                         'percent': r.remaining_percent, 'unit': r.unit, 'status': r.status}
                        for r in values] for p, values in monitor.data.items()}
        health = {p: dict(v) for p, v in monitor.provider_health.items()}
    d = runtime.data.copy()
    allowed = ('pid','state','heartbeat_at','heartbeat_timeout_seconds','bluetooth_connected','last_send_at',
               'frame_result','last_frame_png','last_page','last_bluetooth_error')
    result = {k:d.get(k) for k in allowed}
    result['last_frame_png'] = getattr(runtime, 'last_frame_png', None)
    result['last_page'] = getattr(runtime, 'last_page', None)
    from display.time_status import price_status
    result['mode']='MOCK' if monitor.mocked else 'LIVE'
    return {'runtime':result, 'readings':readings, 'providers':health,'price_status':price_status(rules_path=monitor.c.get('deepseek_price_rules_file'))[0],'config':{k:monitor.c.get(k) for k in ('brightness','enabled','enabled_pages','display_style','rotation_seconds','refresh_seconds')}}

def serve(monitor, runtime, root, commands=None):
    def run():
        server = QLocalServer()
        server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        if not server.listen(NAME):
            return
        seen={}
        while not monitor.stop.is_set():
            if not server.waitForNewConnection(500):
                continue
            sock = server.nextPendingConnection()
            if not sock: continue
            if not sock.bytesAvailable(): sock.waitForReadyRead(1000)
            raw=bytes(sock.readAll())
            while b'\n' not in raw and len(raw)<32768 and sock.waitForReadyRead(300): raw+=bytes(sock.readAll())
            request={}
            try:
                request=json.loads(raw.decode('utf-8'))
                expected=token()
                if not valid(request,expected) or abs(time.time()-float(request.get('at',0)))>30: raise ValueError('unauthorized')
                nonce=request.get('nonce')
                seen={n:t for n,t in seen.items() if time.time()-t<35}
                if not isinstance(nonce,str) or nonce in seen: raise ValueError('replay')
                seen[nonce]=time.time()
                command=request.get('command'); args=request.get('args',{})
                if command=='status': data=snapshot(monitor,runtime)
                elif command=='stop':
                    (Path(root)/'stop.request').write_text('stop',encoding='ascii')
                    data={'ok':True}
                elif command in ('apply','reconnect','hardware') and commands:
                    data=commands.request(command,args)
                else: data={'ok':False,'error':'不支持的命令'}
            except Exception:
                data={'ok':False,'error':'请求未授权或格式无效'}
            key=token()
            reply=response(data,request.get('nonce'),key) if key and isinstance(request,dict) else {'data':{'ok':False}}
            sock.write(json.dumps(reply, ensure_ascii=False).encode('utf-8'))
            sock.flush(); sock.waitForBytesWritten(1000); sock.disconnectFromServer()
        server.close()
    threading.Thread(target=run, daemon=True, name='v1-ipc').start()
