# -*- mode: python ; coding: utf-8 -*-

import pathlib
from typing import List, Tuple


block_cipher = None


_PROJECT_NAME = "minegauler"
_PROJECT_PATH = pathlib.Path("..") / _PROJECT_NAME


def _get_data() -> List[Tuple[str, str]]:
    dirs = ["images", "files"]
    files = ["boards/sample.mgb"]
    return [
        *[(str(_PROJECT_PATH / d), str(pathlib.Path(d))) for d in dirs],
        *[(str(_PROJECT_PATH / f), str(pathlib.Path(f).parent)) for f in files],
    ]


a = Analysis(
    [".pyinstaller_main.py"],
    pathex=[str(_PROJECT_PATH)],
    binaries=[],
    datas=_get_data(),
    hiddenimports=[],
    hookspath=[],
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
    name=_PROJECT_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(_PROJECT_PATH / "images" / "icon.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=_PROJECT_NAME,
)
