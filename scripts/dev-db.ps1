$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Set-Location $Root
docker compose -f infrastructure/docker-compose.yml up -d
