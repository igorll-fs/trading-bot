Write-Host "VS Code Remote - Instalacao Iniciando..." -ForegroundColor Cyan
$InstallDir = "$env:USERPROFILE\.code-server"
$CodeServerPort = 8080
$Password = -join ((48..57)+(65..90)+(97..122)|Get-Random -Count 16|%{[char]$_})
New-Item -ItemType Directory -Force -Path "$InstallDir\bin" | Out-Null
New-Item -ItemType Directory -Force -Path "$InstallDir\data" | Out-Null
@"
bind-addr: 127.0.0.1:$CodeServerPort
auth: password  
password: $Password
cert: false
user-data-dir: $InstallDir\data
"@ | Out-File "$InstallDir\config.yaml" -Encoding UTF8 -Force
$Password | Out-File "$InstallDir\password.txt" -Encoding UTF8 -Force
Write-Host "[OK] Config criada. Senha: $Password" -ForegroundColor Green
Write-Host "Baixando code-server... Aguarde 2-3 min" -ForegroundColor Yellow
$Url = "https://github.com/coder/code-server/releases/download/v4.23.1/code-server-4.23.1-windows-amd64.zip"
$Zip = "$env:TEMP\code-server.zip"
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri $Url -OutFile $Zip -UseBasicParsing -TimeoutSec 300
Expand-Archive -Path $Zip -DestinationPath "$env:TEMP\cs-extract" -Force
$Dir = Get-ChildItem "$env:TEMP\cs-extract" -Directory | Select -First 1
Copy-Item "$($Dir.FullName)\*" -Destination "$InstallDir\bin" -Recurse -Force
Remove-Item $Zip -Force
Remove-Item "$env:TEMP\cs-extract" -Recurse -Force
Write-Host "[OK] Instalado em: $InstallDir\bin" -ForegroundColor Green
$Cfg = "$env:USERPROFILE\.cloudflared\config.yml"
if (Test-Path $Cfg) {
  $Lines = Get-Content $Cfg
  $New = @()
  foreach ($L in $Lines) {
    if ($L -match "service: http_status:404") {
      $New += ""; $New += "  - hostname: code.botrading.uk"; $New += "    service: http://localhost:$CodeServerPort"
    }
    $New += $L
  }
  $New | Out-File $Cfg -Encoding UTF8 -Force
  Write-Host "[OK] Cloudflare tunnel configurado" -ForegroundColor Green
}
Write-Host ""; Write-Host "INSTALACAO CONCLUIDA!" -ForegroundColor Green
Write-Host "Senha: $Password" -ForegroundColor Yellow
Write-Host "Para iniciar: cd $InstallDir\bin; .\code-server.exe" -ForegroundColor Cyan
Write-Host "URL: https://code.botrading.uk" -ForegroundColor Magenta
