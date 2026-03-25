from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QSplitter
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import isDarkTheme, CardWidget, FluentStyleSheet


class WorkspacePage(QWidget):
    """工作区页面 - 主功能区"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 使用 QSplitter 实现可拖动的分割
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧面板（项目树/曲线列表）
        left_panel = self._create_panel("项目面板", "图片列表\n---\n曲线列表", 260)
        splitter.addWidget(left_panel)

        # 中间区域（图片查看器）
        center_panel = QFrame(self)
        center_panel.setFrameShape(QFrame.Shape.StyledPanel)
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(10, 10, 10, 10)

        center_label = QLabel("图片查看器", center_panel)
        center_label.setObjectName("centerLabel")
        center_label.setStyleSheet("font-weight: bold; padding: 5px;")
        center_layout.addWidget(center_label)

        center_placeholder = QLabel("拖放图片到此处\n或使用 文件 > 打开", center_panel)
        center_placeholder.setObjectName("placeholder")
        center_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(center_placeholder)

        # 底部工具栏占位
        toolbar = QFrame(center_panel)
        toolbar.setFixedHeight(50)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)

        tool_buttons = ["选取颜色", "框选蒙版", "涂刷蒙版", "橡皮擦", "撤销", "重做", "放大镜", "校准", "对比视图"]
        for name in tool_buttons:
            btn = QLabel(name, toolbar)
            btn.setObjectName("toolButton")
            toolbar_layout.addWidget(btn)
        toolbar_layout.addStretch()

        center_layout.addWidget(toolbar)
        splitter.addWidget(center_panel)

        # 右侧面板（属性）
        right_panel = self._create_panel("属性面板", "当前选中项\n属性", 260)
        splitter.addWidget(right_panel)

        # 设置分割比例：左侧1，中间3，右侧1
        splitter.setSizes([1, 3, 1])
        splitter.setStretchFactor(1, 1)  # 中间面板可伸展

        main_layout.addWidget(splitter)

    def _create_panel(self, title, placeholder, width):
        """创建面板，使用 CardWidget 以支持主题适配"""
        panel = CardWidget(self)
        panel.setFixedWidth(width)
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        label = QLabel(title, panel)
        label.setObjectName("panelTitle")
        layout.addWidget(label)

        placeholder_label = QLabel(placeholder, panel)
        placeholder_label.setObjectName("panelPlaceholder")
        layout.addWidget(placeholder_label)

        layout.addStretch()
        return panel
