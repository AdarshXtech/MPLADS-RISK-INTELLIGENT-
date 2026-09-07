param(
    [ValidateSet("start", "stop", "status")]
    [string]$Action = "status"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path $PSScriptRoot -Parent
$postgresBin = if ($env:SIH_POSTGRES_BIN) {
    $env:SIH_POSTGRES_BIN
} else {
    Join-Path $projectRoot ".local\postgresql-17.11\pgsql\bin"
}
$clusterPath = Join-Path $projectRoot ".local\postgresql-data-v2"
$pgCtl = Join-Path $postgresBin "pg_ctl.exe"

if (-not (Test-Path -LiteralPath $pgCtl) -or -not (Test-Path -LiteralPath $clusterPath)) {
    throw "The project-local PostgreSQL runtime is not installed. See docs/ingestion.md."
}

switch ($Action) {
    "start" {
        & $pgCtl -D $clusterPath status *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Output "PostgreSQL is already running."
            break
        }
        & $pgCtl -D $clusterPath -l (Join-Path $clusterPath "server.log") -o '"-p" "55432" "-c" "listen_addresses=127.0.0.1"' start
    }
    "stop" {
        & $pgCtl -D $clusterPath stop -m fast
    }
    "status" {
        & $pgCtl -D $clusterPath status
    }
}
