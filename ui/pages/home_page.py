from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import PrimaryPushButton

from ui.theme import text_color, secondary_color, placeholder_color


class HomePage(QWidget):
    """首页 - 项目列表/新建/打开"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._title = None
        self._subtitle = None
        self._recent_label = None
        self._no_recent = None
        self._new_btn = None
        self._open_btn = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        # 左侧边距需要足够大，避免被导航栏遮挡
        layout.setContentsMargins(220, 40, 40, 40)

        # 标题
        self._title = QLabel("PyLine", self)
        self._title.setStyleSheet("font-size: 48px; font-weight: bold;")
        layout.addWidget(self._title, alignment=Qt.AlignCenter)

        # 副标题
        self._subtitle = QLabel("曲线提取与数据可视化工具", self)
        self._subtitle.setStyleSheet("font-size: 18px;")
        layout.addWidget(self._subtitle, alignment=Qt.AlignCenter)

        layout.addSpacing(40)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        self._new_btn = PrimaryPushButton("新建项目", self)
        self._new_btn.setFixedWidth(150)
        self._new_btn.clicked.connect(self.on_new_project)
        btn_layout.addWidget(self._new_btn)

        self._open_btn = QPushButton("打开项目", self)
        self._open_btn.setFixedWidth(150)
        self._open_btn.clicked.connect(self.on_open_project)
        btn_layout.addWidget(self._open_btn)

        layout.addLayout(btn_layout)
        btn_layout.setAlignment(Qt.AlignCenter)

        # 最近项目（预留）
        layout.addSpacing(60)
        self._recent_label = QLabel("最近项目", self)
        self._recent_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self._recent_label, alignment=Qt.AlignLeft)

        self._no_recent = QLabel("暂无最近项目", self)
        self._no_recent.setStyleSheet("font-style: italic;")
        layout.addWidget(self._no_recent, alignment=Qt.AlignLeft)

        layout.addStretch()

        # 初始应用主题颜色
        self._apply_theme_colors()

    def _apply_theme_colors(self):
        """应用当前主题颜色"""
        tc = text_color()
        sc = secondary_color()
        pc = placeholder_color()
        self._title.setStyleSheet(f"font-size: 48px; font-weight: bold; color: {tc};")
        self._subtitle.setStyleSheet(f"font-size: 18px; color: {sc};")
        self._recent_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {tc};")
        self._no_recent.setStyleSheet(f"color: {pc}; font-style: italic;")

    def update_theme(self):
        """更新主题颜色（供外部调用）"""
        self._apply_theme_colors()

    def on_new_project(self):
        # TODO: 实现新建项目
        pass

    def on_open_project(self):
        # TODO: 实现打开项目
        pass
