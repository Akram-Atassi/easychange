# Builds dist\EasyChange\EasyChange.exe. Run from this folder in PowerShell:
#   powershell -ExecutionPolicy Bypass -File build.ps1
$ErrorActionPreference = "Stop"
# Prefer the "py" launcher: the plain "python" command is often the Microsoft Store
# placeholder, which fails with "The system cannot find the path specified".
$py = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
& $py -m pip install --no-warn-script-location -r requirements.txt pyinstaller
# --onedir (not --onefile) so the wheel opens instantly instead of unpacking first.
& $py -m PyInstaller --noconfirm --clean --windowed --onedir `
    --name EasyChange `
    --hidden-import win32timezone `
    easychange.pyw
Write-Host ""
Write-Host "Built dist\EasyChange\EasyChange.exe"
Write-Host "Install with:  dist\EasyChange\EasyChange.exe --install"
