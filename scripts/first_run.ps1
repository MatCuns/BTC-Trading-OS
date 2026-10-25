param([switch]$NoBrowser)
# Process-only execution policy is set by the launcher, never changed globally.
. "$PSScriptRoot\common.ps1"
Write-Host 'BTC QUANT OS | PAPER SETUP | No API keys or real orders' -ForegroundColor Cyan
try {
    Protect-LocalFile $script:Runtime
    if (-not [Environment]::Is64BitOperatingSystem) { throw 'Windows x64 is required.' }
    $basePython = $null
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        $value = & $py.Source -3.12 -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0) { $basePython = [string]$value }
    }
    if (-not $basePython) {
        $candidate = Get-Command python -ErrorAction SilentlyContinue
        if ($candidate) {
            $version = & $candidate.Source -c 'import sys; print(str(sys.version_info.major)+"."+str(sys.version_info.minor))' 2>$null
            if ($version -eq '3.12') { $basePython = $candidate.Source }
        }
    }
    if (-not $basePython) {
        Write-Host 'Step 1: install Python 3.12 x64 from https://www.python.org/downloads/windows/ (include the py launcher). Then reopen START_PAPER.bat.'
        throw 'Python 3.12 not detected. No installation attempted.'
    }
    if (-not (Test-Path $script:Python)) { Invoke-Checked $basePython @('-m','venv','.venv') }
    Invoke-Checked $script:Python @('-c','import sys; assert sys.version_info[:2] == (3,12)')
    Invoke-Checked $script:Python @('-m','pip','install','--disable-pip-version-check','-r','requirements/runtime.txt','-e','.')
    Save-Stage 'python-ready'
    $node = Get-Command node -ErrorAction SilentlyContinue
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    # Release archives contain a compiled terminal. Node is needed only for source checkouts.
    if ((Test-Path '.git') -or -not (Test-Path 'frontend\dist\index.html')) {
        if (-not $node -or -not $npm) {
            Write-Host 'Step 2: install Node.js 22 LTS x64 from https://nodejs.org/en/download. Reopen START_PAPER.bat. Existing steps are preserved.'
            throw 'Node/npm required to compile a source checkout.'
        }
        $major = [int]((& $node.Source --version).TrimStart('v').Split('.')[0])
        if ($major -lt 22) { throw 'Install Node.js 22 LTS or 24 LTS from https://nodejs.org/en/download, then rerun.' }
        Invoke-Checked $npm.Source @('ci','--prefix','frontend')
        Invoke-Checked $npm.Source @('run','build','--prefix','frontend')
    }
    Save-Stage 'frontend-ready'
    if (-not (Test-Path '.env')) {
        $pg = Find-PgTool 'psql'
        if (-not $pg) {
            Write-Host 'Step 3: install PostgreSQL 17 x64 using https://www.postgresql.org/download/windows/ . Keep the chosen administrator password local. Do not create a second instance if one is already installed. Then rerun.'
            throw 'PostgreSQL client not detected.'
        }
        Write-Host 'Select existing local folders. Nothing will be formatted, moved or removed.'
        $dataRoot = Read-Host 'Existing data folder (example E:\BTCData)'
        $backupRoot = Read-Host 'Existing backup folder on a separate destination'
        if (-not (Test-Path $dataRoot -PathType Container) -or -not (Test-Path $backupRoot -PathType Container)) { throw 'Both folders must already exist. Create the folders in Explorer and rerun.' }
        $dataRoot = [IO.Path]::GetFullPath($dataRoot)
        $backupRoot = [IO.Path]::GetFullPath($backupRoot)
        if ([IO.Path]::GetFullPath($dataRoot) -eq [IO.Path]::GetFullPath($backupRoot)) { throw 'Data and backup folders must differ.' }
        Write-Host 'Using an existing PostgreSQL service; no new instance or service will be created.'
        $hostName = '127.0.0.1'
        $portInput = Read-Host 'PostgreSQL port [5432]'
        $port = if ($portInput) { [int]$portInput } else { 5432 }
        $adminInput = Read-Host 'PostgreSQL administrator [postgres]'
        $admin = if ($adminInput) { $adminInput } else { 'postgres' }
        $secure = Read-Host 'PostgreSQL administrator password (never saved)' -AsSecureString
        $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try {
            $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
            $modeInput = Read-Host 'Feed: okx (public live, no keys) or fixture (synthetic offline) [okx]'
            $mode = if ($modeInput) { $modeInput.Trim().ToLower() } else { 'okx' }
            if ($mode -notin @('okx','fixture')) { throw 'Choose okx or fixture.' }
            $payload = @{host=$hostName;port=$port;admin=$admin;database='btc_quant';password=$plain;data_root=$dataRoot;backup_root=$backupRoot;feed_mode=$mode} | ConvertTo-Json -Compress
            # Only stdin carries the password: no command line, history or transcript.
            $payload | & $script:Python -m btc_os.cli db-setup
            if ($LASTEXITCODE -ne 0) { throw 'Database setup failed. Existing databases/roles are never overwritten. Check PostgreSQL locally; see OPERATIONS.md.' }
        } finally {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
            $plain = $null; $payload = $null; $secure = $null
        }
        Protect-LocalFile (Join-Path $script:RepoRoot '.env')
    } else { Write-Host 'Existing local .env preserved; resuming.' }
    Protect-LocalFile (Join-Path $script:RepoRoot '.env')
    Save-Stage 'database-ready'
    Invoke-Checked $script:Python @('-m','btc_os.cli','smoke')
    # No migrations run under the runtime role. Administrative migrations are isolated.
    Save-Stage 'smoke-passed'
    & "$PSScriptRoot\start.ps1"
    if (-not $?) { throw 'Application startup failed.' }
    & "$PSScriptRoot\verify_release.ps1"
    if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8765' }
    Save-Stage 'complete'
    Write-Host 'PAPER ready. Kill switch ON; strategy OFF. Read the feed label before unlocking PAPER.' -ForegroundColor Green
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host 'Resume by double-clicking START_PAPER.bat. Diagnostics: scripts\doctor.ps1. Never paste .env or database passwords into chat.'
    exit 1
}
