param([switch]$Full)
. "$PSScriptRoot\common.ps1"
$pg = Find-PgTool 'pg_restore'
if (-not $pg) { throw 'pg_restore not found.' }
Invoke-Checked $script:Python @('-m','btc_os.cli','restore-check','--executable',$pg)
if (-not $Full) { Write-Host 'Archive readable. Use restore_check.ps1 -Full for a real restore to a NEW isolated database.'; return }
$adminInput = Read-Host 'PostgreSQL administrator [postgres]'
$admin = if ($adminInput) { $adminInput } else { 'postgres' }
$secure = Read-Host 'Administrator password (never saved)' -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    $payload = @{admin=$admin;password=$plain} | ConvertTo-Json -Compress
    $payload | & $script:Python -m btc_os.cli restore-drill --executable $pg
    if ($LASTEXITCODE -ne 0) { throw 'Isolated restore failed. Operational database unchanged.' }
} finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr); $plain=$null; $payload=$null; $secure=$null }
