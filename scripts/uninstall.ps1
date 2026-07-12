$BinDir = Join-Path $env:USERPROFILE "bin"
$Launcher = Join-Path $BinDir "tvwhere.cmd"
if (Test-Path $Launcher) { Remove-Item $Launcher -Force }
Write-Host "TVwhere launcher removed."
