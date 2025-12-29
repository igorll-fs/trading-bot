$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$startBat = Join-Path $projectRoot 'start.bat'

if (-not (Test-Path $startBat)) {
  Write-Error "start.bat não encontrado em $startBat"
}

Start-Process -FilePath $startBat -WorkingDirectory $projectRoot
