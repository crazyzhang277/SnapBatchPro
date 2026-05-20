# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['SnapBatch.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/首页.png', 'assets')],
    hiddenimports=['numpy'],  # 强制保证 numpy 导入正常
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 💡 修正：移除了 'urllib', 'http', 'xml', 'email'，只保留绝对安全的排除项
    excludes=[
        'PySide6.QtNetwork', 'PySide6.QtQml', 'PySide6.QtSql', 'PySide6.QtXml',
        'PySide6.QtMultimedia', 'PySide6.QtCharts', 'PySide6.QtSpatialAudio',
        'PySide6.QtWebEngineCore', 'PySide6.Qt3DCore', 'PySide6.QtQuick',
        'unittest', 'pydoc', 'tkinter'
    ],
    noarchive=False,
    optimize=2,
)

# 💡 核心控体：清理真正占地方的 Qt 无用图片插件（立减数十 MB）
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

# 仅保留中文语言包
def filter_translations(toc):
    return [x for x in toc if not ('qttranslations' in x[1].lower() and 'qt_zh_CN' not in x[0])]

a.datas = filter_translations(a.datas)
a.binaries = filter_translations(a.binaries)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SnapBatch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,      # 保持 UPX 压缩开启
    icon=['app.ico'],
    # 核心守卫：防止系统 DLL 损坏
    upx_exclude=[
        'api-ms-win-core-*.dll',
        'api-ms-win-crt-*.dll',
        'vcruntime140.dll',
        'vcruntime140_1.dll',
        'msvcp140.dll',
        'ucrtbase.dll',
        'python3.dll'
    ],
    runtime_tmpdir=None,
    console=False, # 关闭黑窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)