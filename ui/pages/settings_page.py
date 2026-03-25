from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QTimer
from qfluentwidgets import ComboBox, setTheme, Theme, isDarkTheme, CardWidget


class SettingsPage(QWidget):
    """设置页面 - 主题切换等配置"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._title_label = None
        self._theme_label = None
        self._lang_title = None
        self._lang_placeholder = None
        self._appearance_card = None
        self._lang_card = None
        self.setup_ui()

    def _get_text_color(self):
        return "#ffffff" if isDarkTheme() else "#000000"

    def _get_secondary_color(self):
        return "#a0a0a0" if isDarkTheme() else "#808080"

    def _get_placeholder_color(self):
        return "#808080" if isDarkTheme() else "#a0a0a0"

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # 标题
        self._title_label = QLabel("设置", self)
        self._title_label.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {self._get_text_color()};")
        layout.addWidget(self._title_label)

        # 外观设置卡片
        self._appearance_card = CardWidget(self)

        appearance_layout = QVBoxLayout(self._appearance_card)

        appearance_title = QLabel("外观", self._appearance_card)
        appearance_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        appearance_layout.addWidget(appearance_title)

        # 主题设置
        theme_layout = QVBoxLayout()
        self._theme_label = QLabel("主题", self)
        self._theme_label.setStyleSheet(f"color: {self._get_text_color()};")
        theme_layout.addWidget(self._theme_label)

        self.theme_combo = ComboBox(self)
        self.theme_combo.addItems(["浅色", "深色", "跟随系统"])
        self.theme_combo.setCurrentIndex(2)  # 默认跟随系统
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)

        appearance_layout.addLayout(theme_layout)
        layout.addWidget(self._appearance_card)

        # 语言设置（预留）
        self._lang_card = CardWidget(self)

        lang_layout = QVBoxLayout(self._lang_card)

        self._lang_title = QLabel("语言", self._lang_card)
        self._lang_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        lang_layout.addWidget(self._lang_title)

        self._lang_placeholder = QLabel("语言设置（预留）", self)
        self._lang_placeholder.setStyleSheet(f"color: {self._get_placeholder_color()}; font-style: italic;")
        lang_layout.addWidget(self._lang_placeholder)

        layout.addWidget(self._lang_card)

        layout.addStretch()

    def on_theme_changed(self, index):
        themes = [Theme.LIGHT, Theme.DARK, Theme.AUTO]
        setTheme(themes[index])
        # 延迟刷新颜色，等待主题应用完成
        QTimer.singleShot(50, self._update_colors)

    def _update_colors(self):
        """更新界面颜色以适应新主题"""
        self._title_label.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {self._get_text_color()};")
        self._theme_label.setStyleSheet(f"color: {self._get_text_color()};")
        self._lang_placeholder.setStyleSheet(f"color: {self._get_placeholder_color()}; font-style: italic;")
