$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
$Version = "1.0.0"

Write-Host "== Manualtech open-source build =="
Write-Host "Project: $ProjectRoot"
Write-Host "Version: $Version"

Write-Host "Limpiando builds anteriores..."
foreach ($DirName in @("build", "dist", "installer_output", "release")) {
    $DirPath = Join-Path $ProjectRoot $DirName
    if (Test-Path $DirPath) {
        if ($DirName -eq "release") {
            Get-ChildItem -LiteralPath $DirPath -Force | Remove-Item -Recurse -Force
        }
        else {
            Remove-Item -LiteralPath $DirPath -Recurse -Force
        }
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
$PackageDir = Join-Path $ReleaseDir "Manualtech_${Version}"
$ZipPath = Join-Path $ReleaseDir "Manualtech_${Version}_Windows.zip"

if (-not (Test-Path $InstallerPath)) {
    throw "No se encontró el instalador esperado: $InstallerPath"
}

New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null
New-Item -ItemType Directory -Path $PackageDir -Force | Out-Null

Copy-Item -LiteralPath $InstallerPath -Destination (Join-Path $PackageDir "Manualtech_${Version}_Setup.exe") -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "LICENSE.txt") -Destination $PackageDir -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "THIRD_PARTY_NOTICES.md") -Destination $PackageDir -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "README.md") -Destination $PackageDir -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "SOURCE_CODE.md") -Destination $PackageDir -Force

Write-Host "Creando ZIP de distribución..."
Compress-Archive -Path (Join-Path $PackageDir "*") -DestinationPath $ZipPath -Force

$AllowedEntries = @(
    "Manualtech_${Version}_Setup.exe",
    "LICENSE.txt",
    "THIRD_PARTY_NOTICES.md",
    "README.md",
    "SOURCE_CODE.md"
)

Add-Type -AssemblyName System.IO.Compression.FileSystem
Write-Host "Verificando paquete..."
$Archive = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
try {
    foreach ($Entry in $Archive.Entries) {
        $EntryName = $Entry.FullName.Replace("\", "/")
        if ($AllowedEntries -notcontains $EntryName) {
            throw "El ZIP contiene un archivo no previsto para distribución: $EntryName"
        }
        if ($EntryName.EndsWith(".pdf", [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "El ZIP contiene un PDF no previsto: $EntryName"
        }
        if ($EntryName.EndsWith(".db", [System.StringComparison]::OrdinalIgnoreCase) -or
            $EntryName.EndsWith(".sqlite", [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "El ZIP contiene una base de datos no prevista: $EntryName"
        }
    }
}
finally {
    $Archive.Dispose()
}

Write-Host "Release open source generado correctamente."
Write-Host "EXE: $ProjectRoot\dist\Manualtech.exe"
Write-Host "Instalador: $InstallerPath"
Write-Host "ZIP: $ZipPath"
Write-Host "Código fuente: https://github.com/Javier14051992/Manualtech"
