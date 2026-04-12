# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable,
    StringStruct, VarFileInfo, VarStruct
)

version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 4, 0, 0),
        prodvers=(1, 4, 0, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo([
            StringTable(u'040904B0', [
                StringStruct(u'FileDescription',  u'FantasySF6 Fantasy League App'),
                StringStruct(u'FileVersion',      u'1.4.0'),
                StringStruct(u'InternalName',     u'FantasySF6'),
                StringStruct(u'LegalCopyright',   u'Copyright (C) 2026'),
                StringStruct(u'OriginalFilename', u'FantasySF6.exe'),
                StringStruct(u'ProductName',      u'FantasySF6'),
                StringStruct(u'ProductVersion',   u'1.4.0'),
            ])
        ]),
        VarFileInfo([VarStruct(u'Translation', [0x0409, 1200])])
    ]
)


a = Analysis(
    ['app\\main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/client/assets/fonts',   'app/client/assets/fonts.'),
        ('app/client/assets/icons',   'app/client/assets/icons.'),
        ('app/client/assets/images',  'app/client/assets/images.'),
        ('app/client/assets/players', 'app/client/assets/players.'),
        ('app/client/assets/sounds',  'app/client/assets/sounds.'),
        ('app/client/assets/texts',   'app/client/assets/texts.')
    ],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='FantasySF6',
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
    icon='app/client/assets/icons/logo.ico',
    version=version_info,
)
