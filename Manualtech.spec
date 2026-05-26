# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_dir = Path.cwd()
datas = [
    (str(project_dir / "assets"), "assets"),
    (str(project_dir / "data" / "tessdata"), "data/tessdata"),
    (str(project_dir / "LICENSE.txt"), "."),
    (str(project_dir / "EULA.txt"), "."),
    (str(project_dir / "THIRD_PARTY_NOTICES.md"), "."),
    (str(project_dir / "TERMS_OF_SALE.md"), "."),
    (str(project_dir / "PRIVACY_POLICY.md"), "."),
    (str(project_dir / "REFUND_POLICY.md"), "."),
]


a = Analysis(
    ["main.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Manualtech",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_dir / "assets" / "manualtech.ico"),
)
