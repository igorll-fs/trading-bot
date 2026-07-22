# ============================================
# 🤖 AI SYNC - Sistema de Sincronização entre Sessões
# ============================================
# Uso: .\scripts\ai_sync.ps1 -Action [status|notify|check|work]
# ============================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("status", "notify", "check", "work", "help")]
    [string]$Action = "status",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("A", "B")]
    [string]$Session = "A",
    
    [Parameter(Mandatory=$false)]
    [string]$Message = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Task = ""
)

$ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$CHAT_FILE = Join-Path $ROOT "AI_CHAT.md"
$STATUS_FILE = Join-Path $ROOT ".ai_status.json"
$WORK_LOG = Join-Path $ROOT ".ai_work_log.jsonl"

# Cores para output
function Write-SessionA { param($msg) Write-Host "🅰️ $msg" -ForegroundColor Cyan }
function Write-SessionB { param($msg) Write-Host "🅱️ $msg" -ForegroundColor Magenta }
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "⚠️ $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }

# Inicializar arquivo de status se não existe
function Initialize-StatusFile {
    if (-not (Test-Path $STATUS_FILE)) {
        $initial = @{
            sessionA = @{
                status = "idle"
                lastAction = ""
                currentTask = ""
                timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
                files = @()
            }
            sessionB = @{
                status = "idle"
                lastAction = ""
                currentTask = ""
                timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
                files = @()
            }
            pendingMessages = @()
            sharedKnowledge = @()
        }
        $initial | ConvertTo-Json -Depth 10 | Set-Content $STATUS_FILE -Encoding UTF8
    }
}

# Ler status atual
function Get-AIStatus {
    Initialize-StatusFile
    return Get-Content $STATUS_FILE -Raw | ConvertFrom-Json
}

# Atualizar status de uma sessão
function Set-SessionStatus {
    param(
        [string]$Session,
        [string]$Status,
        [string]$Task = "",
        [string]$LastAction = "",
        [array]$Files = @()
    )
    
    $data = Get-AIStatus
    $sessionKey = "session$Session"
    
    $data.$sessionKey.status = $Status
    $data.$sessionKey.timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    
    if ($Task) { $data.$sessionKey.currentTask = $Task }
    if ($LastAction) { $data.$sessionKey.lastAction = $LastAction }
    if ($Files.Count -gt 0) { $data.$sessionKey.files = $Files }
    
    $data | ConvertTo-Json -Depth 10 | Set-Content $STATUS_FILE -Encoding UTF8
    Write-Success "Status da Sessão $Session atualizado"
}

# Adicionar mensagem pendente
function Add-PendingMessage {
    param(
        [string]$From,
        [string]$To,
        [string]$Message,
        [string]$Type = "INFO"
    )
    
    $data = Get-AIStatus
    $msg = @{
        id = "msg_" + (Get-Date -Format "yyyyMMddHHmmss")
        from = $From
        to = $To
        type = $Type
        message = $Message
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
        read = $false
    }
    
    $data.pendingMessages += $msg
    $data | ConvertTo-Json -Depth 10 | Set-Content $STATUS_FILE -Encoding UTF8
    Write-Success "Mensagem enviada para Sessão $To"
}

# Verificar mensagens pendentes
function Get-PendingMessages {
    param([string]$ForSession)
    
    $data = Get-AIStatus
    $pending = $data.pendingMessages | Where-Object { $_.to -eq $ForSession -and -not $_.read }
    return $pending
}

# Marcar mensagens como lidas
function Set-MessagesRead {
    param([string]$ForSession)
    
    $data = Get-AIStatus
    foreach ($msg in $data.pendingMessages) {
        if ($msg.to -eq $ForSession) {
            $msg.read = $true
        }
    }
    $data | ConvertTo-Json -Depth 10 | Set-Content $STATUS_FILE -Encoding UTF8
}

# Adicionar conhecimento compartilhado
function Add-SharedKnowledge {
    param(
        [string]$Session,
        [string]$Knowledge,
        [string]$Category = "discovery"
    )
    
    $data = Get-AIStatus
    $item = @{
        from = $Session
        category = $Category
        knowledge = $Knowledge
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    }
    
    $data.sharedKnowledge += $item
    $data | ConvertTo-Json -Depth 10 | Set-Content $STATUS_FILE -Encoding UTF8
    Write-Success "Conhecimento compartilhado adicionado"
}

# Log de trabalho
function Add-WorkLog {
    param(
        [string]$Session,
        [string]$Action,
        [string]$Details,
        [array]$Files = @()
    )
    
    $entry = @{
        session = $Session
        action = $Action
        details = $Details
        files = $Files
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    } | ConvertTo-Json -Compress
    
    Add-Content -Path $WORK_LOG -Value $entry -Encoding UTF8
}

# Mostrar status geral
function Show-Status {
    $data = Get-AIStatus
    
    Write-Host "`n" + "="*60 -ForegroundColor DarkGray
    Write-Host "🤖 STATUS DAS SESSÕES IA - $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')" -ForegroundColor White
    Write-Host "="*60 -ForegroundColor DarkGray
    
    # Session A
    Write-Host "`n🅰️ SESSÃO A (Backend/Trading)" -ForegroundColor Cyan
    Write-Host "   Status: $($data.sessionA.status)" -ForegroundColor $(if($data.sessionA.status -eq "working"){"Green"}else{"Yellow"})
    Write-Host "   Tarefa: $($data.sessionA.currentTask)"
    Write-Host "   Última ação: $($data.sessionA.lastAction)"
    Write-Host "   Timestamp: $($data.sessionA.timestamp)"
    if ($data.sessionA.files.Count -gt 0) {
        Write-Host "   Arquivos: $($data.sessionA.files -join ', ')"
    }
    
    # Session B
    Write-Host "`n🅱️ SESSÃO B (Frontend/UX)" -ForegroundColor Magenta
    Write-Host "   Status: $($data.sessionB.status)" -ForegroundColor $(if($data.sessionB.status -eq "working"){"Green"}else{"Yellow"})
    Write-Host "   Tarefa: $($data.sessionB.currentTask)"
    Write-Host "   Última ação: $($data.sessionB.lastAction)"
    Write-Host "   Timestamp: $($data.sessionB.timestamp)"
    if ($data.sessionB.files.Count -gt 0) {
        Write-Host "   Arquivos: $($data.sessionB.files -join ', ')"
    }
    
    # Mensagens pendentes
    $pendingA = ($data.pendingMessages | Where-Object { $_.to -eq "A" -and -not $_.read }).Count
    $pendingB = ($data.pendingMessages | Where-Object { $_.to -eq "B" -and -not $_.read }).Count
    
    Write-Host "`n📬 MENSAGENS PENDENTES" -ForegroundColor Yellow
    Write-Host "   Para Sessão A: $pendingA"
    Write-Host "   Para Sessão B: $pendingB"
    
    # Conhecimento compartilhado recente
    if ($data.sharedKnowledge.Count -gt 0) {
        Write-Host "`n🧠 CONHECIMENTO RECENTE" -ForegroundColor Green
        $recent = $data.sharedKnowledge | Select-Object -Last 3
        foreach ($k in $recent) {
            Write-Host "   [$($k.from)] $($k.knowledge)"
        }
    }
    
    Write-Host "`n" + "="*60 -ForegroundColor DarkGray
}

# Verificar conflitos de arquivos
function Test-FileConflict {
    param([string]$Session, [array]$Files)
    
    $data = Get-AIStatus
    $otherSession = if ($Session -eq "A") { "sessionB" } else { "sessionA" }
    
    $conflicts = @()
    foreach ($file in $Files) {
        if ($data.$otherSession.files -contains $file) {
            $conflicts += $file
        }
    }
    
    if ($conflicts.Count -gt 0) {
        Write-Warning "CONFLITO DETECTADO! Arquivos em uso pela outra sessão:"
        foreach ($c in $conflicts) {
            Write-Host "   - $c" -ForegroundColor Red
        }
        return $true
    }
    return $false
}

# Ações principais
switch ($Action) {
    "status" {
        Show-Status
    }
    
    "notify" {
        if (-not $Message) {
            Write-Error "Use: -Message 'sua mensagem' -Session [A|B]"
            exit 1
        }
        $to = if ($Session -eq "A") { "B" } else { "A" }
        Add-PendingMessage -From $Session -To $to -Message $Message
    }
    
    "check" {
        $pending = Get-PendingMessages -ForSession $Session
        if ($pending.Count -eq 0) {
            Write-Host "📭 Nenhuma mensagem pendente para Sessão $Session" -ForegroundColor Gray
        } else {
            Write-Host "`n📬 MENSAGENS PARA SESSÃO $Session" -ForegroundColor Yellow
            foreach ($msg in $pending) {
                Write-Host "`n[$($msg.timestamp)] De: Sessão $($msg.from)" -ForegroundColor Cyan
                Write-Host "   Tipo: $($msg.type)"
                Write-Host "   $($msg.message)"
            }
            
            $confirm = Read-Host "`nMarcar como lidas? (S/N)"
            if ($confirm -eq "S") {
                Set-MessagesRead -ForSession $Session
                Write-Success "Mensagens marcadas como lidas"
            }
        }
    }
    
    "work" {
        if (-not $Task) {
            Write-Error "Use: -Task 'descrição da tarefa' -Session [A|B]"
            exit 1
        }
        Set-SessionStatus -Session $Session -Status "working" -Task $Task
        Add-WorkLog -Session $Session -Action "started" -Details $Task
    }
    
    "help" {
        Write-Host ""
        Write-Host "AI SYNC - Sistema de Sincronizacao entre Sessoes" -ForegroundColor Cyan
        Write-Host "================================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "COMANDOS:" -ForegroundColor Yellow
        Write-Host "  .\ai_sync.ps1 -Action status          Mostra status de ambas sessoes"
        Write-Host "  .\ai_sync.ps1 -Action notify -Session A -Message 'msg'   Envia mensagem"
        Write-Host "  .\ai_sync.ps1 -Action check -Session B   Verifica mensagens pendentes"
        Write-Host "  .\ai_sync.ps1 -Action work -Session A -Task 'tarefa'   Marca trabalhando"
        Write-Host ""
        Write-Host "EXEMPLOS:" -ForegroundColor Yellow
        Write-Host "  .\ai_sync.ps1 -Action notify -Session A -Message 'Endpoints prontos!'"
        Write-Host "  .\ai_sync.ps1 -Action check -Session B"
        Write-Host "  .\ai_sync.ps1"
        Write-Host ""
    }
}
