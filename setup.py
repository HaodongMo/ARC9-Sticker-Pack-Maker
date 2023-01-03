import cx_Freeze

packages = ['PyQt5.QtWidgets', 'VTFLibWrapper.VTFLib', 'VTFLibWrapper.VTFLibEnums', 'PIL', 'numpy', 'ctypes']
include_files = []

executables = [cx_Freeze.Executable("main.py")]

cx_Freeze.setup(
    name="makestickers",
    options={'build_exe': {'packages': packages, 'include_files': include_files}},
    executables=executables
)