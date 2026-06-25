# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VSVersionInfo,
    VarFileInfo,
    VarStruct,
)

block_cipher = None
project_root = Path(SPECPATH).resolve()


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
datas += collect_tree(project_root / "App_TestData" / "assets", "App_TestData/assets")
datas += collect_tree(project_root / "components" / "assets", "components/assets")

hiddenimports = [
    "App_TestData",
    "App_Organigrama",
    "App_Directorio",
    "fitz",
    "PIL.Image",
    "PIL.ImageTk",
]

version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 1, 0, 0),
        prodvers=(1, 1, 0, 0),
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040904B0",
                    [
                        StringStruct("CompanyName", "Municipio de Fresnillo"),
                        StringStruct("FileDescription", "Suite Digital Fresnillo"),
                        StringStruct("FileVersion", "1.1.0"),
                        StringStruct("InternalName", "SuiteFresnillo"),
                        StringStruct("OriginalFilename", "SuiteFresnillo.exe"),
                        StringStruct("ProductName", "Suite Digital Fresnillo"),
                        StringStruct("ProductVersion", "1.1.0"),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [1033, 1200])]),
    ],
)

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(project_root / "hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "components" / "assets" / "SuiteIcon.ico"),
    version=version_info,
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
