# -*- mode: python ; coding: utf-8 -*-
"""PyLine PyInstaller spec — Linux 版：单文件、无终端
优先保证运行正确，仅移除确认无用的 Qt 模块来缩减体积。"""

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None
ROOT = Path(SPECPATH)

# ── 图标 ──
ICON_FILE = ROOT / "assets" / "icon.ico"
icon_path = str(ICON_FILE) if ICON_FILE.exists() else None

# ══════════════════════════════════════════════════════════════════════
# 排除列表：只排除【确认不需要】的 PySide6 子包
# 项目实际用到的 Qt 模块（不可排除）：
#   QtCore, QtGui, QtWidgets, QtSvg, QtSvgWidgets, QtXml,
#   QtNetwork, QtMultimedia, QtMultimediaWidgets  ← qfluentwidgets 依赖
# ══════════════════════════════════════════════════════════════════════
_QT_EXCLUDES = [
    # 3D
    "PySide6.Qt3DAnimation", "PySide6.Qt3DCore", "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput", "PySide6.Qt3DLogic", "PySide6.Qt3DRender",
    # 蓝牙 / NFC / 串口
    "PySide6.QtBluetooth", "PySide6.QtNfc",
    "PySide6.QtSerialBus", "PySide6.QtSerialPort",
    # 图表（项目用 matplotlib 而非 QtCharts）
    "PySide6.QtCharts", "PySide6.QtChartsQml",
    "PySide6.QtDataVisualization",
    "PySide6.QtGraphs", "PySide6.QtGraphsWidgets",
    # 设计器 / 测试
    "PySide6.QtDesigner", "PySide6.QtTest", "PySide6.QtUiTools",
    # HTTP / DB
    "PySide6.QtHttpServer", "PySide6.QtSql",
    # 定位 / 传感器
    "PySide6.QtLocation", "PySide6.QtPositioning", "PySide6.QtSensors",
    # OpenGL
    "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets",
    # PDF
    "PySide6.QtPdf", "PySide6.QtPdfWidgets",
    # QML / Quick（纯 Widgets 应用）
    "PySide6.QtQml", "PySide6.QtQmlCore", "PySide6.QtQmlModels",
    "PySide6.QtQuick", "PySide6.QtQuickControls2", "PySide6.QtQuickWidgets",
    # 远程对象 / 状态机
    "PySide6.QtRemoteObjects", "PySide6.QtScxml", "PySide6.QtStateMachine",
    # 着色器 / 空间音频
    "PySide6.QtShaderTools", "PySide6.QtSpatialAudio",
    # TTS / 虚拟键盘
    "PySide6.QtTextToSpeech", "PySide6.QtVirtualKeyboard",
    # Web 引擎
    "PySide6.QtWebChannel", "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick", "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets", "PySide6.QtWebView",
    # 打印
    "PySide6.QtPrintSupport",
    # 网络认证 / DBus / Concurrent / Help
    "PySide6.QtNetworkAuth", "PySide6.QtDBus",
    "PySide6.QtConcurrent", "PySide6.QtHelp",
]

_OTHER_EXCLUDES = [
    "tkinter", "_tkinter",
    "xmlrpc", "pydoc",
    # matplotlib 不需要的后端（只保留 backend_qtagg 和 backend_agg）
    "matplotlib.backends.backend_cairo",
    "matplotlib.backends.backend_gtk3", "matplotlib.backends.backend_gtk3agg",
    "matplotlib.backends.backend_gtk4", "matplotlib.backends.backend_gtk4agg",
    "matplotlib.backends.backend_macosx",
    "matplotlib.backends.backend_nbagg",
    "matplotlib.backends.backend_pdf",
    "matplotlib.backends.backend_pgf",
    "matplotlib.backends.backend_ps",
    "matplotlib.backends.backend_svg",
    "matplotlib.backends.backend_tkagg", "matplotlib.backends.backend_tk",
    "matplotlib.backends.backend_webagg", "matplotlib.backends.backend_webagg_core",
    "matplotlib.backends.backend_wx", "matplotlib.backends.backend_wxagg",
    # matplotlib 测试
    "matplotlib.tests", "mpl_toolkits.tests",
    # PIL
    "PIL.ImageTk",
]

EXCLUDES = _QT_EXCLUDES + _OTHER_EXCLUDES

# ══════════════════════════════════════════════════════════════════════
# 隐式导入：显式声明所有运行时需要的模块
# ══════════════════════════════════════════════════════════════════════
hiddenimports = [
    # ─ qfluentwidgets ─
    "qfluentwidgets",
    *collect_submodules("qfluentwidgets"),
    "qframelesswindow",
    *collect_submodules("qframelesswindow"),
    # ─ OpenCV ─
    "cv2",
    *collect_submodules("cv2"),
    # ─ numpy ─
    "numpy",
    # ─ openpyxl ─
    "openpyxl",
    *collect_submodules("openpyxl"),
    # ─ pydantic ─
    "pydantic", "pydantic_core",
    *collect_submodules("pydantic"),
    "typing_extensions", "typing_inspection",
    # ─ matplotlib ─
    "matplotlib", "matplotlib.pyplot", "matplotlib.figure",
    "matplotlib.axes", "matplotlib.axis",
    "matplotlib.lines", "matplotlib.patches",
    "matplotlib.colors", "matplotlib.ticker",
    "matplotlib.font_manager",
    "matplotlib.backends.backend_agg",
    "matplotlib.backends.backend_qtagg",
    "mpl_toolkits",
    # ─ matplotlib 间接依赖 ─
    "cycler", "kiwisolver", "pyparsing",
    "dateutil", "six", "packaging",
    "PIL", "darkdetect",
    # ─ stdlib（matplotlib 运行时需要 unittest） ─
    "unittest", "unittest.mock",
]

# ══════════════════════════════════════════════════════════════════════
# Analysis
# ══════════════════════════════════════════════════════════════════════
a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        *collect_data_files("matplotlib"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    cipher=block_cipher,
)

# ── 裁剪 Qt 动态库（仅移除确认不需要的，其他全部保留） ──
_QT_LIB_STRIP = (
    "libQt63D", "libQt6Bluetooth",
    "libQt6Charts", "libQt6DataVisualization", "libQt6Graphs",
    "libQt6Designer", "libQt6Test",
    "libQt6Help", "libQt6HttpServer",
    "libQt6Location", "libQt6Positioning", "libQt6Sensors",
    "libQt6Nfc", "libQt6SerialBus", "libQt6SerialPort",
    "libQt6Pdf",
    "libQt6Quick", "libQt6Qml",
    "libQt6RemoteObjects", "libQt6Scxml", "libQt6StateMachine",
    "libQt6ShaderTools", "libQt6SpatialAudio",
    "libQt6Sql",
    "libQt6TextToSpeech", "libQt6VirtualKeyboard",
    "libQt6WebChannel", "libQt6WebEngine", "libQt6WebSockets", "libQt6WebView",
    "libQt6OpenGL",
    "libQt6Concurrent", "libQt6Labs", "libQt6UiTools",
    "libQt6DBus", "libQt6PrintSupport", "libQt6Wayland",
)

def _keep_binary(name):
    if any(name.startswith(p) for p in _QT_LIB_STRIP):
        return False
    return True

a.binaries = [b for b in a.binaries if _keep_binary(b[0])]

# ── 裁剪数据文件 ──
a.datas = [
    d for d in a.datas
    if not d[0].startswith("PySide6/Qt/translations")
    and not d[0].startswith("matplotlib/mpl-data/sample_data")
    and "/tests/" not in d[0]
]

# ── PYZ ──
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
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
