. "$PSScriptRoot\common.ps1"
$report = @{utc=[DateTime]::UtcNow.ToString('o');python=(Test-Path $script:Python);config_present=(Test-Path '.env');frontend=(Test-Path 'frontend\dist\index.html');windows=[Environment]::OSVersion.VersionString;live_enabled=$false}
try { $report.health = Invoke-RestMethod 'http://127.0.0.1:8765/api/health' -TimeoutSec 3 } catch { $report.health = 'unreachable' }
# Whitelist only: no environment variables, credentials, raw logs or process command lines.
$report | ConvertTo-Json -Depth 8 | Tee-Object -FilePath (Join-Path $script:Runtime 'doctor-redacted.json')
