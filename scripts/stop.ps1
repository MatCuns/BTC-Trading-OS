. "$PSScriptRoot\common.ps1"
$pidFile = Join-Path $script:Runtime 'app.pid'
if (-not (Test-Path $pidFile)) { Write-Host 'No managed process recorded.'; return }
$appId = [int](Get-Content $pidFile)
$proc = Get-CimInstance Win32_Process -Filter "ProcessId=$appId" -ErrorAction SilentlyContinue
if ($proc) {
    if ($proc.CommandLine -notlike '*-m btc_os*' -or $proc.ExecutablePath -ne $script:Python) { throw 'PID ownership mismatch. Refusing to stop another process.' }
    Stop-Process -Id $appId
}
Remove-Item $pidFile
Write-Host 'PAPER stopped. Pending paper remainder will be cancelled and reconciled on next startup.'
