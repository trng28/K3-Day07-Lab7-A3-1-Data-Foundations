[CmdletBinding()]
param(
    [switch]$CoreOnly
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

Set-Location $projectRoot

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "Creating .venv..."
    python -m venv .venv
}

$requirementsFile = if ($CoreOnly) {
    "requirements.txt"
} else {
    "requirements-backend.txt"
}

Write-Host "Installing $requirementsFile with $venvPython..."
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $venvPython -m pip install -r $requirementsFile
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Requirements installed successfully."
Write-Host "Run backend:"
Write-Host ".\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"
