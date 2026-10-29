$ErrorActionPreference='Stop'
$script=Join-Path $PSScriptRoot 'start.bat'
$action=New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ('/c ""' + $script + '""') -WorkingDirectory $PSScriptRoot
$trigger=New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
Register-ScheduledTask -TaskName 'Pixoo AI Monitor' -Action $action -Trigger $trigger -Description 'Start Pixoo AI Monitor after login' -Force | Out-Null
Write-Host 'Task created. Remove with: Unregister-ScheduledTask -TaskName "Pixoo AI Monitor"'
