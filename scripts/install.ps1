# Install TVwhere launcher on Windows.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BinDir = Join-Path $env:USERPROFILE "bin"
$Launcher = Join-Path $BinDir "tvwhere.cmd"

New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

@"
@echo off
cd /d "$Root"
py -m tvwhere %* 2>nul || python -m tvwhere %*
"@ | Set-Content -Path $Launcher -Encoding ASCII

# Add to user PATH if missing
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$BinDir;$userPath", "User")
    $env:Path = "$BinDir;$env:Path"
}

# Optional pip editable install
try {
    pip install -e $Root --quiet 2>$null
} catch {}

Write-Host "TVwhere installed."
Write-Host "  Project : $Root"
Write-Host "  Launch  : tvwhere"
Write-Host "  Or      : py -m tvwhere  (from project folder)"
