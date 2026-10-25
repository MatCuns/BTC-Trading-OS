. "$PSScriptRoot\common.ps1"
Invoke-Checked $script:Python @('-m','btc_os.cli','smoke')
$health = Invoke-RestMethod 'http://127.0.0.1:8765/api/health' -TimeoutSec 5
if ($health.live_enabled -or $health.environment_id -ne 'INTERNAL_PAPER' -or -not $health.database -or -not $health.reconciled) { throw 'Release health gate failed.' }
& "$PSScriptRoot\doctor.ps1"
Write-Host 'Local foundation verified. Feed may still be discovering. Server hardware/backup and forward-trading acceptance must be checked using docs/ACCEPTANCE.md.'
