param(
    [switch]$Migrate
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "Installing root npm workspaces..."
Set-Location $Root
npm install

Write-Host "Installing Python dependencies with uv..."
uv sync --directory "$Root\apps\api"

if ($Migrate) {
    Write-Host "Running database migrations..."
    uv run --directory "$Root\apps\api" alembic upgrade head
}

Write-Host "Setup complete."
