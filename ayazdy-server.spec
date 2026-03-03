# -*- mode: python ; coding: utf-8 -*-
# AyazDy Server - PyInstaller Spec File
# For advanced build customization

block_cipher = None

# Analysis: Find all imports and dependencies
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('dashboard', 'dashboard'),
        ('plugins', 'plugins'),
        ('.env.example', '.'),
        ('README.md', '.'),
        ('QUICK_REFERENCE.md', '.'),
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'httpx',
        'pydantic',
        'telegram',
        'telegram.ext',
        'yaml',
        'json',
        'sqlite3',
        'asyncio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',  # Not needed for server
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ: Compress Python modules
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE: Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AyazDy-Server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show console for server
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
