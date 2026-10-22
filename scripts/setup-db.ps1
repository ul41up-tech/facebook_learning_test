<#
.SYNOPSIS
  Creates the PostgreSQL database for the app, wires DATABASE_URL into backend/.env,
  and seeds demo accounts + posts.

.PARAMETER PgPassword
  Password of the local PostgreSQL superuser. If omitted you are prompted.
#>
param(
  [string]$PgPassword,
  [string]$PgUser = 'postgres',
  [string]$PgHost = '127.0.0.1',
  [string]$PgPort = '5432',
  [string]$DbName = 'facebook_clone'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root 'backend'
$envFile = Join-Path $backend '.env'

if (-not (Test-Path $envFile)) {
  Copy-Item (Join-Path $backend '.env.example') $envFile
}

# The password may come from -PgPassword, from secrets\pg_password.txt, or an
# interactive prompt. It is never echoed to the console.
$secretFile = Join-Path $backend 'secrets\pg_password.txt'
if (-not $PgPassword -and (Test-Path $secretFile)) {
  foreach ($raw in (Get-Content $secretFile)) {
    $line = $raw.Trim()
    if (-not $line -or $line.StartsWith('#')) { continue }
    if ($line -match '^PG_PASSWORD=(.*)$') { $PgPassword = $Matches[1].Trim() }
    else { $PgPassword = $line }
    break
  }
}

if (-not $PgPassword) {
  $secure = Read-Host -AsSecureString "PostgreSQL password for '$PgUser'"
  $PgPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
}

$env:PGPASSWORD = $PgPassword

Write-Host "[db] checking server on $PgHost`:$PgPort ..." -ForegroundColor Cyan
psql -U $PgUser -h $PgHost -p $PgPort -d postgres -v ON_ERROR_STOP=1 -c "SELECT version();" | Out-Null

Write-Host "[db] ensuring database '$DbName' exists ..." -ForegroundColor Cyan
$exists = psql -U $PgUser -h $PgHost -p $PgPort -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DbName';"
if ($exists -ne '1') {
  psql -U $PgUser -h $PgHost -p $PgPort -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE $DbName ENCODING 'UTF8';" | Out-Null
  Write-Host "[db] created database '$DbName'" -ForegroundColor Green
} else {
  Write-Host "[db] database '$DbName' already exists" -ForegroundColor DarkGray
}

# The password deliberately stays OUT of .env - it lives in secrets\pg_password.txt
# and config.py composes DATABASE_URL from it at runtime.
$settings = @{
  PG_USER = $PgUser
  PG_HOST = $PgHost
  PG_PORT = $PgPort
  PG_DB   = $DbName
}
$lines = Get-Content $envFile
foreach ($key in $settings.Keys) {
  $value = $settings[$key]
  $found = $false
  $out = foreach ($line in $lines) {
    if ($line -match "^$key=") { $found = $true; "$key=$value" } else { $line }
  }
  if (-not $found) { $out += "$key=$value" }
  $lines = $out
}
Set-Content -Path $envFile -Value $lines -Encoding utf8
Write-Host "[db] PG_* settings written to backend/.env (password stays in secrets\pg_password.txt)" -ForegroundColor Green

Write-Host "[db] seeding ..." -ForegroundColor Cyan
Push-Location $backend
try {
  & (Join-Path $backend '.venv\Scripts\python.exe') seed.py
} finally {
  Pop-Location
}

Write-Host "[db] done." -ForegroundColor Green
