# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['SnapBatch.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/首页.png', 'assets')],
    hiddenimports=['numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtNetwork', 'PySide6.QtQml', 'PySide6.QtSql', 'PySide6.QtXml',
        'PySide6.QtMultimedia', 'PySide6.QtCharts', 'PySide6.QtSpatialAudio',
        'PySide6.QtWebEngineCore', 'PySide6.Qt3DCore', 'PySide6.QtQuick',
        'unittest', 'pydoc', 'tkinter'
    ],
    noarchive=False,
    optimize=2,
)

discard_qt_keywords = {
    'network', 'qml', 'quick', 'sql', 'xml', 'multimedia',
    'charts', 'spatialaudio', 'webengine', '3d', 'opengl',
    'virtualkeyboard', 'positioning', 'pdf', 'designer', 'assistant',
    'qgif', 'qjpeg', 'qwebp', 'qsvg', 'qico', 'tls', 'networkinformation'
}

a.binaries = [
    item for item in a.binaries
    if not any(qt_mod in item[0].lower() or qt_mod in item[1].lower() for qt_mod in discard_qt_keywords)
]

def filter_translations(toc):
    return [x for x in toc if not ('qttranslations' in x[1].lower() and 'qt_zh_CN' not in x[0])]

a.datas = filter_translations(a.datas)
a.binaries = filter_translations(a.binaries)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SnapBatch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    icon=['app.ico'],
    console=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        'api-ms-win-core-*.dll',
        'api-ms-win-crt-*.dll',
        'vcruntime140.dll',
        'vcruntime140_1.dll',
        'msvcp140.dll',
        'ucrtbase.dll',
        'python3.dll'
    ],
    name='SnapBatch'
)
