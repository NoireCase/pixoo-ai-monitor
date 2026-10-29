"""Read-only monitor health check. No Bluetooth, keyring or provider imports."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from runtime_health import evaluate,process_birth

ROOT=Path(__file__).resolve().parent

def process_inventory(target_pid=None):
    if os.name!='nt': return None
    script=r'''$ErrorActionPreference='Stop'
$project=$env:PIXOO_HEALTH_ROOT
$heartbeatPid=$env:PIXOO_HEALTH_PID
$processes=@(Get-CimInstance Win32_Process -Filter "name='python.exe' OR name='pythonw.exe'")
$selected=@($processes | Where-Object { $_.CommandLine -match '(?i)(?:^|[\s"''\\/])app\.py(?:[\s"'']|$)' -and $_.CommandLine -notmatch '--(simulate|previews|hardware-test|diagnose)(\s|$)' -and (($_.ExecutablePath -and $_.ExecutablePath.StartsWith($project+'\',[StringComparison]::OrdinalIgnoreCase)) -or $_.CommandLine.IndexOf($project+'\app.py',[StringComparison]::OrdinalIgnoreCase) -ge 0 -or ($heartbeatPid -and $_.ProcessId -eq [int]$heartbeatPid)) })
$ids=@($selected | ForEach-Object { $_.ProcessId })
$children=@($processes | Where-Object { $_.ParentProcessId -in $ids -and $_.CommandLine -match 'app\.py' })
@($selected+$children | Sort-Object ProcessId -Unique | ForEach-Object { @{pid=[int]$_.ProcessId;parent_pid=[int]$_.ParentProcessId} }) | ConvertTo-Json -Compress'''
    try:
        result=subprocess.run(['powershell','-NoProfile','-Command',script],capture_output=True,text=True,timeout=12,
                              env={**os.environ,'PIXOO_HEALTH_ROOT':str(ROOT),'PIXOO_HEALTH_PID':str(target_pid) if target_pid is not None else ''},creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if result.returncode: return None
        data=json.loads(result.stdout or '[]')
        return [data] if isinstance(data,dict) else data
    except (OSError,ValueError,subprocess.TimeoutExpired): return None

def read_snapshot(path):
    try:
        if Path(path).stat().st_size>65536: return None,'运行心跳文件过大或损坏。'
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        if data.get('schema_version')!=1: return None,'运行心跳版本不受支持。'
        import math
        for key in ('pid','heartbeat_at','heartbeat_timeout_seconds','refresh_seconds','provider_timeout_seconds'):
            value=data[key]
            if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value) or value<=0:
                raise ValueError('Invalid heartbeat')
        if not isinstance(data.get('providers'),dict): raise ValueError('Invalid providers')
        if not isinstance(data['pid'],int) or data.get('state') not in ('running','stopped'): raise ValueError('Invalid process state')
        for key in ('process_birth','last_send_at','last_frame_check_at','data_stale_seconds'):
            value=data.get(key)
            if value is not None and (not isinstance(value,(int,float)) or not math.isfinite(value)): raise ValueError('Invalid timestamp')
        for name,entry in data['providers'].items():
            if name not in ('go','cx','ds') or not isinstance(entry,dict): raise ValueError('Invalid provider')
            if entry.get('status') not in ('PENDING','OK','STALE','ERROR','NOT_CONFIGURED','UNSUPPORTED'): raise ValueError('Invalid provider status')
            for key in ('last_attempt_at','last_success_at'):
                value=entry.get(key)
                if value is not None and (not isinstance(value,(int,float)) or not math.isfinite(value)): raise ValueError('Invalid provider time')
            error=entry.get('error_kind')
            if error is not None:
                import re
                if not isinstance(error,str) or not re.fullmatch(r'[A-Za-z_]{1,64}|HTTP [0-9]{3}',error): raise ValueError('Invalid error kind')
        return data,None
    except FileNotFoundError: return None,None
    except (OSError,ValueError,KeyError,TypeError): return None,'无法读取运行心跳，文件可能损坏或权限不足。'

def main():
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description='Pixoo 只读进程健康自检')
    parser.add_argument('--json',action='store_true',help='以JSON输出安全的健康结论')
    args=parser.parse_args()
    snapshot,error=read_snapshot(ROOT/'runtime-status.json')
    processes=process_inventory(snapshot['pid'] if snapshot else None)
    try:
        report=evaluate(snapshot,processes,live_birth=process_birth(snapshot['pid']) if snapshot else None)
    except (KeyError,TypeError,ValueError):
        report={'overall':'UNKNOWN','checks':[{'level':'UNKNOWN','name':'heartbeat','message':'心跳结构损坏，无法判定健康。'}]}
    if error:
        report['overall']='UNKNOWN'
        report['checks'].append({'level':'UNKNOWN','name':'heartbeat_file','message':error})
    if args.json: print(json.dumps(report,ensure_ascii=False,indent=2))
    else:
        labels={'HEALTHY':'健康','DEGRADED':'运行中，但有异常','UNHEALTHY':'未运行或不健康','UNKNOWN':'信息不足，无法确认'}
        print('Pixoo AI Monitor 自检：'+labels[report['overall']]+' ('+report['overall']+')')
        names={'go':'OpenCode Go','cx':'Codex','ds':'DeepSeek','process':'进程','duplicates':'重复实例','heartbeat':'主循环心跳','identity':'进程身份','bluetooth':'蓝牙','last_send':'图像发送','state':'运行状态','providers':'数据来源','heartbeat_file':'心跳文件'}
        for c in report['checks']: print('['+c['level']+'] '+names.get(c['name'],c['name'])+'：'+c['message'])
        print('只读检查：不重启、不结束进程、不读取密钥、不调用额度API、不另开蓝牙连接。')
    return {'HEALTHY':0,'DEGRADED':1,'UNHEALTHY':2,'UNKNOWN':3}[report['overall']]

if __name__=='__main__': sys.exit(main())
