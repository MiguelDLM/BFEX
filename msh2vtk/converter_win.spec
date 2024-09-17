# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import gmsh

# get the location of the gmsh dll which sits in venv/Lib
libname = 'gmsh-4.13.dll'  # Cambia esto si el nombre del DLL es diferente
libpath = Path('venv/Lib') / libname
print('Adding {} to binaries'.format(libpath))

block_cipher = None

a = Analysis(
    ['Convert_to_csv.py'],  # Script de conversión
    pathex=['.'],
    binaries=[(str(libpath), '.')],  # Añadir el DLL de gmsh a los binarios
    datas=[],
    hiddenimports=[
        'os',
        'sys',
        'numpy',
        'pandas',
        'gmsh',
        'json',
        'pyvista',
        'argparse',
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
    name='Convert_to_csv',
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
    name='Convert_to_csv',
)