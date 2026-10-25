. "$PSScriptRoot\common.ps1"
Invoke-RestMethod 'http://127.0.0.1:8765/api/health' -TimeoutSec 5 | ConvertTo-Json -Depth 6
