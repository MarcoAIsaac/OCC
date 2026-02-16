param(
  [string]$Python = "python",
  [string]$Name = "OCCDesktop"
)

$ErrorActionPreference = "Stop"

Write-Host "Building Windows desktop executable with PyInstaller..."

& $Python -m pip install --upgrade pip
& $Python -m pip install -e ".[dev]"
& $Python -m pip install pyinstaller

if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "release-windows") { Remove-Item -Recurse -Force "release-windows" }

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onefile `
  --name $Name `
  --hidden-import occ.cli `
  --hidden-import occ.module_autogen `
  occ/desktop.py

New-Item -ItemType Directory -Path "release-windows" | Out-Null

$exeSource = "dist/$Name.exe"
$exeTarget = "release-windows/OCCDesktop-windows-x64.exe"

Copy-Item $exeSource $exeTarget -Force
Compress-Archive -Path $exeTarget -DestinationPath "release-windows/OCCDesktop-windows-x64.zip" -Force

Write-Host ""
Write-Host "Done. Release assets:"
Write-Host "  release-windows/OCCDesktop-windows-x64.exe"
Write-Host "  release-windows/OCCDesktop-windows-x64.zip"
