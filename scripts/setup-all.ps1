<#
.SYNOPSIS
  One-shot bootstrap: PostgreSQL database -> seed -> (optional) Resend sending
  domain -> Cloudflare quick tunnel + Flask.

.DESCRIPTION
  Reads every secret straight from files under backend\secrets\ so nothing has
  to be pasted into a chat window:

    backend\secrets\resend_api_key.txt   Resend API key
    backend\secrets\pg_password.txt      local PostgreSQL password
    backend\secrets\resend_domain.txt    sending domain for option B
    backend\secrets\cloudflare_api_token.txt  optional, auto DNS

  The files are never printed back to the console.
#>
param(
  [switch]$SkipDomain,
  [int]$FlaskPort = 5055,
  [switch]$NoTunnel
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root 'backend'
$python = Join-Path $backend '.venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
  Write-Host "[setup] creating the python venv ..." -ForegroundColor Cyan
  Push-Location $backend
  try {
    uv venv --python 3.14 .venv
    uv pip install --python .venv\Scripts\python.exe -r requirements.txt
  } finally { Pop-Location }
}

Write-Host "`n[1/4] PostgreSQL" -ForegroundColor Cyan
& (Join-Path $PSScriptRoot 'setup-db.ps1')

if (-not $SkipDomain) {
  Write-Host "`n[2/4] Resend sending domain (option B)" -ForegroundColor Cyan
  Push-Location $backend
  try {
    & $python setup_resend_domain.py
  } finally { Pop-Location }
} else {
  Write-Host "`n[2/4] skipping the Resend domain setup" -ForegroundColor DarkGray
}

Write-Host "`n[3/4] build the frontend" -ForegroundColor Cyan
if (Test-Path (Join-Path $root 'frontend\package.json')) {
  Push-Location (Join-Path $root 'frontend')
  try {
    if (-not (Test-Path 'node_modules')) { npm install }
    npm run build
  } finally { Pop-Location }
}

Write-Host "`n[4/4] starting Cloudflare tunnel + Flask" -ForegroundColor Cyan
& (Join-Path $PSScriptRoot 'start.ps1') -FlaskPort $FlaskPort -NoTunnel:$NoTunnel
