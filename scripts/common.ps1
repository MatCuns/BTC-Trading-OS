Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$env:PYTHONIOENCODING = 'utf-8'
$script:RepoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $script:RepoRoot
$script:Runtime = Join-Path $script:RepoRoot '.runtime'
New-Item -ItemType Directory -Force $script:Runtime | Out-Null
$script:Python = Join-Path $script:RepoRoot '.venv\Scripts\python.exe'
function Invoke-Checked {
    param([string]$Command, [string[]]$Arguments)
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Step failed (exit $LASTEXITCODE). Rerun START_PAPER.bat to resume." }
}
function Find-PgTool {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $roots = @(Get-ChildItem "$env:ProgramFiles\PostgreSQL" -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending)
    foreach ($root in $roots) {
        $candidate = Join-Path $root.FullName "bin\$Name.exe"
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}
function Save-Stage {
    param([string]$Stage)
    @{stage=$Stage;utc=[DateTime]::UtcNow.ToString('o');environment='INTERNAL_PAPER'} | ConvertTo-Json | Set-Content (Join-Path $script:Runtime 'setup-state.json') -Encoding UTF8
}
function Protect-LocalFile {
    param([string]$Path)
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $grant = if (Test-Path $Path -PathType Container) { '(OI)(CI)F' } else { '(F)' }
    & icacls.exe $Path '/inheritance:r' '/grant:r' "${identity}:$grant" "SYSTEM:$grant" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Unable to restrict local configuration permissions.' }
}
