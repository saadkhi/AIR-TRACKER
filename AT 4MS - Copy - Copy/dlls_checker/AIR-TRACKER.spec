# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('media', 'media')]
datas += collect_data_files('mediapipe')
datas += collect_data_files('cvzone')
datas += collect_data_files('comtypes')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('C:\\Windows\\System32\\msvcp140.dll', '.'), ('C:\\Windows\\System32\\msvcp140_1.dll', '.'), ('C:\\Windows\\System32\\msvcp140_2.dll', '.'), ('C:\\Windows\\System32\\vcruntime140.dll', '.'), ('C:\\Windows\\System32\\vcruntime140_1.dll', '.')],
    datas=datas,
    hiddenimports=['cv2', 'cv2.data', 'mediapipe', 'cvzone.HandTrackingModule', 'PIL', 'PIL.Image', 'PIL.ImageTk', 'numpy', 'pyautogui', 'comtypes', 'comtypes.client', 'comtypes.gen', 'comtypes.client._code_cache', 'customtkinter', 'tkinter', 'tkinter.messagebox', 'win32gui', 'win32con', 'pynput', 'pynput.mouse', 'tensorflow', 'tensorflow.python', 'tensorflow.python.platform'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AIR-TRACKER',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AIR-TRACKER',
)
