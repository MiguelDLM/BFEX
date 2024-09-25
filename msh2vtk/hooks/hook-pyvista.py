from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect data files and submodules for pyvista, excluding pyvista.trame
datas = collect_data_files('pyvista')
hiddenimports = collect_submodules('pyvista')
hiddenimports = [mod for mod in hiddenimports if not mod.startswith('pyvista.trame')]