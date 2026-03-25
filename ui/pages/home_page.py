from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import PrimaryPushButton

from ui.theme import text_color, secondary_color, placeholder_color


class HomePage(QWidget):
    """首页 - 项目列表/新建/打开"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # 标题
        title = QLabel("PyLine", self)
        title.setStyleSheet(f"font-size: 48px; font-weight: bold; color: {text_color()};")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # 副标题
        subtitle = QLabel("曲线提取与数据可视化工具", self)
        subtitle.setStyleSheet(f"font-size: 18px; color: {secondary_color()};")
        layout.addWidget(subtitle, alignment=Qt.AlignCenter)

        layout.addSpacing(40)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        new_btn = PrimaryPushButton("新建项目", self)
        new_btn.setFixedWidth(150)
        new_btn.clicked.connect(self.on_new_project)
        btn_layout.addWidget(new_btn)

        open_btn = QPushButton("打开项目", self)
        open_btn.setFixedWidth(150)
        open_btn.clicked.connect(self.on_open_project)
        btn_layout.addWidget(open_btn)

        layout.addLayout(btn_layout)
        btn_layout.setAlignment(Qt.AlignCenter)

        # 最近项目（预留）
        layout.addSpacing(60)
        recent_label = QLabel("最近项目", self)
        recent_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {text_color()};")
        layout.addWidget(recent_label, alignment=Qt.AlignLeft)

        no_recent = QLabel("暂无最近项目", self)
        no_recent.setStyleSheet(f"color: {placeholder_color()}; font-style: italic;")
        layout.addWidget(no_recent, alignment=Qt.AlignLeft)

        layout.addStretch()

    def on_new_project(self):
        # TODO: 实现新建项目
        pass

    def on_open_project(self):
        # TODO: 实现打开项目
        pass
