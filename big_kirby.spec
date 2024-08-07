# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['big_kirby.py'],
    pathex=['.'],
    binaries=[],
    datas=[('y3il.gif', '.'), ('y3il-reverse.gif', '.'), ('strberry.gif', '.')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='big_kirby',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='big_kirby',
)
app = BUNDLE(
    coll,
    name='big_kirby.app',
    icon=None,
    bundle_identifier=None,
)
