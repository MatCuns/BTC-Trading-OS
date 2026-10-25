param([string]$Tag = 'v0.1.0-paper')
. "$PSScriptRoot\common.ps1"
if ($Tag -notmatch '^v\d+\.\d+\.\d+-paper$') { throw 'Only explicit PAPER release tags are accepted.' }
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git -or -not (Test-Path '.git')) { throw 'For a release ZIP: extract the new release into a new folder, copy only the local .env there, then run START_PAPER.bat. Keep the old folder for rollback. Never overwrite running files.' }
$origin = & git remote get-url origin
if ($origin -notin @('https://github.com/MatCuns/BTC-Trading-OS.git','https://github.com/MatCuns/BTC-Trading-OS')) { throw 'Unexpected origin. Refusing update.' }
if (& git status --porcelain) { throw 'Working tree contains changes. Preserve them before updating.' }
& "$PSScriptRoot\backup.ps1"
& "$PSScriptRoot\restore_check.ps1"
$old = & git rev-parse HEAD
Invoke-Checked 'git' @('fetch','origin','--tags')
$release = Invoke-RestMethod "https://api.github.com/repos/MatCuns/BTC-Trading-OS/releases/tags/$Tag" -TimeoutSec 15
if ($release.draft -or $release.prerelease) { throw 'Release is not an approved PAPER build.' }
& "$PSScriptRoot\stop.ps1"
try {
    Invoke-Checked 'git' @('switch','--detach',$Tag)
    # R1 has revision 0001 only. Future migrations must use an administrator in a
    # dedicated step, never grant schema ownership to the runtime role.
    & "$PSScriptRoot\first_run.ps1"
    if (-not $?) { throw 'Updated startup failed.' }
    $old | Set-Content (Join-Path $script:Runtime 'rollback-commit.txt')
} catch {
    & "$PSScriptRoot\stop.ps1"
    Invoke-Checked 'git' @('switch','--detach',$old)
    Write-Host 'Previous code restored. Re-run START_PAPER.bat to rebuild and reconcile. Database downgrade is never automatic.'
    throw
}
