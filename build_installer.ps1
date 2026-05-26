$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
$Version = "1.0.0"

Write-Host "== Manualtech build =="
Write-Host "Project: $ProjectRoot"
Write-Host "Version: $Version"

python -m pip install -r requirements.txt
python -m pip install pyinstaller

Write-Host "Compilando Manualtech.exe..."
python -m PyInstaller --noconfirm .\Manualtech.spec

$InnoCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)

$ISCC = $InnoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $ISCC) {
    Write-Host "Inno Setup no esta instalado."
    Write-Host "Instalalo con: winget install --id JRSoftware.InnoSetup -e"
    Write-Host "Despues ejecuta de nuevo: .\build_installer.ps1"
    exit 1
}

Write-Host "Creando instalador con Inno Setup..."
& $ISCC .\installer\Manualtech.iss

$InstallerPath = Join-Path $ProjectRoot "installer_output\Manualtech_${Version}_Setup.exe"
$ReleaseDir = Join-Path $ProjectRoot "release"
$ZipPath = Join-Path $ReleaseDir "Manualtech_${Version}_MSL.zip"

if (-not (Test-Path $InstallerPath)) {
    throw "No se encontro el instalador esperado: $InstallerPath"
}

New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null

$PackageFiles = @(
    $InstallerPath,
    (Join-Path $ProjectRoot "LICENSE.txt"),
    (Join-Path $ProjectRoot "EULA.txt"),
    (Join-Path $ProjectRoot "THIRD_PARTY_NOTICES.md"),
    (Join-Path $ProjectRoot "TERMS_OF_SALE.md"),
    (Join-Path $ProjectRoot "PRIVACY_POLICY.md"),
    (Join-Path $ProjectRoot "REFUND_POLICY.md")
)

Write-Host "Creando ZIP comercial..."
Compress-Archive -Path $PackageFiles -DestinationPath $ZipPath -Force

Write-Host "Build completado."
Write-Host "EXE: $ProjectRoot\dist\Manualtech.exe"
Write-Host "Instalador: $InstallerPath"
Write-Host "ZIP comercial: $ZipPath"
