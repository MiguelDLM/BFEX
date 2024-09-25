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
    hookspath=[],  # No hooks adicionales
    runtime_hooks=[],  # No runtime hooks adicionales
    excludes=[],  # No exclusiones específicas
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
    upx=False,  # Deshabilitar UPX para evitar problemas en Linux
    upx_exclude=[],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    console=True,
)
