# Install TVwhere on Windows.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BinDir = Join-Path $env:USERPROFILE "bin"
$Launcher = Join-Path $BinDir "tvwhere.cmd"
$WebLauncher = Join-Path $BinDir "tvwhere-web.cmd"

New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

@"
@echo off
set PYTHONPATH=$Root;%PYTHONPATH%
cd /d "$Root"
py -m tvwhere %* 2>nul || python -m tvwhere %*
"@ | Set-Content -Path $Launcher -Encoding ASCII

@"
@echo off
set PYTHONPATH=$Root;%PYTHONPATH%
cd /d "$Root"
py -m tvwhere --web --open %* 2>nul || python -m tvwhere --web --open %*
"@ | Set-Content -Path $WebLauncher -Encoding ASCII

try { pip install -e $Root --quiet 2>$null } catch {}

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$BinDir;$userPath", "User")
}

Write-Host "TVwhere 2.0 installed."
Write-Host "  Project   : $Root"
Write-Host "  Desktop   : tvwhere"
Write-Host "  Web/Mobile: tvwhere-web"
Write-Host "  Icon      : $Root\assets\icon.ico"
