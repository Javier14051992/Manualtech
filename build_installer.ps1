$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
$Version = "1.0.0"

Write-Host "== Manualtech build =="
Write-Host "Project: $ProjectRoot"
Write-Host "Version: $Version"

Write-Host "Limpiando builds anteriores..."
foreach ($DirName in @("build", "dist", "installer_output", "release")) {
    $DirPath = Join-Path $ProjectRoot $DirName
    if (Test-Path $DirPath) {
        Remove-Item -LiteralPath $DirPath -Recurse -Force
    }
}

python -m pip install -r requirements.txt
python -m pip install pyinstaller

Write-Host "Compilando Manualtech..."
python -m PyInstaller --noconfirm .\Manualtech.spec

$InnoCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)

$ISCC = $InnoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $ISCC) {
    Write-Host "Inno Setup no está instalado."
    Write-Host "Instálalo con: winget install --id JRSoftware.InnoSetup -e"
    Write-Host "Después ejecuta de nuevo: .\build_installer.ps1"
    exit 1
}

Write-Host "Creando instalador..."
& $ISCC .\installer\Manualtech.iss

$InstallerPath = Join-Path $ProjectRoot "installer_output\Manualtech_${Version}_Setup.exe"
$ReleaseDir = Join-Path $ProjectRoot "release"
$ZipPath = Join-Path $ReleaseDir "Manualtech_${Version}_Beta_MSL.zip"

if (-not (Test-Path $InstallerPath)) {
    throw "No se encontró el instalador esperado: $InstallerPath"
}

New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null

$PackageFiles = @(
    $InstallerPath,
    (Join-Path $ProjectRoot "LICENSE.txt"),
    (Join-Path $ProjectRoot "EULA.txt"),
    (Join-Path $ProjectRoot "THIRD_PARTY_NOTICES.md"),
    (Join-Path $ProjectRoot "TERMS_OF_SALE.md"),
    (Join-Path $ProjectRoot "PRIVACY_POLICY.md"),
    (Join-Path $ProjectRoot "REFUND_POLICY.md"),
    (Join-Path $ProjectRoot "README.md")
)

Write-Host "Creando ZIP comercial..."
Compress-Archive -Path $PackageFiles -DestinationPath $ZipPath -Force

$BlockedEntries = @(
    "data/manuales",
    "data/previews",
    "data/manuales.db",
    "logs/",
    "build/",
    "dist/",
    "installer_output/",
    "__pycache__/",
    ".venv/"
)

Add-Type -AssemblyName System.IO.Compression.FileSystem
$Archive = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
try {
    foreach ($Entry in $Archive.Entries) {
        $EntryName = $Entry.FullName.Replace("\", "/")
        foreach ($BlockedEntry in $BlockedEntries) {
            if ($EntryName.StartsWith($BlockedEntry, [System.StringComparison]::OrdinalIgnoreCase)) {
                throw "El ZIP contiene una ruta no permitida: $EntryName"
            }
        }
        if ($EntryName.EndsWith(".pdf", [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "El ZIP contiene un PDF privado o no permitido: $EntryName"
        }
    }
}
finally {
    $Archive.Dispose()
}

Write-Host "Build finalizado correctamente."
Write-Host "EXE: $ProjectRoot\dist\Manualtech.exe"
Write-Host "Instalador: $InstallerPath"
Write-Host "ZIP comercial: $ZipPath"
Write-Host "Revisa release\Manualtech_${Version}_Beta_MSL.zip antes de distribuir."
