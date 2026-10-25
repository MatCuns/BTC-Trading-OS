. "$PSScriptRoot\common.ps1"
$pg = Find-PgTool 'pg_dump'
if (-not $pg) { throw 'pg_dump not found. Install PostgreSQL command-line tools from the official installer.' }
Invoke-Checked $script:Python @('-m','btc_os.cli','backup','--executable',$pg)
