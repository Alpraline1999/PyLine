import sys
import os

# 确保项目根目录在 sys.path 中，无论从哪里启动
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from qfluentwidgets.common.config import qconfig, Theme
from qfluentwidgets.common.style_sheet import setTheme

from ui.main_window import MainWindow

# 图标路径（兼容 PyInstaller 打包后的路径）
def _icon_path() -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = _ROOT
    return os.path.join(base, "assets", "icon.ico")


def main():
    # Linux: 设置 wmclass，使桌面环境能正确关联应用图标
    if sys.platform.startswith("linux"):
        os.environ.setdefault("XDG_SESSION_TYPE", "x11")

    app = QApplication(sys.argv)

    # 设置应用级图标（任务栏 / Dock）
    icon_file = _icon_path()
    if os.path.exists(icon_file):
        app.setWindowIcon(QIcon(icon_file))

    # 设置默认主题（跟随系统）
    setTheme(Theme.AUTO)

    # 创建并显示主窗口
    window = MainWindow()
    window.resize(1200, 800)
    if os.path.exists(icon_file):
        window.setWindowIcon(QIcon(icon_file))
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
