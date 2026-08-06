$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$NgrokConfig = Join-Path $Root "infrastructure\ngrok.yml"
$GlobalNgrokConfig = Join-Path $env:LOCALAPPDATA "ngrok\ngrok.yml"

Write-Host "Starting ngrok (web tunnel on port 3000)..." -ForegroundColor Cyan
Write-Host "Ensure the web app is running: npm run dev:web" -ForegroundColor Yellow
Write-Host "Ensure the API is running: scripts/dev-api.ps1" -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $GlobalNgrokConfig)) {
  throw "ngrok is not configured. Run: ngrok config add-authtoken <token>"
}

ngrok start web --config="$GlobalNgrokConfig" --config="$NgrokConfig"
