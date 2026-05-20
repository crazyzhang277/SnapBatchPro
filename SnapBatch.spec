# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['.venv/SnapBatch.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/首页.png', 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 基础排除
    excludes=[
        'PySide6.QtNetwork', 'PySide6.QtQml', 'PySide6.QtSql', 'PySide6.QtXml',
        'PySide6.QtMultimedia', 'PySide6.QtCharts', 'PySide6.QtSpatialAudio',
        'PySide6.QtWebEngineCore', 'PySide6.Qt3DCore', 'PySide6.QtQuick'
    ],
    noarchive=False,
    optimize=2,
)

# 💡 1. 修正后的 Qt6 垃圾模块绝对拦截词（去掉了‘qt’，直接精准切除带数字6的组件）
discard_qt_keywords = {
    'network', 'qml', 'quick', 'sql', 'xml', 'multimedia',
    'charts', 'spatialaudio', 'webengine', '3d', 'opengl',
    'virtualkeyboard', 'positioning', 'pdf', 'designer', 'assistant'
}

# 💡 2. 修正后的 NumPy 2.x 数学加速库绝对拦截词（直接用 openblas 斩断 libscipy_openblas）
discard_math_keywords = {'openblas', 'mkl', 'tbb', 'quadmath'}

a.binaries = [
    item for item in a.binaries
    if not any(qt_mod in item[0].lower() or qt_mod in item[1].lower() for qt_mod in discard_qt_keywords)
    and not any(math_mod in item[0].lower() or math_mod in item[1].lower() for math_mod in discard_math_keywords)
]

# 3. 自动过滤 Qt 多国语言包
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
    upx=True,
    icon=['.venv/app.ico'],
    # 4. 排除无法压缩的系统核心 DLL
    upx_exclude=[
        'api-ms-win-core-*.dll',
        'api-ms-win-crt-*.dll',
        'vcruntime140.dll',
        'vcruntime140_1.dll',
        'msvcp140.dll',
        'ucrtbase.dll',
        'python3.dll'  # 排除掉你日志里报错的 python3.dll
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)