# Builds dist\EasyChange\EasyChange.exe. Run from this folder in PowerShell:
#   powershell -ExecutionPolicy Bypass -File build.ps1
# GitHub Actions runs this same script to make the Release download.
$ErrorActionPreference = "Stop"
# Prefer the "py" launcher: the plain "python" command is often the Microsoft Store
# placeholder, which fails with "The system cannot find the path specified".
# GitHub Actions sets $env:PYTHON to pick its exact Python.
$py = if ($env:PYTHON) { $env:PYTHON } elseif (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
& $py -m pip install --no-warn-script-location -r requirements.txt pyinstaller
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
# Generate the UI Automation wrapper now so it gets bundled (used to open the
# wheel over the file's icon).
& $py -c "import comtypes.client as c; c.GetModule('UIAutomationCore.dll')"
if ($LASTEXITCODE -ne 0) { throw "Generating the UI Automation wrapper failed" }
# --onedir (not --onefile) so the wheel opens instantly instead of unpacking first.
# --collect-all: these packages ship DLLs/data files PyInstaller can miss.
& $py -m PyInstaller --noconfirm --clean --windowed --onedir `
    --name EasyChange `
    --hidden-import win32timezone `
    --collect-all pillow_heif `
    --collect-all pypdfium2 `
    --collect-all pypdfium2_raw `
    --collect-all docx `
    --collect-submodules comtypes `
    easychange.pyw
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }
Write-Host ""
Write-Host "Built dist\EasyChange\EasyChange.exe"
Write-Host "Install with:  dist\EasyChange\EasyChange.exe --install"
