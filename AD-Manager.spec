# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for AD Manager (standalone Windows exe).

Build with:
    pyinstaller AD-Manager.spec --noconfirm --clean

Produces a one-folder build: dist/AD-Manager/AD-Manager.exe
(Folder build starts faster and is less flag-prone than one-file;
zip or copy the whole folder for distribution.)
"""
from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'ldap3',
        *collect_submodules('ldap3'),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Nothing in this app uses these; shrinks the bundle.
        'tkinter',
        'unittest',
        'pydoc_data',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AD-Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # windowed GUI app — no console flash
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
    upx=False,
    name='AD-Manager',
)
