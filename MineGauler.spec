# -*- mode: python -*-

import platform


block_cipher = None

included_files = [('images/icon.ico', 'images/')]
for folder in ['buttons', 'faces', 'markers', 'numbers']:
    path = 'images/' + folder
    included_files.append((path, path))


if platform.system() == 'Windows':
    base_direc = 'C:\\Users\\User\\Dropbox\\MineGauler\\minegaulerQt'
elif platform.system() == 'Darwin':
    base_direc = '/Users/lewisgaul/Dropbox/MineGauler/minegaulerQt'
elif platform.system() == 'Linux':
  base_direc = '/home/lewis/Dropbox/MineGauler/minegaulerQt'

a = Analysis(['src/main.py'],
             pathex=[base_direc],
             binaries=[],
             datas=included_files,
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
          name='MineGauler',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='images/icon.ico') #icon arg may give error on mac?
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='MineGauler')
