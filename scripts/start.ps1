. "$PSScriptRoot\common.ps1"
$pidFile = Join-Path $script:Runtime 'app.pid'
if (Test-Path $pidFile) {
    $oldId = [int](Get-Content $pidFile)
    $existing = Get-CimInstance Win32_Process -Filter "ProcessId=$oldId" -ErrorAction SilentlyContinue
    if ($existing -and $existing.CommandLine -like '*-m btc_os*' -and $existing.ExecutablePath -eq $script:Python) {
        Write-Host 'PAPER process already running.'
        return
    }
    Remove-Item $pidFile
}
if (-not (Test-Path '.env')) { throw 'Run START_PAPER.bat first.' }
$proc = Start-Process -FilePath $script:Python -ArgumentList @('-m','btc_os') -WorkingDirectory $script:RepoRoot -PassThru -WindowStyle Hidden -RedirectStandardOutput (Join-Path $script:Runtime 'stdout.log') -RedirectStandardError (Join-Path $script:Runtime 'stderr.log')
$proc.Id | Set-Content $pidFile
for ($attempt=0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Milliseconds 500
    try {
        $health = Invoke-RestMethod 'http://127.0.0.1:8765/api/health' -TimeoutSec 2
        if ($health.environment_id -eq 'INTERNAL_PAPER' -and $health.database) { Write-Host 'PAPER listening on http://127.0.0.1:8765'; return }
    } catch { }
    if ($proc.HasExited) { throw 'PAPER exited. Run doctor.ps1; local stderr.log may help.' }
}
throw 'PAPER readiness timed out. No new orders allowed; run doctor.ps1.'
