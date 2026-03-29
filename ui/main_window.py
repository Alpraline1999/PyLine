from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox
from qfluentwidgets import FluentWindow, NavigationItemPosition, setTheme, Theme
from qfluentwidgets.common.icon import FluentIcon as FIF

from .pages.home_page import HomePage
from .pages.workspace_page import WorkspacePage
from .pages.settings_page import SettingsPage
from core.project_manager import project_manager


class MainWindow(FluentWindow):
    """PyLine 主窗口"""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self._setup_theme_watcher()
        self._setup_project_signals()

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

        # 导航栏默认折叠（仅显示图标），不常驻展开占据界面空间
        self.navigationInterface.setCollapsible(True)
        self.navigationInterface.toggle()  # 初始状态: 折叠（图标模式）

    def _setup_theme_watcher(self):
        """监听主题变化并更新各页面颜色"""
        self.settings_page.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        # 快捷键更新信号 → workspace 重新绑定
        self.settings_page.shortcuts_changed.connect(self.workspace_page.apply_shortcuts)

    def _setup_project_signals(self):
        """监听项目事件"""
        self.home_page.project_created.connect(self._on_project_created)
        self.home_page.project_opened.connect(self._on_project_opened)
        self.workspace_page.project_modified.connect(self._on_project_modified)
        self.workspace_page.project_saved.connect(self._update_window_title)

    def _on_project_created(self, name: str):
        """项目创建后的处理"""
        self._update_window_title()
        self.workspace_page._refresh_project_tree()
        self.switchTo(self.workspace_page)

    def _on_project_opened(self, file_path: str):
        """项目打开后的处理"""
        self._update_window_title()
        self.workspace_page._refresh_project_tree()
        self.switchTo(self.workspace_page)

    def _on_project_modified(self):
        """项目修改后的处理 - 标记未保存状态"""
        if project_manager.current_project:
            project_manager.current_project.is_modified = True
        self._update_window_title()

    def _update_window_title(self):
        """更新窗口标题，未保存时显示 *"""
        if project_manager.current_project:
            name = project_manager.current_project.name
            modified = project_manager.current_project.is_modified
            marker = " *" if modified else ""
            self.setWindowTitle(f"PyLine - {name}{marker}")
        else:
            self.setWindowTitle("PyLine")

    def closeEvent(self, event):
        """关闭前检查未保存的项目"""
        unsaved = [p for p in project_manager.projects if p.is_modified]
        if unsaved:
            names = "、".join(p.name for p in unsaved)
            reply = QMessageBox.question(
                self,
                "未保存的更改",
                f"以下项目有未保存的更改：\n{names}\n\n确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()

    def _on_theme_changed(self, index):
        """主题切换后的回调"""
        themes = [Theme.LIGHT, Theme.DARK, Theme.AUTO]
        setTheme(themes[index])
        QTimer.singleShot(100, self._update_all_pages_theme)

    def _update_all_pages_theme(self):
        """更新所有页面的主题颜色"""
        self.home_page.update_theme()
        self.settings_page._update_colors()
        self.workspace_page.update_theme_colors()
