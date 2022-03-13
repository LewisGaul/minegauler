# -*- mode: python ; coding: utf-8 -*-

import os.path
import pathlib

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_data_files


block_cipher = None


_PROJECT_NAME = "minegauler"
_PROJECT_DIR = pathlib.Path.cwd() / "src"
_PROJECT_ROOT = _PROJECT_DIR / _PROJECT_NAME
_ICON_PATH = _PROJECT_ROOT / "app/images/icon.ico"


_APP_DATA = [
    (x[0], os.path.relpath(x[1], start=_PROJECT_NAME))
    for x in collect_data_files(
        _PROJECT_NAME,
        subdir="app",
        includes=("images/", "files/", "boards/sample.mgb"),
    )
]
_APP_DATA += collect_data_files("zig_minesolver")


app_analysis = Analysis(
    [".pyinstaller_main.py"],
    pathex=[],
    binaries=[],
    datas=_APP_DATA,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
app_pyz = PYZ(app_analysis.pure, app_analysis.zipped_data, cipher=block_cipher)
app_exe = EXE(
    app_pyz,
    app_analysis.scripts,
    [],
    exclude_binaries=True,
    name=_PROJECT_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(_ICON_PATH),
)

bot_analysis = Analysis(
    [".pyinstaller_bot.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
bot_pyz = PYZ(bot_analysis.pure, bot_analysis.zipped_data, cipher=block_cipher)
bot_exe = EXE(
    bot_pyz,
    bot_analysis.scripts,
    [],
    exclude_binaries=True,
    name=f"{_PROJECT_NAME}-bot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=str(_ICON_PATH),
)

coll = COLLECT(
    app_exe,
    app_analysis.binaries,
    app_analysis.zipfiles,
    app_analysis.datas,
    bot_exe,
    bot_analysis.binaries,
    bot_analysis.zipfiles,
    bot_analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=_PROJECT_NAME,
)
