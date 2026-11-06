# FanGoblin modifications by ZenoBell, 2026-11-06. See CHANGES_FROM_UPSTREAM.md.
# Build the OnlyGoblins Windows GUI with the local project environment.
[CmdletBinding()]
param([string]$Python = (Join-Path $PSScriptRoot '.venv\Scripts\python.exe'))
$ErrorActionPreference = 'Stop'
if (!(Test-Path -LiteralPath $Python)) {
    throw 'Create .venv and install requirements-dev.txt, or pass -Python with a Python executable path.'
}
Push-Location $PSScriptRoot
try {
    & $Python -X utf8 (Join-Path $PSScriptRoot 'build_exe.py')
    if ($LASTEXITCODE -ne 0) { throw "OnlyGoblins build failed with exit code $LASTEXITCODE" }
} finally { Pop-Location }
