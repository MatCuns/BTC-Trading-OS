# Parse every script without executing setup, tasks, installers or account operations.
$ErrorActionPreference = 'Stop'
$errorsFound = @()
Get-ChildItem $PSScriptRoot -Filter '*.ps1' | ForEach-Object {
    $tokens = $null; $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$tokens, [ref]$parseErrors) | Out-Null
    $errorsFound += @($parseErrors)
}
if ($errorsFound.Count -gt 0) { $errorsFound | Format-List; throw 'PowerShell parse checks failed.' }
Write-Host 'All PowerShell scripts parsed successfully. No tasks, installs or services were changed.'
