from PySide6.QtCore import QTimer
from qfluentwidgets import FluentWindow, NavigationItemPosition, setTheme, Theme
from qfluentwidgets.common.icon import FluentIcon as FIF
from qfluentwidgets.common.config import qconfig

from .pages.home_page import HomePage
from .pages.workspace_page import WorkspacePage
from .pages.settings_page import SettingsPage


class MainWindow(FluentWindow):
    """PyLine 主窗口"""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self._setup_theme_watcher()

    def setup_ui(self):
        # 设置窗口标题
        self.setWindowTitle("PyLine")

        # 创建页面
        self.home_page = HomePage(self)
        self.home_page.setObjectName("homePage")

        self.workspace_page = WorkspacePage(self)
        self.workspace_page.setObjectName("workspacePage")

        self.settings_page = SettingsPage(self)
        self.settings_page.setObjectName("settingsPage")

        # 添加子页面到导航
        self.addSubInterface(
            interface=self.home_page,
            icon=FIF.HOME,
            text="首页",
            position=NavigationItemPosition.TOP
        )

        self.addSubInterface(
            interface=self.workspace_page,
            icon=FIF.EDIT,
            text="工作区",
            position=NavigationItemPosition.TOP
        )

        self.addSubInterface(
            interface=self.settings_page,
            icon=FIF.SETTING,
            text="设置",
            position=NavigationItemPosition.BOTTOM
        )

    def _setup_theme_watcher(self):
        """监听主题变化并更新各页面颜色"""
        # 连接设置页面的主题切换信号
        self.settings_page.theme_combo.currentIndexChanged.connect(self._on_theme_changed)

    def _on_theme_changed(self, index):
        """主题切换后的回调"""
        themes = [Theme.LIGHT, Theme.DARK, Theme.AUTO]
        setTheme(themes[index])
        # 延迟更新，等待主题应用完成
        QTimer.singleShot(100, self._update_all_pages_theme)

    def _update_all_pages_theme(self):
        """更新所有页面的主题颜色"""
        self.home_page.update_theme()
        self.settings_page._update_colors()
        self.workspace_page.update_theme_colors()
