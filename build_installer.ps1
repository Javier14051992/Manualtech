$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "== Manualtech build =="
Write-Host "Project: $ProjectRoot"

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

Write-Host "Build completado."
Write-Host "EXE: $ProjectRoot\dist\Manualtech.exe"
Write-Host "Instalador: $ProjectRoot\installer_output\Manualtech_Setup.exe"
