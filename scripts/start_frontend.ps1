$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $root "frontend")

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..."
    npm install
}

Write-Host "Starting AI MarketGuard React dashboard at http://127.0.0.1:5173"
npm run dev
