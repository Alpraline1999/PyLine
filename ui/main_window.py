from qfluentwidgets import FluentWindow, NavigationItemPosition
from qfluentwidgets.common.icon import FluentIcon as FIF

from .pages.home_page import HomePage
from .pages.workspace_page import WorkspacePage
from .pages.settings_page import SettingsPage


class MainWindow(FluentWindow):
    """PyLine 主窗口"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # 设置窗口标题
        self.setWindowTitle("PyLine")

        # 设置导航图标
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
