# -*- mode: python -*-

import platform


block_cipher = None

if platform.system() == 'Windows':
    base_direc = 'C:\\Users\\User\\Dropbox\\MineGauler\\minegaulerQt'
elif platform.system() == 'Darwin':
    base_direc = '/Users/lewisgaul/Dropbox/MineGauler/minegaulerQt'
block_cipher = None

a = Analysis(['src/cli_entry.py'],
             pathex=[base_direc],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='MineGaulerCLI',
          debug=False,
          strip=False,
          upx=True,
          console=True,
          icon='images/icon.ico') #Error on mac?
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='MineGauler')
