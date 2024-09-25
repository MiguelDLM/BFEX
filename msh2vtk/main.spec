# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],  # Script principal
    pathex=['.'],
    binaries=[],  # No se necesitan binarios adicionales
    datas=[],
    hiddenimports=[
        'os',
        'sys',
        'tkinter',
        'customtkinter',
        'queue',
        'threading',
        'subprocess',
    ],
    hookspath=['./hooks'],  # Añadir el directorio de hooks si es necesario
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
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)