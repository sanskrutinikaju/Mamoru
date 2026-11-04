# Run Mamoru backend tests (PowerShell).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:MAMORU_API_TOKEN = "test-token-ci"
$env:MAMORU_MAX_CONTENT_CHARS = "50000"
.\.venv\Scripts\python.exe -m pytest
