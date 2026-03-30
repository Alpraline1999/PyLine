import sys
import os

# 确保项目根目录在 sys.path 中，无论从哪里启动
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from PySide6.QtWidgets import QApplication
from qfluentwidgets.common.config import qconfig, Theme
from qfluentwidgets.common.style_sheet import setTheme

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # 设置默认主题（跟随系统）
    setTheme(Theme.AUTO)

    # 创建并显示主窗口
    window = MainWindow()
    window.resize(1200, 800)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
