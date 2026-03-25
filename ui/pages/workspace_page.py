from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QSplitter, QFileDialog, QPushButton
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import CardWidget, PrimaryPushButton

from ui.theme import text_color, secondary_color, placeholder_color
from ui.widgets import ImageViewer
from core.project_manager import project_manager


class WorkspacePage(QWidget):
    """工作区页面 - 主功能区"""

    add_image_clicked = Signal()  # 添加图片信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._splitter = None
        self._left_panel = None
        self._right_panel = None
        self._image_viewer = None
        self._tool_buttons = []
        self._image_list_label = None
        self._add_image_btn = None
        self._add_image_hbox = None
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

        # 添加图片按钮
        self._add_image_btn = PrimaryPushButton("添加图片", panel)
        self._add_image_btn.setFixedHeight(32)
        self._add_image_btn.clicked.connect(self._on_add_image)
        layout.addWidget(self._add_image_btn)

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

    def _refresh_image_list(self):
        """刷新图片列表显示"""
        if project_manager.current_project is None:
            content = "请先创建或打开项目"
        elif not project_manager.current_project.images:
            content = "暂无图片\n\n点击上方「添加图片」按钮"
        else:
            lines = ["📷 图片列表:"]
            for img in project_manager.current_project.images:
                lines.append(f"• {img.name}")
            content = "\n".join(lines)
        self._image_list_label.setText(content)
        self._image_list_label.setStyleSheet(f"color: {placeholder_color() if not project_manager.current_project or not project_manager.current_project.images else text_color()}; font-style: italic;" if not project_manager.current_project or not project_manager.current_project.images else f"color: {text_color()};")

    def _border_color(self):
        """获取边框颜色"""
        from qfluentwidgets import isDarkTheme
        return "#3d3d3d" if isDarkTheme() else "#e0e0e0"

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

    def _on_add_image(self):
        """添加图片按钮点击"""
        if project_manager.current_project is None:
            from PySide6.QtWidgets import QMessageBox
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
