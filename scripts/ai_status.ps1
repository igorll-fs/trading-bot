# AI STATUS - Script simples para verificar status das sessoes
# Uso: .\scripts\ai_status.ps1

$ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$STATUS_FILE = Join-Path $ROOT ".ai_status.json"
$CHAT_FILE = Join-Path $ROOT "AI_CHAT.md"

Write-Host ""
Write-Host "============================================================" -ForegroundColor DarkGray
Write-Host "  AI SESSION STATUS - $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor DarkGray

# Verificar arquivo de status
if (Test-Path $STATUS_FILE) {
    $data = Get-Content $STATUS_FILE -Raw | ConvertFrom-Json
    
    Write-Host ""
    Write-Host "SESSION A (Backend/Trading)" -ForegroundColor Cyan
    Write-Host "  Status: $($data.sessionA.status)"
    Write-Host "  Tarefa: $($data.sessionA.currentTask)"
    Write-Host "  Ultimo: $($data.sessionA.lastAction)"
    
    Write-Host ""
    Write-Host "SESSION B (Frontend/UX)" -ForegroundColor Magenta
    Write-Host "  Status: $($data.sessionB.status)"
    Write-Host "  Tarefa: $($data.sessionB.currentTask)"
    Write-Host "  Ultimo: $($data.sessionB.lastAction)"
    
    # Contar mensagens pendentes
    $pendingA = ($data.pendingMessages | Where-Object { $_.to -eq "A" -and -not $_.read }).Count
    $pendingB = ($data.pendingMessages | Where-Object { $_.to -eq "B" -and -not $_.read }).Count
    
    Write-Host ""
    Write-Host "MENSAGENS PENDENTES" -ForegroundColor Yellow
    Write-Host "  Para Sessao A: $pendingA"
    Write-Host "  Para Sessao B: $pendingB"
    
} else {
    Write-Host ""
    Write-Host "Arquivo de status nao encontrado: $STATUS_FILE" -ForegroundColor Red
}

# Verificar tamanho do chat
if (Test-Path $CHAT_FILE) {
    $chatLines = (Get-Content $CHAT_FILE).Count
    Write-Host ""
    Write-Host "AI_CHAT.md: $chatLines linhas" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor DarkGray
Write-Host ""
