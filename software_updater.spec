a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Software Updater',
    debug=False,
    strip=False,
    runtime_tmpdir=None,
)
