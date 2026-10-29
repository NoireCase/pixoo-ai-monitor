"""Current-user scheduled task; only explicit GUI actions install/remove it."""
import os,sys,json,subprocess
from pathlib import Path
NAME='Pixoo AI Monitor V1'
def update(action):
    if action not in ('query','enable','disable'): raise ValueError('无效操作')
    if action=='enable' and not getattr(sys,'frozen',False): return {'ok':False,'error':'请从打包 EXE 配置登录自启'}
    env={**os.environ,'PIXOO_TASK_EXE':sys.executable}
    script="$ErrorActionPreference='Stop'; $name='Pixoo AI Monitor V1'; "
    if action=='enable':
        script+="$a=New-ScheduledTaskAction -Execute $env:PIXOO_TASK_EXE -Argument '--supervisor'; $t=New-ScheduledTaskTrigger -AtLogOn -User ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name); $s=New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; Register-ScheduledTask -TaskName $name -Action $a -Trigger $t -Settings $s -Force | Out-Null; "
    elif action=='disable': script+="Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue; "
    script+="try{$task=Get-ScheduledTask -TaskName $name -ErrorAction Stop}catch{if($_.FullyQualifiedErrorId -like '*CmdletizationQuery_NotFound*'){$task=$null}else{throw}}; if($task){'INSTALLED:'+$task.State}else{'NOT_INSTALLED'}"
    r=subprocess.run(['powershell','-NoProfile','-Command',script],capture_output=True,timeout=20,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if r.returncode: return {'ok':False,'error':'无法读取或修改任务计划；系统权限或服务不可用，操作未验证'}
    state=r.stdout.decode('ascii',errors='replace').strip()
    if action=='disable' and state!='NOT_INSTALLED': return {'ok':False,'error':'取消后任务仍存在，请检查权限'}
    return {'ok':True,'message':'未安装' if state=='NOT_INSTALLED' else ('已安装：'+state.split(':',1)[-1])}
