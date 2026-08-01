$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Set-Location "$Root\apps\api"
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
