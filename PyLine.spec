# -*- mode: python ; coding: utf-8 -*-
"""PyLine PyInstaller spec — Linux 版：单文件、无终端、最小体积"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# ── 项目根目录 ──
ROOT = Path(SPECPATH)

# ── 图标文件（预留，放置后自动使用） ──
ICON_FILE = ROOT / "assets" / "icon.ico"
icon_path = str(ICON_FILE) if ICON_FILE.exists() else None

# ── 需要排除的 PySide6 / Qt 模块（项目仅用 QtCore, QtGui, QtWidgets, QtSvg, QtXml, QtNetwork） ──
_QT_EXCLUDES = [
    "PySide6.Qt3DAnimation", "PySide6.Qt3DCore", "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput", "PySide6.Qt3DLogic", "PySide6.Qt3DRender",
    "PySide6.QtBluetooth",
    "PySide6.QtCharts", "PySide6.QtChartsQml",
    "PySide6.QtConcurrent",
    "PySide6.QtDataVisualization",
    "PySide6.QtDBus",
    "PySide6.QtDesigner",
    "PySide6.QtGraphs", "PySide6.QtGraphsWidgets",
    "PySide6.QtHelp",
    "PySide6.QtHttpServer",
    "PySide6.QtLocation",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets",
    "PySide6.QtNetworkAuth",
    "PySide6.QtNfc",
    "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets",
    "PySide6.QtPdf", "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning",
    "PySide6.QtPrintSupport",
    "PySide6.QtQml", "PySide6.QtQmlCore", "PySide6.QtQmlModels",
    "PySide6.QtQuick", "PySide6.QtQuickControls2", "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtSensors",
    "PySide6.QtSerialBus", "PySide6.QtSerialPort",
    "PySide6.QtShaderTools",
    "PySide6.QtSpatialAudio",
    "PySide6.QtSql",
    "PySide6.QtStateMachine",
    "PySide6.QtTest",
    "PySide6.QtTextToSpeech",
    "PySide6.QtUiTools",
    "PySide6.QtVirtualKeyboard",
    "PySide6.QtWebChannel", "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick", "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets", "PySide6.QtWebView",
]

# ── 其他不需要的模块 ──
_OTHER_EXCLUDES = [
    "tkinter", "_tkinter",
    "unittest", "test",
    "xmlrpc", "pydoc",
    # matplotlib 不需要的后端和测试
    "matplotlib.tests", "mpl_toolkits.tests",
    "matplotlib.backends.backend_cairo",
    "matplotlib.backends.backend_gtk3",
    "matplotlib.backends.backend_gtk3agg",
    "matplotlib.backends.backend_gtk4",
    "matplotlib.backends.backend_gtk4agg",
    "matplotlib.backends.backend_macosx",
    "matplotlib.backends.backend_nbagg",
    "matplotlib.backends.backend_pdf",
    "matplotlib.backends.backend_pgf",
    "matplotlib.backends.backend_ps",
    "matplotlib.backends.backend_svg",
    "matplotlib.backends.backend_tkagg",
    "matplotlib.backends.backend_tk",
    "matplotlib.backends.backend_webagg",
    "matplotlib.backends.backend_webagg_core",
    "matplotlib.backends.backend_wx",
    "matplotlib.backends.backend_wxagg",
    # PIL 不需要的插件
    "PIL.ImageTk",
]

EXCLUDES = _QT_EXCLUDES + _OTHER_EXCLUDES

# ── 隐式导入（PyInstaller 可能漏掉的） ──
hiddenimports = [
    "qfluentwidgets",
    *collect_submodules("qfluentwidgets"),
    "cv2",
    "numpy",
    "openpyxl",
    "pydantic",
    "matplotlib.backends.backend_qtagg",
]

# ── Analysis ──
a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    cipher=block_cipher,
)

# ── 进一步裁剪二进制文件 ──
import re

# Qt 动态库黑名单前缀（Linux: libQt6*.so, Windows: Qt6*.dll）
_QT_LIB_STRIP = (
    "libQt63D", "libQt6Bluetooth", "libQt6Charts", "libQt6Concurrent",
    "libQt6DataVisualization", "libQt6Designer", "libQt6Graphs",
    "libQt6Help", "libQt6HttpServer", "libQt6Labs", "libQt6Location",
    "libQt6Multimedia", "libQt6Nfc", "libQt6Pdf", "libQt6Positioning",
    "libQt6Quick", "libQt6Qml", "libQt6RemoteObjects", "libQt6Scxml",
    "libQt6Sensors", "libQt6SerialBus", "libQt6SerialPort",
    "libQt6ShaderTools", "libQt6SpatialAudio", "libQt6Sql",
    "libQt6StateMachine", "libQt6Test", "libQt6TextToSpeech",
    "libQt6UiTools", "libQt6VirtualKeyboard", "libQt6Wayland",
    "libQt6WebChannel", "libQt6WebEngine", "libQt6WebSockets",
    "libQt6WebView",
)

# OpenCV headless 中不需要的视频编解码 / FFmpeg 库
_CV_LIB_STRIP_RE = re.compile(
    r"lib(avcodec|avformat|avfilter|avdevice|swresample|swscale|avutil|"
    r"aom|vpx|x264|x265|openh264|dav1d)-"
)

def _keep_binary(name):
    if any(name.startswith(p) for p in _QT_LIB_STRIP):
        return False
    if _CV_LIB_STRIP_RE.search(name):
        return False
    return True

a.binaries = [b for b in a.binaries if _keep_binary(b[0])]

# 移除 Qt 翻译文件 + matplotlib 样本数据 + matplotlib 测试数据
a.datas = [
    d for d in a.datas
    if not d[0].startswith("PySide6/Qt/translations")
    and not d[0].startswith("matplotlib/mpl-data/sample_data")
    and "/tests/" not in d[0]
]

# ── PYZ (压缩 Python 字节码) ──
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── EXE ──
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PyLine",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,          # strip 二进制符号
    upx=True,            # 启用 UPX 压缩（如果系统安装了 UPX）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # 无终端
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
