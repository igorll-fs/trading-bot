param(
    [string[]]$LogPaths = @("backend\\uvicorn.err"),
    [string]$PythonExe = ".\\.venv\\Scripts\\python.exe",
    [string]$Summarizer = "backend\\scripts\\summarize_error.py",
    [string]$Actions = "docs\\error_actions.json",
    [string]$Report = "logs\\last_error_report.md",
    [int]$BufferLines = 160,
    [string]$Pattern = "ERROR|Exception|Traceback",
    [int]$CooldownSeconds = 20,
    [switch]$PushToVSCode,
    [string]$CodeCli = "code"
)

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Resolve-AbsolutePath {
    param([string]$PathValue)

    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return $PathValue
    }

    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return $PathValue
    }

    return (Join-Path $repoRoot $PathValue)
}

function Invoke-CodePush {
    param(
        [string]$CodeCli,
        [string]$PayloadSource
    )

    try {
        Start-Process -FilePath $CodeCli -ArgumentList @('--command', 'igorSentinel.pushError') -WindowStyle Hidden -ErrorAction Stop
        Write-Host "[watcher] comando VS Code disparado (fonte: $PayloadSource)."
    }
    catch {
        Write-Warning "[watcher] não foi possível chamar '$CodeCli --command igorSentinel.pushError': $_"
    }
}

function Watch-LogPath {
    param(
        [string]$LogPath,
        [string]$Pattern,
        [int]$BufferLines,
        [int]$CooldownSeconds,
        [string]$PythonExe,
        [string]$Summarizer,
        [string]$Actions,
        [string]$Report,
        [switch]$PushToVSCode,
        [string]$CodeCli
    )

    $regex = New-Object System.Text.RegularExpressions.Regex($Pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    $buffer = New-Object System.Collections.Generic.List[string]
    $lastTrigger = Get-Date "1900-01-01"

    while (-not (Test-Path $LogPath)) {
        Write-Host "[watcher] aguardando arquivo $LogPath" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }

    Write-Host "[watcher] monitorando $LogPath" -ForegroundColor Cyan

    Get-Content -Path $LogPath -Wait -Tail 0 | ForEach-Object {
        $line = $_
        $buffer.Add($line)
        if ($buffer.Count -gt $BufferLines) {
            $buffer.RemoveAt(0)
        }

        if ($regex.IsMatch($line)) {
            $now = Get-Date
            if (($now - $lastTrigger).TotalSeconds -ge $CooldownSeconds) {
                $lastTrigger = $now

                $snippet = ($buffer -join [Environment]::NewLine)
                $tempFile = Join-Path $env:TEMP ("sentinel-snippet-" + [guid]::NewGuid().ToString() + ".log")
                $snippet | Set-Content -Path $tempFile -Encoding UTF8

                try {
                    $result = & $PythonExe $Summarizer --source $LogPath --snippet $tempFile --actions $Actions --report $Report --trigger-line $line 2>&1
                    $result | Write-Host

                    if ($PushToVSCode.IsPresent) {
                        Invoke-CodePush -CodeCli $CodeCli -PayloadSource $LogPath
                    }
                }
                catch {
                    Write-Warning "[watcher] falha ao chamar summarizer: $_"
                }
                finally {
                    if (Test-Path $tempFile) {
                        Remove-Item $tempFile -Force
                    }
                }
            }
        }
    }
}

$normalized = @()
foreach ($relativePath in $LogPaths) {
    $fullPath = Resolve-Path -Path $relativePath -ErrorAction SilentlyContinue
    if ($fullPath) {
        $normalized += $fullPath.ProviderPath
    }
    else {
        $normalized += (Join-Path $repoRoot $relativePath)
    }
}

if (-not $normalized -or $normalized.Count -eq 0) {
    throw "Nenhum caminho de log válido informado."
}

if ($normalized.Count -gt 1) {
    Write-Warning "Monitorando apenas o primeiro caminho: $($normalized[0]). Abra novas instâncias para múltiplos arquivos."
}

$pythonAbsolute = Resolve-AbsolutePath -PathValue $PythonExe
$summarizerAbsolute = Resolve-AbsolutePath -PathValue $Summarizer
$actionsAbsolute = Resolve-AbsolutePath -PathValue $Actions
$reportAbsolute = Resolve-AbsolutePath -PathValue $Report

Watch-LogPath -LogPath $normalized[0] -Pattern $Pattern -BufferLines $BufferLines -CooldownSeconds $CooldownSeconds -PythonExe $pythonAbsolute -Summarizer $summarizerAbsolute -Actions $actionsAbsolute -Report $reportAbsolute -PushToVSCode:$PushToVSCode -CodeCli $CodeCli
