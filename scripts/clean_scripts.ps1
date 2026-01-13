# Script de Limpeza dos Scripts - Remove dados pessoais
# Data: 15/01/2026

param(
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "LIMPEZA DE SCRIPTS - DADOS PESSOAIS" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "`nMODO DRY-RUN: Mostrando mudancas sem aplicar" -ForegroundColor Yellow
} else {
    Write-Host "`nMODO EXECUCAO: Aplicando mudancas" -ForegroundColor Green
}

# Arquivos que precisam ser corrigidos
$scriptsToFix = @{
    "prepare_github.ps1" = @{
        'C:\Users\igor\Desktop\17-10-2025-main' = '$PSScriptRoot\..'
        'cUsersigorDesktop17-10-2025-maintemp_trades.json' = 'temp_trades.json'
    }
    "start_system_simple.ps1" = @{
        'C:\Users\igor\Desktop\17-10-2025-main' = '$PSScriptRoot\..'
    }
    "start_system.ps1" = @{
        'C:\Users\igor\Desktop\17-10-2025-main' = '$PSScriptRoot\..'
    }
    "restart_simple.ps1" = @{
        'C:\Users\igor\Desktop\17-10-2025-main' = '$PSScriptRoot\..'
    }
    "start_remote_access.ps1" = @{
        'C:\Users\igor\cloudflared.exe' = 'cloudflared.exe'
    }
    "start_services.bat" = @{
        'C:\Users\igor\cloudflared.exe' = '%USERPROFILE%\cloudflared.exe'
        'C:\Users\igor\.cloudflared' = '%USERPROFILE%\.cloudflared'
    }
    "start_cloudflared_manual.bat" = @{
        'cd C:\Users\igor' = 'cd %USERPROFILE%'
    }
    "setup_autostart.bat" = @{
        'C:\Users\igor\cloudflared.exe' = '%USERPROFILE%\cloudflared.exe'
        'C:\Users\igor\.cloudflared' = '%USERPROFILE%\.cloudflared'
    }
    "install_cloudflare_service.bat" = @{
        'C:\Users\igor\cloudflared.exe' = '%USERPROFILE%\cloudflared.exe'
    }
}

$fixedCount = 0
$errorCount = 0

foreach ($scriptName in $scriptsToFix.Keys) {
    $scriptPath = Join-Path $PSScriptRoot $scriptName
    
    if (-not (Test-Path $scriptPath)) {
        Write-Host "  Arquivo nao encontrado: $scriptName" -ForegroundColor Yellow
        continue
    }
    
    Write-Host "`nProcessando: $scriptName" -ForegroundColor Cyan
    
    try {
        $content = Get-Content $scriptPath -Raw -Encoding UTF8
        $originalContent = $content
        $replacements = $scriptsToFix[$scriptName]
        
        foreach ($oldValue in $replacements.Keys) {
            $newValue = $replacements[$oldValue]
            
            if ($content -match [regex]::Escape($oldValue)) {
                $content = $content -replace [regex]::Escape($oldValue), $newValue
                
                if ($DryRun) {
                    Write-Host "  DRY-RUN: '$oldValue' -> '$newValue'" -ForegroundColor Yellow
                } else {
                    Write-Host "  Substituido: '$oldValue' -> '$newValue'" -ForegroundColor Green
                }
            }
        }
        
        if ($content -ne $originalContent) {
            if (-not $DryRun) {
                Set-Content -Path $scriptPath -Value $content -Encoding UTF8 -NoNewline
            }
            $fixedCount++
        } else {
            Write-Host "  Nenhuma alteracao necessaria" -ForegroundColor Gray
        }
        
    } catch {
        Write-Host "  ERRO ao processar: $_" -ForegroundColor Red
        $errorCount++
    }
}

# Verificar se ha outros caminhos hardcoded
Write-Host "`nVerificando outros caminhos hardcoded..." -ForegroundColor Cyan

$allScripts = Get-ChildItem -Path $PSScriptRoot -Include "*.ps1","*.bat" -File
$problematicPaths = @()

foreach ($script in $allScripts) {
    $content = Get-Content $script.FullName -Raw -ErrorAction SilentlyContinue
    
    if ($content -match 'C:\\Users\\[^\\]+' -or $content -match 'C:/Users/[^/]+') {
        $problematicPaths += $script.Name
    }
}

if ($problematicPaths.Count -gt 0) {
    Write-Host "`nAVISO: Arquivos com possiveis caminhos hardcoded:" -ForegroundColor Yellow
    foreach ($path in $problematicPaths) {
        Write-Host "  - $path" -ForegroundColor Yellow
    }
    Write-Host "`nRECOMENDACAO: Revisar manualmente esses arquivos" -ForegroundColor Yellow
} else {
    Write-Host "Nenhum caminho hardcoded adicional encontrado" -ForegroundColor Green
}

# Resumo
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "RESUMO DA LIMPEZA" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "`nMODO DRY-RUN - Nada foi modificado" -ForegroundColor Yellow
    Write-Host "Execute sem -DryRun para aplicar mudancas" -ForegroundColor Yellow
}

Write-Host "`nArquivos corrigidos: $fixedCount" -ForegroundColor $(if($fixedCount -gt 0){'Green'}else{'Gray'})
Write-Host "Erros: $errorCount" -ForegroundColor $(if($errorCount -gt 0){'Red'}else{'Green'})
Write-Host "Arquivos com avisos: $($problematicPaths.Count)" -ForegroundColor $(if($problematicPaths.Count -gt 0){'Yellow'}else{'Green'})

Write-Host "`nScript concluido!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
