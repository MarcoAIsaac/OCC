param(
  [string]$Python = "python",
  [string]$Name = "OCCDesktop",
  [string]$CodeSignPfxBase64 = "",
  [string]$CodeSignPassword = "",
  [string]$TimestampServer = "http://timestamp.digicert.com",
  [string]$FileDescription = "OCC Desktop",
  [string]$ProductName = "OCC Desktop",
  [switch]$BuildInstaller = $true
)

$ErrorActionPreference = "Stop"

function Sign-Binary {
  param(
    [string]$TargetPath,
    [string]$PfxPath,
    [string]$PfxPassword,
    [string]$SignTimestampServer,
    [string]$SignFileDescription,
    [string]$SignProductName
  )

  $signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -eq $signtool) {
    throw "signtool.exe not found on PATH. Install Windows SDK signing tools."
  }

  & $signtool.Source sign `
    /fd SHA256 `
    /td SHA256 `
    /f $PfxPath `
    /p $PfxPassword `
    /tr $SignTimestampServer `
    /d $SignFileDescription `
    /du "https://github.com/MarcoAIsaac/OCC" `
    /n $SignProductName `
    $TargetPath

  if ($LASTEXITCODE -ne 0) {
    throw "signtool failed with exit code $LASTEXITCODE for $TargetPath"
  }

  $signature = Get-AuthenticodeSignature -FilePath $TargetPath
  Write-Host "Authenticode signature status for $TargetPath : $($signature.Status)"
  if ($signature.Status -ne "Valid") {
    throw "Signature is not valid for $TargetPath . Status: $($signature.Status)"
  }
}

Write-Host "Building Windows desktop executable with PyInstaller..."

& $Python -m pip install --upgrade pip
& $Python -m pip install -e ".[dev]"
& $Python -m pip install pyinstaller

if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "release-windows") { Remove-Item -Recurse -Force "release-windows" }

New-Item -ItemType Directory -Path "build" | Out-Null

$iconPath = "build/occ_desktop.ico"
& $Python scripts/generate_windows_icon.py --ico-out $iconPath | Out-Null
if (!(Test-Path $iconPath)) {
  throw "Failed to generate icon at $iconPath"
}
$iconPath = (Resolve-Path $iconPath).Path

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onefile `
  --name $Name `
  --icon $iconPath `
  --copy-metadata occ-mrd-runner `
  --hidden-import occ.cli `
  --hidden-import occ.module_autogen `
  occ/desktop.py

New-Item -ItemType Directory -Path "release-windows" | Out-Null
$releaseDir = (Resolve-Path "release-windows").Path

$exeSource = "dist/$Name.exe"
$exeTarget = Join-Path $releaseDir "OCCDesktop-windows-x64.exe"
Copy-Item $exeSource $exeTarget -Force

$tempDir = if (![string]::IsNullOrWhiteSpace($env:RUNNER_TEMP)) {
  $env:RUNNER_TEMP
} else {
  [System.IO.Path]::GetTempPath()
}
$pfxPath = Join-Path $tempDir "occ_codesign.pfx"
$doSign = (![string]::IsNullOrWhiteSpace($CodeSignPfxBase64) -and ![string]::IsNullOrWhiteSpace($CodeSignPassword))

if ($doSign) {
  Write-Host "Code signing enabled."
  [System.IO.File]::WriteAllBytes($pfxPath, [System.Convert]::FromBase64String($CodeSignPfxBase64))
  try {
    Sign-Binary `
      -TargetPath $exeTarget `
      -PfxPath $pfxPath `
      -PfxPassword $CodeSignPassword `
      -SignTimestampServer $TimestampServer `
      -SignFileDescription $FileDescription `
      -SignProductName $ProductName
  }
  catch {
    throw
  }
}
else {
  Write-Host "Code signing skipped (certificate secrets not configured)."
}

$zipTarget = Join-Path $releaseDir "OCCDesktop-windows-x64.zip"
Compress-Archive -Path $exeTarget -DestinationPath $zipTarget -Force

$setupTarget = Join-Path $releaseDir "OCCDesktop-Setup-windows-x64.exe"
if ($BuildInstaller) {
  $iscc = Get-Command iscc.exe -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -eq $iscc) {
    throw "iscc.exe not found. Install Inno Setup to build installer."
  }

  $appVersion = (& $Python -c "from occ.version import get_version; print(get_version())").Trim()
  if ([string]::IsNullOrWhiteSpace($appVersion)) {
    $appVersion = "0.0.0"
  }

  $issScript = (Resolve-Path "scripts/windows/OCCDesktopSetup.iss").Path

  & $iscc.Source `
    "/DAppVersion=$appVersion" `
    "/DExeFile=$exeTarget" `
    "/DOutputDir=$releaseDir" `
    "/DSetupIconFile=$iconPath" `
    $issScript

  if (!(Test-Path $setupTarget)) {
    throw "Installer not generated at $setupTarget"
  }

  if ($doSign) {
    Sign-Binary `
      -TargetPath $setupTarget `
      -PfxPath $pfxPath `
      -PfxPassword $CodeSignPassword `
      -SignTimestampServer $TimestampServer `
      -SignFileDescription "$FileDescription Installer" `
      -SignProductName $ProductName
  }
}

if (Test-Path $pfxPath) {
  Remove-Item $pfxPath -Force -ErrorAction SilentlyContinue
}

$hashLines = @()
$hashLines += "$((Get-FileHash -Path $exeTarget -Algorithm SHA256).Hash.ToLowerInvariant())  OCCDesktop-windows-x64.exe"
$hashLines += "$((Get-FileHash -Path $zipTarget -Algorithm SHA256).Hash.ToLowerInvariant())  OCCDesktop-windows-x64.zip"
if (Test-Path $setupTarget) {
  $hashLines += "$((Get-FileHash -Path $setupTarget -Algorithm SHA256).Hash.ToLowerInvariant())  OCCDesktop-Setup-windows-x64.exe"
}

$hashPath = Join-Path $releaseDir "OCCDesktop-windows-x64.sha256"
$hashLines | Set-Content -Path $hashPath -Encoding ascii

Write-Host ""
Write-Host "Done. Release assets:"
Write-Host "  $exeTarget"
Write-Host "  $zipTarget"
if (Test-Path $setupTarget) { Write-Host "  $setupTarget" }
Write-Host "  $hashPath"
