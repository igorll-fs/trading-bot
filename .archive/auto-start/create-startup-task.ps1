$ErrorActionPreference = 'Stop'

# Resolve project root based on this script location
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$startBat = Join-Path $projectRoot 'start.bat'

if (-not (Test-Path $startBat)) {
  Write-Error "start.bat não encontrado em $startBat"
}

$taskName = 'TradingBot AutoStart'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -WindowStyle Hidden -Command `"Start-Process -FilePath '$startBat' -WorkingDirectory '$projectRoot'`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

try {
  if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false | Out-Null
  }
} catch {}

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal | Out-Null
Write-Host "Tarefa agendada '$taskName' criada. O bot iniciará automaticamente no logon."
