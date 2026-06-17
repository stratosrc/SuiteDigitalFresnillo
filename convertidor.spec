# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


block_cipher = None
project_root = Path.cwd()


def collect_tree(source: Path, destination: str):
    if not source.exists():
        return []
    files = []
    for path in source.rglob("*"):
        if path.is_file():
            files.append((str(path), str(Path(destination) / path.relative_to(source).parent)))
    return files


libreoffice_source = project_root / "App_ConversorPDF" / "vendor" / "LibreOffice"
if not libreoffice_source.exists():
    libreoffice_source = project_root / "App_ConversorPDF" / "vendor" / "libreoffice"

datas = []
datas += collect_tree(libreoffice_source, "vendor/libreoffice")
datas += collect_tree(project_root / "App_ConversorPDF" / "assets", "App_ConversorPDF/assets")
datas += collect_tree(project_root / "App_ConversorPDF" / "vendor" / "python", "App_ConversorPDF/vendor/python")
datas += collect_tree(project_root / "App_Directorio" / "assets", "App_Directorio/assets")
datas += collect_tree(project_root / "App_Organigrama" / "assets", "App_Organigrama/assets")
datas += collect_tree(project_root / "App_TestData" / "assets", "App_TestData/assets")
datas += collect_tree(project_root / "components" / "assets", "components/assets")

hiddenimports = [
    "App_TestData",
    "App_Organigrama",
    "App_Directorio",
    "App_ConversorPDF",
    "tkinterdnd2",
    "fitz",
    "PIL.Image",
    "PIL.ImageTk",
]

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
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
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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
