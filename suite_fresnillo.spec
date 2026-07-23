# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None
project_root = Path(SPECPATH).resolve()
is_windows = sys.platform.startswith("win")
is_macos = sys.platform == "darwin"
macos_minimum_version = "13.0"


def collect_tree(source: Path, destination: str):
    if not source.exists():
        return []
    files = []
    for path in source.rglob("*"):
        if "__MACOSX" in path.parts:
            continue
        if path.is_file():
            files.append((str(path), str(Path(destination) / path.relative_to(source).parent)))
    return files


def repair_framework_symlink(link_path: Path, expected_target: str) -> None:
    if link_path.is_symlink():
        return
    if not link_path.exists() or not link_path.is_file():
        return

    current_target = link_path.read_text(encoding="utf-8", errors="ignore").strip()
    if current_target != expected_target:
        return

    link_path.unlink()
    os.symlink(expected_target, link_path)


def repair_libreoffice_python_framework(project_root: Path) -> None:
    framework_root = (
        project_root
        / "App_ConversorPDF"
        / "vendor"
        / "LibreOffice"
        / "Contents"
        / "Frameworks"
        / "LibreOfficePython.framework"
    )
    if not framework_root.exists():
        return

    repair_framework_symlink(framework_root / "Versions" / "Current", "3.12")
    repair_framework_symlink(framework_root / "Headers", "Versions/Current/Headers")
    repair_framework_symlink(framework_root / "Resources", "Versions/Current/Resources")
    repair_framework_symlink(
        framework_root / "LibreOfficePython",
        "Versions/Current/LibreOfficePython",
    )

hiddenimports = [
    "App_ConversorPDF",
    "App_TestData",
    "App_Organigrama",
    "App_Directorio",
    "fitz",
    "PIL.Image",
    "PIL.ImageTk",
]

if is_macos:
    repair_libreoffice_python_framework(project_root)

datas = []
datas += collect_tree(project_root / "App_ConversorPDF" / "assets", "App_ConversorPDF/assets")
datas += collect_tree(project_root / "App_ConversorPDF" / "vendor", "App_ConversorPDF/vendor")
datas += collect_tree(project_root / "App_Directorio" / "assets", "App_Directorio/assets")
datas += collect_tree(project_root / "App_Organigrama" / "assets", "App_Organigrama/assets")
datas += collect_tree(project_root / "App_TestData" / "assets", "App_TestData/assets")
datas += collect_tree(project_root / "components" / "assets", "components/assets")

if is_macos:
    datas = [
        item
        for item in datas
        if "App_ConversorPDF/vendor/python" not in item[0].replace("\\", "/")
    ]

version_info = None
if is_windows:
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo,
        StringFileInfo,
        StringStruct,
        StringTable,
        VarFileInfo,
        VarStruct,
        VSVersionInfo,
    )

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
    pathex=[
        str(project_root),
        *([] if is_macos else [str(project_root / "App_ConversorPDF" / "vendor" / "python")]),
    ],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
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
    argv_emulation=is_macos,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "components" / "assets" / "SuiteIcon.ico") if is_windows else None,
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

if is_macos:
    app = BUNDLE(
        coll,
        name="SuiteFresnillo.app",
        icon=None,
        bundle_identifier="mx.gob.fresnillo.suitedigital",
        info_plist={
            "CFBundleDisplayName": "Suite Digital Fresnillo",
            "CFBundleName": "SuiteFresnillo",
            "CFBundleShortVersionString": "1.1.0",
            "CFBundleVersion": "1.1.0",
            "LSMinimumSystemVersion": macos_minimum_version,
            "NSHighResolutionCapable": "True",
        },
    )
