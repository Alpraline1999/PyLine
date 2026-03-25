from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QSplitter, QFileDialog, QPushButton, QInputDialog, QMessageBox
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import CardWidget, PrimaryPushButton, ToolButton, ToolTipFilter
from qfluentwidgets.common.icon import FluentIcon as FIF

from ui.theme import text_color, secondary_color, placeholder_color
from ui.widgets import ImageViewer
from core.project_manager import project_manager


class WorkspacePage(QWidget):
    """工作区页面 - 主功能区"""

    project_modified = Signal()  # 项目修改信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._splitter = None
        self._left_panel = None
        self._right_panel = None
        self._image_viewer = None
        self._tool_buttons = []
        self._image_list_label = None
        self._add_image_btn = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 使用 QSplitter 实现可拖动的分割
        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧面板（项目树/曲线列表）
        self._left_panel = self._create_left_panel()
        self._splitter.addWidget(self._left_panel)

        # 中间区域（图片查看器）
        center_panel = QFrame(self)
        center_panel.setFrameShape(QFrame.Shape.StyledPanel)
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(10, 10, 10, 10)

        center_label = QLabel("图片查看器", center_panel)
        center_label.setStyleSheet(f"font-weight: bold; padding: 5px; color: {text_color()};")
        center_layout.addWidget(center_label)

        # 图片查看器
        self._image_viewer = ImageViewer(center_panel)
        self._image_viewer.image_loaded.connect(self._on_image_loaded)
        center_layout.addWidget(self._image_viewer)

        # 底部工具栏占位
        toolbar = QFrame(center_panel)
        toolbar.setFixedHeight(50)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)

        self._tool_buttons = []
        tool_buttons = ["选取颜色", "框选蒙版", "涂刷蒙版", "橡皮擦", "撤销", "重做", "放大镜", "校准", "对比视图"]
        for name in tool_buttons:
            btn = QLabel(name, toolbar)
            btn.setStyleSheet(f"padding: 5px 10px; color: {text_color()}; background-color: {secondary_color()}; border-radius: 3px;")
            toolbar_layout.addWidget(btn)
            self._tool_buttons.append(btn)
        toolbar_layout.addStretch()

        center_layout.addWidget(toolbar)
        self._splitter.addWidget(center_panel)

        # 右侧面板（属性）
        self._right_panel = self._create_side_panel("属性面板", "当前选中项\n属性", 260)
        self._splitter.addWidget(self._right_panel)

        # 设置分割比例：左侧1，中间3，右侧1
        self._splitter.setSizes([1, 3, 1])
        self._splitter.setStretchFactor(1, 1)

        main_layout.addWidget(self._splitter)

    def _create_left_panel(self) -> CardWidget:
        """创建左侧面板"""
        panel = CardWidget(self)
        panel.setFixedWidth(260)
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 标题
        title_label = QLabel("项目面板", panel)
        title_label.setStyleSheet(f"font-weight: bold; padding: 5px; color: {text_color()};")
        layout.addWidget(title_label)

        # 工具按钮区域
        toolbar_widget = QWidget(panel)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(5)

        # 新建项目按钮
        self._new_project_btn = ToolButton(FIF.ADD, toolbar_widget)
        self._new_project_btn.setToolTip("新建项目")
        self._new_project_btn.clicked.connect(self._on_new_project)
        toolbar_layout.addWidget(self._new_project_btn)

        # 打开项目按钮
        self._open_project_btn = ToolButton(FIF.FOLDER, toolbar_widget)
        self._open_project_btn.setToolTip("打开项目")
        self._open_project_btn.clicked.connect(self._on_open_project)
        toolbar_layout.addWidget(self._open_project_btn)

        # 保存项目按钮
        self._save_project_btn = ToolButton(FIF.SAVE, toolbar_widget)
        self._save_project_btn.setToolTip("保存项目")
        self._save_project_btn.clicked.connect(self._on_save_project)
        toolbar_layout.addWidget(self._save_project_btn)

        # 关闭项目按钮
        self._close_project_btn = ToolButton(FIF.CLOSE, toolbar_widget)
        self._close_project_btn.setToolTip("关闭项目")
        self._close_project_btn.clicked.connect(self._on_close_project)
        toolbar_layout.addWidget(self._close_project_btn)

        toolbar_layout.addStretch()
        layout.addWidget(toolbar_widget)

        # 添加图片按钮
        self._add_image_btn = ToolButton(FIF.CAMERA, toolbar_widget)
        self._add_image_btn.setToolTip("添加图片")
        self._add_image_btn.clicked.connect(self._on_add_image)
        toolbar_layout.addWidget(self._add_image_btn)

        # 分隔线
        line = QFrame(panel)
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {self._border_color()};")
        layout.addWidget(line)

        # 图片列表标签
        self._image_list_label = QLabel(panel)
        self._image_list_label.setWordWrap(True)
        self._refresh_image_list()
        layout.addWidget(self._image_list_label)

        layout.addStretch()
        return panel

    def _border_color(self):
        """获取边框颜色"""
        from qfluentwidgets import isDarkTheme
        return "#3d3d3d" if isDarkTheme() else "#e0e0e0"

    def _refresh_image_list(self):
        """刷新图片列表显示"""
        if project_manager.current_project is None:
            content = "请先创建或打开项目"
            self._image_list_label.setStyleSheet(f"color: {placeholder_color()}; font-style: italic;")
        elif not project_manager.current_project.images:
            content = "暂无图片\n\n点击上方「添加图片」按钮"
            self._image_list_label.setStyleSheet(f"color: {placeholder_color()}; font-style: italic;")
        else:
            lines = ["📷 图片列表:"]
            for img in project_manager.current_project.images:
                lines.append(f"• {img.name}")
            content = "\n".join(lines)
            self._image_list_label.setStyleSheet(f"color: {text_color()};")
        self._image_list_label.setText(content)

    def _create_side_panel(self, title: str, placeholder: str, width: int) -> CardWidget:
        """创建侧边面板"""
        panel = CardWidget(self)
        panel.setFixedWidth(width)
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        label = QLabel(title, panel)
        label.setStyleSheet(f"font-weight: bold; padding: 5px; color: {text_color()};")
        layout.addWidget(label)

        placeholder_label = QLabel(placeholder, panel)
        placeholder_label.setStyleSheet(f"color: {placeholder_color()}; font-style: italic;")
        placeholder_label.setWordWrap(True)
        layout.addWidget(placeholder_label)

        layout.addStretch()
        return panel

    def _on_new_project(self):
        """新建项目"""
        name, ok = QInputDialog.getText(self, "新建项目", "请输入项目名称:")
        if ok and name:
            project_manager.create_new(name)
            self._refresh_image_list()
            self.project_modified.emit()

    def _on_open_project(self):
        """打开项目"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开项目",
            "",
            "PyLine 项目 (*.pyline);;所有文件 (*)"
        )
        if file_path:
            try:
                project_manager.open(file_path)
                self._refresh_image_list()
                self.project_modified.emit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开项目:\n{str(e)}")

    def _on_save_project(self):
        """保存项目"""
        if project_manager.current_project is None:
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
                QMessageBox.information(self, "成功", f"项目已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")

    def _on_close_project(self):
        """关闭项目"""
        project_manager.close()
        self._refresh_image_list()
        self.project_modified.emit()

    def _on_add_image(self):
        """添加图片按钮点击"""
        if project_manager.current_project is None:
            QMessageBox.warning(self, "警告", "请先创建或打开项目")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;所有文件 (*)"
        )
        if file_path:
            # 添加到项目
            project_manager.add_image(file_path)
            # 加载到查看器
            self._image_viewer.load_image(file_path)
            # 刷新列表
            self._refresh_image_list()
            self.project_modified.emit()

    def _on_image_loaded(self, file_path: str):
        """图片加载完成"""
        self._refresh_image_list()

    def load_image(self, file_path: str) -> bool:
        """加载图片到查看器"""
        if self._image_viewer:
            return self._image_viewer.load_image(file_path)
        return False

    def update_theme_colors(self):
        """更新主题颜色（供外部调用）"""
        for btn in self._tool_buttons:
            btn.setStyleSheet(f"padding: 5px 10px; color: {text_color()}; background-color: {secondary_color()}; border-radius: 3px;")
