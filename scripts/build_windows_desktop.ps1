param(
  [string]$Python = "python",
  [string]$Name = "OCCDesktop",
  [string]$CodeSignPfxBase64 = "",
  [string]$CodeSignPassword = "",
  [string]$TimestampServer = "http://timestamp.digicert.com",
  [string]$FileDescription = "OCC Desktop",
  [string]$ProductName = "OCC Desktop"
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

if (![string]::IsNullOrWhiteSpace($CodeSignPfxBase64) -and ![string]::IsNullOrWhiteSpace($CodeSignPassword)) {
  Write-Host "Code signing executable with Authenticode..."
  $signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -eq $signtool) {
    throw "signtool.exe not found on PATH. Install Windows SDK signing tools."
  }

  $tempDir = if (![string]::IsNullOrWhiteSpace($env:RUNNER_TEMP)) {
    $env:RUNNER_TEMP
  } else {
    [System.IO.Path]::GetTempPath()
  }
  $pfxPath = Join-Path $tempDir "occ_codesign.pfx"
  [System.IO.File]::WriteAllBytes($pfxPath, [System.Convert]::FromBase64String($CodeSignPfxBase64))

  try {
    & $signtool.Source sign `
      /fd SHA256 `
      /td SHA256 `
      /f $pfxPath `
      /p $CodeSignPassword `
      /tr $TimestampServer `
      /d $FileDescription `
      /du "https://github.com/MarcoAIsaac/OCC" `
      /n $ProductName `
      $exeTarget

    if ($LASTEXITCODE -ne 0) {
      throw "signtool failed with exit code $LASTEXITCODE"
    }
  }
  finally {
    Remove-Item $pfxPath -Force -ErrorAction SilentlyContinue
  }

  $signature = Get-AuthenticodeSignature -FilePath $exeTarget
  Write-Host "Authenticode signature status: $($signature.Status)"
  if ($signature.Status -ne "Valid") {
    throw "Executable signature is not valid. Status: $($signature.Status)"
  }
}
else {
  Write-Host "Code signing skipped (certificate secrets not configured)."
}

$zipTarget = "release-windows/OCCDesktop-windows-x64.zip"
Compress-Archive -Path $exeTarget -DestinationPath $zipTarget -Force

$exeHash = (Get-FileHash -Path $exeTarget -Algorithm SHA256).Hash.ToLowerInvariant()
$zipHash = (Get-FileHash -Path $zipTarget -Algorithm SHA256).Hash.ToLowerInvariant()
$hashPath = "release-windows/OCCDesktop-windows-x64.sha256"
@(
  "$exeHash  OCCDesktop-windows-x64.exe",
  "$zipHash  OCCDesktop-windows-x64.zip"
) | Set-Content -Path $hashPath -Encoding ascii

Write-Host ""
Write-Host "Done. Release assets:"
Write-Host "  release-windows/OCCDesktop-windows-x64.exe"
Write-Host "  release-windows/OCCDesktop-windows-x64.zip"
Write-Host "  release-windows/OCCDesktop-windows-x64.sha256"
