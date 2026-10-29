# Updates EasyChange to the latest code on GitHub, rebuilds it and turns it back on.
# Run from this folder:
#   powershell -ExecutionPolicy Bypass -File update.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Stopping EasyChange..."
Get-Process EasyChange -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1  # let Windows release the files

Write-Host "Downloading the latest version..."
git fetch origin main
if ($LASTEXITCODE -ne 0) { throw "git fetch failed" }
# reset (not pull) so it also works after the history on GitHub was rewritten.
git reset --hard origin/main
if ($LASTEXITCODE -ne 0) { throw "git reset failed" }

Write-Host "Building..."
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
& powershell -ExecutionPolicy Bypass -File build.ps1
if ($LASTEXITCODE -ne 0) { throw "Build failed" }

Write-Host "Turning it on..."
& dist\EasyChange\EasyChange.exe --install
Write-Host ""
Write-Host "Done. EasyChange is updated."
