$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Set-Location "$Root\apps\api"
uv run python run_dev.py
