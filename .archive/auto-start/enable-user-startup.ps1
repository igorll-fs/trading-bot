$ErrorActionPreference = 'Stop'

$scriptDir = $PSScriptRoot
$projectRoot = Split-Path -Parent $scriptDir
$launcher = Join-Path $scriptDir 'launch-startbat.ps1'

if (-not (Test-Path $launcher)) {
  Write-Error "Launcher não encontrado: $launcher"
}

# Comando para iniciar o launcher em background no logon do usuário
$cmd = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$launcher`""

New-Item -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'TradingBotAutoStart' -Value $cmd

Write-Host "Auto-start habilitado para o usuário atual. O bot iniciará no logon."
