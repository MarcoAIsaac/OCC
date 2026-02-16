param(
  [string]$Python = "python",
  [string]$Name = "OCCDesktop"
)

$ErrorActionPreference = "Stop"

Write-Host "Building Windows desktop executable with PyInstaller..."

& $Python -m pip install --upgrade pip
& $Python -m pip install -e ".[dev]"
& $Python -m pip install pyinstaller

& $Python -m PyInstaller `
  --noconfirm `
  --windowed `
  --name $Name `
  --hidden-import occ.cli `
  --hidden-import occ.module_autogen `
  occ/desktop.py

Write-Host ""
Write-Host "Done. Executable folder:"
Write-Host "  dist/$Name/"
