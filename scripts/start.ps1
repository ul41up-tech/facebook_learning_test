<#
.SYNOPSIS
  Starts the whole stack: Cloudflare quick tunnel -> Flask API -> React static build.

.DESCRIPTION
  1. cloudflared boots first and prints a random https://<name>.trycloudflare.com URL.
  2. That URL becomes PUBLIC_BASE_URL so the verification link inside the email
     points at the public host.
  3. Flask starts, serving the API and the built React app from frontend/dist.

  The URL changes every restart - that is what makes it a *temporary* domain.
#>
param(
  [int]$FlaskPort = 5055,
  [switch]$NoTunnel
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root 'backend'
$logDir = Join-Path $root '.logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$envFile = Join-Path $backend '.env'
if (-not (Test-Path $envFile)) {
  Copy-Item (Join-Path $backend '.env.example') $envFile
  Write-Host "[start] created backend/.env from .env.example - fill in the secrets" -ForegroundColor Yellow
}

# --- 1. tunnel -------------------------------------------------------------
$tunnelUrl = $null
if (-not $NoTunnel) {
  Write-Host "[start] launching cloudflared quick tunnel..." -ForegroundColor Cyan
  $tunnelLog = Join-Path $logDir 'cloudflared.log'
  $tunnelErr = Join-Path $logDir 'cloudflared.err.log'
  Remove-Item $tunnelLog, $tunnelErr -ErrorAction SilentlyContinue  # avoid matching a stale URL
  $proc = Start-Process -FilePath 'cloudflared' `
    -ArgumentList 'tunnel','--url',"http://127.0.0.1:$FlaskPort",'--no-autoupdate' `
    -RedirectStandardOutput $tunnelLog -RedirectStandardError $tunnelErr `
    -PassThru -WindowStyle Hidden

  for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 500
    $m = Select-String -Path @($tunnelLog, $tunnelErr) `
      -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -ErrorAction SilentlyContinue |
      Select-Object -First 1
    if ($m) { $tunnelUrl = $m.Matches[0].Value; break }
  }

  if ($tunnelUrl) {
    Write-Host "[start] tunnel URL: $tunnelUrl" -ForegroundColor Green
    Set-Content -Path (Join-Path $backend '.tunnel-url.txt') -Value $tunnelUrl -Encoding utf8
  } else {
    Write-Host "[start] could not detect the tunnel URL - check $logDir\cloudflared.log" -ForegroundColor Yellow
  }
} else {
  Write-Host "[start] tunnel disabled, using http://127.0.0.1:$FlaskPort" -ForegroundColor Yellow
}

# --- 2. persist PUBLIC_BASE_URL -------------------------------------------
if ($tunnelUrl) {
  $lines = Get-Content $envFile
  $found = $false
  $out = foreach ($line in $lines) {
    if ($line -match '^PUBLIC_BASE_URL=') { $found = $true; "PUBLIC_BASE_URL=$tunnelUrl" }
    else { $line }
  }
  if (-not $found) { $out += "PUBLIC_BASE_URL=$tunnelUrl" }
  Set-Content -Path $envFile -Value $out -Encoding utf8
}

# --- 3. flask --------------------------------------------------------------
Write-Host "[start] launching Flask on port $FlaskPort..." -ForegroundColor Cyan
$python = Join-Path $backend '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
  Write-Host "[start] virtualenv missing - run: cd backend; uv venv .venv; uv pip install -r requirements.txt" -ForegroundColor Red
  exit 1
}

Set-Location $backend
& $python -m flask --app app run --host 127.0.0.1 --port $FlaskPort
