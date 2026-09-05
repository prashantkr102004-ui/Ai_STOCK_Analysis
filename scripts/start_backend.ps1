$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv .venv
}

Write-Host "Starting AI MarketGuard FastAPI backend at http://127.0.0.1:8000"
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
