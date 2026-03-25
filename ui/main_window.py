from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMenuBar, QMenu, QFileDialog, QMessageBox
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

    def _setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        open_image_action = file_menu.addAction("打开图片...")
        open_image_action.triggered.connect(self._on_open_image)

        save_project_action = file_menu.addAction("保存项目")
        save_project_action.triggered.connect(self._on_save_project)

        file_menu.addSeparator()

        close_project_action = file_menu.addAction("关闭项目")
        close_project_action.triggered.connect(self._on_close_project)

    def _on_open_image(self):
        """打开图片"""
        if project_manager.current_project is None:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", "请先创建或打开项目")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;所有文件 (*)"
        )
        if file_path:
            self.workspace_page.load_image(file_path)
            # 将图片添加到项目
            project_manager.add_image(file_path)

    def _on_save_project(self):
        """保存项目"""
        from PySide6.QtWidgets import QFileDialog
        if project_manager.current_project is None:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", "没有当前项目")
            return

        file_path = project_manager.file_path
        if file_path is None:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存项目",
                f"{project_manager.current_project.name}.pyline",
                "PyLine 项目 (*.pyline)"
            )

        if file_path:
            try:
                project_manager.save(file_path)
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "成功", f"项目已保存到:\n{file_path}")
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")

    def _on_close_project(self):
        """关闭项目"""
        project_manager.close()
        self._update_window_title()

    def _setup_theme_watcher(self):
        """监听主题变化并更新各页面颜色"""
        self.settings_page.theme_combo.currentIndexChanged.connect(self._on_theme_changed)

    def _setup_project_signals(self):
        """监听项目事件"""
        self.home_page.project_created.connect(self._on_project_created)
        self.home_page.project_opened.connect(self._on_project_opened)

    def _on_project_created(self, name: str):
        """项目创建后的处理"""
        self._update_window_title()
        self.switchTo(self.workspace_page)

    def _on_project_opened(self, file_path: str):
        """项目打开后的处理"""
        self._update_window_title()
        self.switchTo(self.workspace_page)

    def _update_window_title(self):
        """更新窗口标题"""
        if project_manager.current_project:
            self.setWindowTitle(f"PyLine - {project_manager.current_project.name}")
        else:
            self.setWindowTitle("PyLine")

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
