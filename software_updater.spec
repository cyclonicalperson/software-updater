# gui.spec

# Import necessary modules
from PyInstaller.utils.hooks import collect_data_files
import os

# Analysis of your main script
a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[('gui_styles.qss', '.')],  # Adding the QSS file
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[]
)

# Create the PYZ archive
pyz = PYZ(a.pure, a.zipped_data)

# Define the EXE with additional options
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Software Updater',
    icon='icon.ico',
    debug=False,
    strip=False,
    upx=True,  # Enabling UPX compression
    runtime_tmpdir=None,
    console=False,  # Equivalent to --noconsole
    uac_admin=False,  # Optional, for Windows if you need admin rights
    onefile=True,  # Equivalent to --onefile
)

# Add UPX compression directory
exe.upx_dir = "ups-5.0.0-win64"  # Path to UPX directory
