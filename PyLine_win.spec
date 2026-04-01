# -*- mode: python ; coding: utf-8 -*-
"""PyLine PyInstaller spec — Windows 版：单文件、无终端、最小体积"""

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

# Qt 动态库黑名单（Windows: Qt6*.dll / *d.dll）
_QT_DLL_STRIP = (
    "Qt63D", "Qt6Bluetooth", "Qt6Charts", "Qt6Concurrent",
    "Qt6DataVisualization", "Qt6Designer", "Qt6Graphs",
    "Qt6Help", "Qt6HttpServer", "Qt6Labs", "Qt6Location",
    "Qt6Multimedia", "Qt6Nfc", "Qt6Pdf", "Qt6Positioning",
    "Qt6Quick", "Qt6Qml", "Qt6RemoteObjects", "Qt6Scxml",
    "Qt6Sensors", "Qt6SerialBus", "Qt6SerialPort",
    "Qt6ShaderTools", "Qt6SpatialAudio", "Qt6Sql",
    "Qt6StateMachine", "Qt6Test", "Qt6TextToSpeech",
    "Qt6UiTools", "Qt6VirtualKeyboard",
    "Qt6WebChannel", "Qt6WebEngine", "Qt6WebSockets",
    "Qt6WebView",
)

# OpenCV headless 中不需要的视频编解码库（Windows .dll 命名）
_CV_DLL_STRIP_RE = re.compile(
    r"(opencv_videoio|avcodec|avformat|avfilter|avdevice|"
    r"swresample|swscale|avutil|aom|vpx|x264|x265|openh264|dav1d)",
    re.IGNORECASE,
)

def _keep_binary(name):
    base = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    # Qt DLL 过滤
    if any(base.startswith(p) for p in _QT_DLL_STRIP):
        return False
    # 兼容 Linux libQt6* 命名（spec 可在 WSL 下使用）
    if any(base.startswith("lib" + p) for p in _QT_DLL_STRIP):
        return False
    # FFmpeg / 视频编解码
    if _CV_DLL_STRIP_RE.search(base):
        return False
    return True

a.binaries = [b for b in a.binaries if _keep_binary(b[0])]

# 移除 Qt 翻译文件 + matplotlib 样本数据 + 测试数据
a.datas = [
    d for d in a.datas
    if not d[0].startswith("PySide6/Qt/translations")
    and not d[0].startswith("PySide6\\Qt\\translations")
    and not d[0].startswith("matplotlib/mpl-data/sample_data")
    and not d[0].startswith("matplotlib\\mpl-data\\sample_data")
    and "/tests/" not in d[0]
    and "\\tests\\" not in d[0]
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
    strip=False,         # Windows 下不使用 strip
    upx=True,            # 启用 UPX 压缩（需系统安装 UPX 并加入 PATH）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # 无终端（windowed 模式）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
