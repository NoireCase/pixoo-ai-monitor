"""Small, atomic runtime telemetry; deliberately excludes account/device values."""
import ctypes
from ctypes import wintypes
import json
import logging
import os
from pathlib import Path
import time
import re

def process_birth(pid):
    """Windows process creation time, to distinguish reused PIDs. None = unknown."""
    if os.name!='nt': return None
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    k.OpenProcess.restype=wintypes.HANDLE
    k.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=k.OpenProcess(0x1000,False,pid)
    if not handle: return None
    try:
        values=[wintypes.FILETIME() for _ in range(4)]
        if not k.GetProcessTimes(handle,*(ctypes.byref(v) for v in values)): return None
        return ((values[0].dwHighDateTime<<32)|values[0].dwLowDateTime)/10**7-11644473600
    finally: k.CloseHandle(handle)

class RuntimeStatus:
    def __init__(self,path,cfg):
        self.path=Path(path)
        rotation=max(1,float(cfg.get('rotation_seconds',5)))
        cadence=min(60,rotation) if cfg.get('display_style')=='b3' else rotation
        self.data={'schema_version':1,'pid':os.getpid(),'process_birth':process_birth(os.getpid()),
                   'started_at':time.time(),'state':'running','heartbeat_at':None,
                   'heartbeat_timeout_seconds':max(30,cadence*2+20),
                   'refresh_seconds':max(15,float(cfg.get('refresh_seconds',120))),
                   'data_stale_seconds':cfg.get('display_data_stale_seconds',max(300,float(cfg.get('refresh_seconds',120))*3)) if cfg.get('display_style')=='b3' else None,
                   'provider_timeout_seconds':75,'bluetooth_connected':False,
                   'frame_result':'starting','last_frame_check_at':None,'last_send_at':None,
                   'last_bluetooth_error':None,'providers':{}}
    def write(self,monitor,**changes):
        self.data.update(changes)
        self.data['heartbeat_at']=time.time()
        with monitor.guard:
            fields=('status','last_success_at','last_attempt_at','in_progress','error_kind')
            self.data['providers']={p:{k:v.get(k) for k in fields} for p,v in monitor.provider_health.items() if p in ('go','cx','ds')}
            for meta in self.data['providers'].values():
                if meta['status'] not in ('OK','PENDING','STALE','ERROR','NOT_CONFIGURED','UNSUPPORTED'): meta['status']='ERROR'
                error=meta['error_kind']
                if error is not None and (not isinstance(error,str) or not re.fullmatch(r'[A-Za-z_]{1,64}|HTTP [0-9]{3}',error)): meta['error_kind']='UNKNOWN_ERROR'
        temp=self.path.with_suffix('.json.tmp')
        try:
            temp.write_text(json.dumps(self.data,ensure_ascii=True,indent=2),encoding='utf-8')
            os.replace(temp,self.path)
        except OSError as exc:
            logging.warning('Health heartbeat write failed: %s',type(exc).__name__)

def evaluate(snapshot,processes,now=None,live_birth=None):
    """Pure evaluator; processes is a list of sanitized pid/parent_pid entries, or None."""
    now=time.time() if now is None else now
    checks=[]
    def add(level,name,message): checks.append({'level':level,'name':name,'message':message})
    if snapshot is None:
        if processes==[]: add('UNHEALTHY','process','未发现本项目监控进程；当前可能未启动。')
        else: add('UNKNOWN','heartbeat','没有运行心跳；可能仍是旧版进程，需要用 stop.bat / start.bat 重启一次。')
    else:
        pid=snapshot['pid']
        if processes is None:
            add('UNKNOWN','process','无权读取进程清单，不能独立确认进程或重复实例。')
        elif not any(p['pid']==pid for p in processes):
            add('UNHEALTHY','process','心跳所属进程已退出，不能将遗留心跳当成正在运行。')
        else:
            add('OK','process',f'监控进程 PID {pid} 存在。')
        if processes:
            ids={p['pid'] for p in processes}
            groups=[p for p in processes if p['parent_pid'] not in ids]
            if len(groups)>1: add('UNHEALTHY','duplicates',f'发现 {len(groups)} 组本项目进程，可能存在重复实例。')
            else: add('OK','duplicates','未发现多组监控实例；虚拟环境启动器及其子进程按一组计算。')
        recorded=snapshot.get('process_birth')
        if recorded is not None and live_birth is not None and abs(recorded-live_birth)>1:
            add('UNHEALTHY','identity','PID 已被其他进程复用，心跳不属于当前进程。')
        elif live_birth is None:
            add('UNKNOWN','identity','无法验证进程创建时间。')
        if snapshot.get('state')!='running': add('UNHEALTHY','state','监控已正常停止。')
        age=now-snapshot['heartbeat_at']
        reliable=snapshot.get('state')=='running' and 0<=age<=snapshot['heartbeat_timeout_seconds'] and processes is not None and any(p['pid']==pid for p in processes) and live_birth is not None and recorded is not None and abs(recorded-live_birth)<=1
        if age < -5: add('UNKNOWN','heartbeat','心跳时间位于未来，请检查系统时钟。')
        elif age>snapshot['heartbeat_timeout_seconds']:
            add('UNHEALTHY','heartbeat',f'主循环心跳已超时 {round(age)} 秒，可能卡住。')
        else: add('OK','heartbeat',f'主循环心跳正常，距今 {max(0,round(age))} 秒。')
        frame=snapshot.get('frame_result')
        if not reliable:
            add('UNKNOWN','bluetooth','心跳或进程未验证，不能据遗留 socket 状态判断当前蓝牙连接。')
        elif snapshot.get('bluetooth_connected'):
            if frame in ('sent','unchanged'):
                detail='本轮图像已发送。' if frame=='sent' else '画面未变，已正常跳过重复发送。'
                add('OK','bluetooth','现有 socket 为连接状态；'+detail)
            else: add('DEGRADED','bluetooth','连接状态存在，但尚未确认本轮画面检查完成。')
        else: add('DEGRADED','bluetooth','蓝牙未连接或正在重试；自检不会另开 socket。')
        if snapshot.get('last_send_at') is not None:
            add('OK','last_send',f'最近一次程序发送成功距今 {max(0,round(now-snapshot["last_send_at"]))} 秒；不等同于屏幕目视确认。')
        else: add('DEGRADED','last_send','尚无图像发送成功记录。')
        if not snapshot.get('providers'): add('DEGRADED','providers','未启用任何额度来源。')
        for provider,entry in snapshot.get('providers',{}).items():
            status=entry.get('status','PENDING');attempt=entry.get('last_attempt_at')
            budget=snapshot['provider_timeout_seconds']
            if attempt is not None and now-attempt < -5:
                add('UNKNOWN',provider,'刷新时间位于未来，请检查系统时钟。')
            elif attempt is not None and now-attempt > (budget if entry.get('in_progress') else snapshot['refresh_seconds']+budget):
                add('DEGRADED',provider,'刷新线程长时间未完成或未按时启动下一轮。')
            elif status=='OK':
                success=entry.get('last_success_at');stale=snapshot.get('data_stale_seconds')
                if success is None: add('UNKNOWN',provider,'缺少成功刷新时间，不能确认数据新鲜度。')
                elif stale is not None and now-success>stale: add('DEGRADED',provider,'上次成功数据已过期，画面可能显示 OLD。')
                else: add('OK',provider,'心跳记录最近一次真实额度刷新成功。')
            elif status=='PENDING': add('DEGRADED',provider,'正在等待首次刷新。')
            else: add('DEGRADED',provider,'当前状态 '+status+'；错误类别 '+str(entry.get('error_kind') or '无')+'。')
    levels={c['level'] for c in checks}
    overall='UNHEALTHY' if 'UNHEALTHY' in levels else 'UNKNOWN' if 'UNKNOWN' in levels else 'DEGRADED' if 'DEGRADED' in levels else 'HEALTHY'
    return {'overall':overall,'checks':checks}
