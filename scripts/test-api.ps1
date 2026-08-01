$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

uv run --directory "$Root\apps\api" pytest
