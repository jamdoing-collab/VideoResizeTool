# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Video Resize Processor Windows executable
"""

import os
import sys

block_cipher = None

# Get FFmpeg binaries
binaries = []
if sys.platform == 'win32' or os.path.exists('ffmpeg.exe'):
    if os.path.exists('ffmpeg.exe'):
        binaries.append(('ffmpeg.exe', '.'))
    if os.path.exists('ffprobe.exe'):
        binaries.append(('ffprobe.exe', '.'))

a = Analysis(
    ['video_resize_gui.py'],
    pathex=[],
    binaries=binaries,
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add hidden imports for PyQt6
a.hiddenimports += [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtSvg',
    'PyQt6.QtXml',
]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VideoResizeTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
