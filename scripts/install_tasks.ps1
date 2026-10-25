param([switch]$Remove)
. "$PSScriptRoot\common.ps1"
$name = 'BTCQuantOS-PAPER'
if ($Remove) { Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue; return }
# Per-user interactive logon: no admin, password, SYSTEM account or public listener.
if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) { throw 'Task already exists. Use -Remove before replacing it.' }
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\start.ps1`"" -WorkingDirectory $script:RepoRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
try { Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Principal $principal -Description 'Local PAPER only; kill switch remains on after restart.' | Out-Null } catch { Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue; throw }
Write-Host 'Per-user logon task installed. Rollback: scripts\install_tasks.ps1 -Remove. It requires user logon; unattended boot hardening belongs to R3.'
