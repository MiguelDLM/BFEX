# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import gmsh

# get the location of the gmsh shared library which sits in venv/Lib
libname = 'libgmsh.so.4.11'  # Cambia esto si el nombre de la biblioteca compartida es diferente
libpath = Path('myenv/lib') / libname
print('Adding {} to binaries'.format(libpath))

block_cipher = None

a = Analysis(
    ['Convert_to_csv.py'],  # Script de conversión
    pathex=['.'],
    binaries=[(str(libpath), '.')],  # Añadir la biblioteca compartida de gmsh a los binarios
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
    excludes=['PySide2', 'PyQt5', 'trame'],  # Excluir bindings de Qt no necesarios y trame
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
    upx=False,  # Cambiado a False para evitar problemas con UPX en Linux
    upx_exclude=[],
    name='Convert_to_csv',
    debug=True,
    bootloader_ignore_signals=False,
    console=True,
)
