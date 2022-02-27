# -*- mode: python ; coding: utf-8 -*-

import pathlib


block_cipher = None


_PROJECT_NAME = "minegauler"
_EXE_NAME = "minegauler-bot"
_PROJECT_PATH = pathlib.Path("..") / _PROJECT_NAME


a = Analysis(
    [".pyinstaller_bot.py"],
    pathex=[str(_PROJECT_PATH)],
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
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=_EXE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(_PROJECT_PATH / "app/images/icon.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=_EXE_NAME,
)
