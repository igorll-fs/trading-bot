Param(
    [string]$Python = "$PSScriptRoot\..\.venv\Scripts\python.exe",
    [switch]$Install
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path $Python)) {
    throw "Python executable not found at $Python. Adjust the -Python parameter to point to your environment."
}

if ($Install.IsPresent) {
    Write-Host "📦 Installing backend dependencies..." -ForegroundColor Cyan
    & $Python -m pip install --disable-pip-version-check -r "$root\backend\requirements.txt"
}

Write-Host "🧹 Running Ruff lint..." -ForegroundColor Cyan
& $Python -m ruff check "$root\backend" "$root\tests" --fix

Write-Host "🎨 Running Black formatter..." -ForegroundColor Cyan
& $Python -m black "$root\backend" "$root\tests"

Write-Host "✅ Running pytest..." -ForegroundColor Cyan
& $Python -m pytest "$root\tests"

Write-Host "All quality checks completed successfully." -ForegroundColor Green
