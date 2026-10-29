"""Plain Chinese summaries for read-only diagnostic results."""
import json,time

def summarize(lines,state=None):
    radios=[s for s in lines if s.startswith('Radio:')]
    devices=[s for s in lines if s.startswith('Device:')]
    adapters=[]
    for line in lines:
        if line.startswith('PnP adapters:'):
            try: adapters=json.loads(line.split(':',1)[1].strip())
            except (ValueError,TypeError): pass
    adapter='已检测到' if radios else '暂未检测到，或 Windows 不允许读取'
    if adapters and all(a.get('Status')=='OK' for a in adapters): adapter='工作正常'
    paired=any('authenticated=True' in d for d in devices)
    rt=(state or {}).get('runtime',{})
    active=rt.get('bluetooth_connected') if rt.get('state')=='running' else None
    connected='已连接' if active is True else '尚未连接' if active is False else 'Windows 显示已连接' if any('connected=True' in d for d in devices) else '暂时无法确认'
    rows=['蓝牙适配器：'+adapter,'Pixoo 配对：'+('已配对' if paired else '未找到配对记录，请在 Windows 蓝牙设置中确认'),'Pixoo 连接：'+connected]
    last=rt.get('last_send_at')
    if last: rows.append('最近画面发送：'+time.strftime('%H:%M:%S',time.localtime(last)))
    if active is True: advice='当前连接正常，可以继续使用。'
    elif active is False: advice='请确认 Pixoo 已开机并在电脑附近，然后在设备页点击“重新连接”。'
    else: advice='请查看设备页的连接状态。如仍无法连接，请检查 Windows 蓝牙设置。'
    return '检查结果\n\n'+'\n'.join('• '+r for r in rows)+'\n\n'+advice+'\n\n本次检查不会中断画面或重新配对设备。'

def run(state=None,mac=''):
    from bluetooth_diagnose import inventory,pnp_inventory
    return {'ok':True,'title':'蓝牙诊断','message':summarize(inventory()+pnp_inventory(mac),state)}
