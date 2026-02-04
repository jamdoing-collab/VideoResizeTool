#!/usr/bin/env python3
"""
Setup script for packaging Video Resize Processor GUI with FFmpeg
Usage: 
    1. Copy ffmpeg and ffprobe to this directory
    2. python3 setup.py py2app
"""

from setuptools import setup
import os

# Check if ffmpeg exists in current directory
has_ffmpeg = os.path.exists('ffmpeg') and os.path.exists('ffprobe')

APP = ['video_resize_gui.py']

# Include ffmpeg binaries if they exist
DATA_FILES = []
if has_ffmpeg:
    DATA_FILES = ['ffmpeg', 'ffprobe']
    print("✓ Found ffmpeg and ffprobe, will bundle with app")
else:
    print("⚠ ffmpeg not found in current directory")
    print("  App will require users to install ffmpeg separately")

OPTIONS = {
    'argv_emulation': False,
    'packages': ['PyQt6'],
    'iconfile': 'icon.icns',
    'plist': {
        'CFBundleName': 'VideoResizeTool',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'CFBundleIdentifier': 'com.videoresize.app',
        'NSHumanReadableCopyright': '© 2025 Video Resize Processor',
    },
    'semi_standalone': False,
    'site_packages': True,
}

setup(
    app=APP,
    name='VideoResizeTool',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
