# -*- mode: python -*-

block_cipher = None


included_files = [('images/', 'images/')]

a = Analysis(['src\\main.py'],
             pathex=['C:\\Users\\User\\SkyDrive\\Documents\\Python\\minegaulerQt'],
             binaries=[],
             datas=included_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='MineGauler',
          debug=False,
          strip=False,
          upx=True,
          console=False, icon='images\\icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='MineGauler')
