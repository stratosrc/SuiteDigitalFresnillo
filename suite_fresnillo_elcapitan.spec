# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None
project_root = Path(SPECPATH).resolve()
is_windows = sys.platform.startswith("win")
is_macos = sys.platform == "darwin"
macos_minimum_version = "10.11"

if is_macos:
    # El Capitan's codesign cannot handle PyInstaller's modern signature-removal flags.
    import PyInstaller.utils.osx as osxutils

    osxutils.remove_signature_from_binary = lambda *args, **kwargs: None
    osxutils.sign_binary = lambda *args, **kwargs: None


def collect_tree(source: Path, destination: str):
    if not source.exists():
        return []
    files = []
    for path in source.rglob("*"):
        if path.is_file():
            files.append((str(path), str(Path(destination) / path.relative_to(source).parent)))
    return files


datas = []
datas += collect_tree(project_root / "App_Directorio" / "assets", "App_Directorio/assets")
datas += collect_tree(project_root / "App_Organigrama" / "assets", "App_Organigrama/assets")
datas += collect_tree(project_root / "components" / "assets", "components/assets")

hiddenimports = [
    "App_Organigrama",
    "App_Directorio",
    "PIL.Image",
    "PIL.ImageTk",
]

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / "hooks" / "legacy_mac_runtime.py")],
    excludes=[
        "App_TestData",
        "fitz",
        "pymupdf",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SuiteFresnillo",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=is_macos,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "components" / "assets" / "SuiteIcon.ico") if is_windows else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SuiteFresnillo",
)

if is_macos:
    app = BUNDLE(
        coll,
        name="SuiteFresnillo.app",
        icon=None,
        bundle_identifier="mx.gob.fresnillo.suitedigital.legacy",
        info_plist={
            "CFBundleDisplayName": "Suite Digital Fresnillo",
            "CFBundleName": "SuiteFresnillo",
            "CFBundleShortVersionString": "1.1.0",
            "CFBundleVersion": "1.1.0",
            "LSMinimumSystemVersion": macos_minimum_version,
            "NSHighResolutionCapable": "True",
        },
    )
