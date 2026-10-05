# PyInstaller spec for Easy Macro Recorder.
# Build with:  pyinstaller EasyMacroRecorder.spec
#
# Deliberately NOT using UPX: UPX-packed executables are a very common
# antivirus heuristic trigger, and the size saving is not worth the flags.

block_cipher = None

a = Analysis(
    ['easy_macro_recorder.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pynput.keyboard._win32', 'pynput.mouse._win32'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['numpy', 'PIL', 'pytest', 'setuptools'],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='EasyMacroRecorder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    version='version_info.txt',
    icon=None,
)
