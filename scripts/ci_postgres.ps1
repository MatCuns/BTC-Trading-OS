# CI-only temporary PostgreSQL cluster. Never called by the server installer.
$ErrorActionPreference = 'Stop'
$root = Get-ChildItem "$env:ProgramFiles\PostgreSQL" -Directory | Sort-Object Name -Descending | Select-Object -First 1
if (-not $root) { throw 'GitHub Windows runner has no PostgreSQL binaries.' }
$bin = Join-Path $root.FullName 'bin'
$cluster = Join-Path $env:RUNNER_TEMP 'btc-ci-postgres'
if (Test-Path $cluster) { throw 'CI cluster directory already exists; refusing reuse.' }
& "$bin\initdb.exe" -D $cluster -U postgres -A trust -E UTF8
if ($LASTEXITCODE -ne 0) { throw 'initdb failed' }
& "$bin\pg_ctl.exe" -D $cluster -l (Join-Path $env:RUNNER_TEMP 'postgres.log') -o '-p 55432 -h 127.0.0.1' -w start
if ($LASTEXITCODE -ne 0) { throw 'pg_ctl failed' }
& "$bin\createdb.exe" -h 127.0.0.1 -p 55432 -U postgres btc_test
if ($LASTEXITCODE -ne 0) { throw 'createdb failed' }
"$bin" | Out-File $env:GITHUB_PATH -Encoding utf8 -Append
