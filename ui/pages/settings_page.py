from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QScrollArea, QFrame, QFormLayout, QKeySequenceEdit)
from PySide6.QtCore import Qt, QTimer, Signal
from qfluentwidgets import ComboBox, setTheme, Theme, CardWidget, PushButton

from ui.theme import text_color, secondary_color, placeholder_color
from core.shortcut_manager import shortcut_manager


class SettingsPage(QWidget):
    """设置页面 - 主题切换、快捷键自定义等配置"""

    shortcuts_changed = Signal()  # 快捷键保存后发出

    def __init__(self, parent=None):
        super().__init__(parent)
        self._title_label = None
        self._theme_label = None
        self._appearance_title = None
        self._lang_title = None
        self._lang_placeholder = None
        self._shortcuts_title = None
        self._appearance_card = None
        self._lang_card = None
        self._shortcuts_card = None
        self.theme_combo = None
        self._shortcut_edits: dict[str, QKeySequenceEdit] = {}
        self._shortcut_labels: list[QLabel] = []
        self._conflict_labels: dict[str, QLabel] = {}  # action -> red warning label
        self.setup_ui()

    def setup_ui(self):
        outer = QScrollArea(self)
        outer.setWidgetResizable(True)
        outer.setFrameShape(QFrame.Shape.NoFrame)
        outer.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        outer.setWidget(content)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(outer)

        # 标题
        self._title_label = QLabel("设置", content)
        self._title_label.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {text_color()};")
        layout.addWidget(self._title_label)

        # ── 外观设置 ──
        self._appearance_card = CardWidget(content)
        appearance_layout = QVBoxLayout(self._appearance_card)

        self._appearance_title = QLabel("外观", self._appearance_card)
        self._appearance_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {text_color()};")
        appearance_layout.addWidget(self._appearance_title)

        theme_layout = QVBoxLayout()
        self._theme_label = QLabel("主题", content)
        self._theme_label.setStyleSheet(f"color: {text_color()};")
        theme_layout.addWidget(self._theme_label)

        self.theme_combo = ComboBox(content)
        self.theme_combo.addItems(["浅色", "深色", "跟随系统"])
        self.theme_combo.setCurrentIndex(2)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)

        appearance_layout.addLayout(theme_layout)
        layout.addWidget(self._appearance_card)

        # ── 语言设置（预留）──
        self._lang_card = CardWidget(content)
        lang_layout = QVBoxLayout(self._lang_card)

        self._lang_title = QLabel("语言", self._lang_card)
        self._lang_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {text_color()};")
        lang_layout.addWidget(self._lang_title)

        self._lang_placeholder = QLabel("语言设置（预留）", content)
        self._lang_placeholder.setStyleSheet(f"color: {placeholder_color()}; font-style: italic;")
        lang_layout.addWidget(self._lang_placeholder)

        layout.addWidget(self._lang_card)
        self._lang_card.hide()  # 暂不实现语言设置

        # ── 快捷键自定义 ──
        self._shortcuts_card = CardWidget(content)
        shortcuts_layout = QVBoxLayout(self._shortcuts_card)

        self._shortcuts_title = QLabel("快捷键", self._shortcuts_card)
        self._shortcuts_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {text_color()};")
        shortcuts_layout.addWidget(self._shortcuts_title)

        hint = QLabel("点击输入框后按下新快捷键即可修改。按 → 应用快捷键 保存。", self._shortcuts_card)
        hint.setStyleSheet(f"color: {placeholder_color()}; font-size: 11px;")
        hint.setWordWrap(True)
        shortcuts_layout.addWidget(hint)

        sc_content = QWidget(self._shortcuts_card)
        sc_form = QFormLayout(sc_content)
        sc_form.setSpacing(6)
        sc_form.setContentsMargins(0, 4, 0, 4)

        for action, label in shortcut_manager.LABELS.items():
            from ui.theme import card_background_color, border_color
            edit = QKeySequenceEdit(sc_content)
            from PySide6.QtGui import QKeySequence
            edit.setKeySequence(QKeySequence(shortcut_manager.get(action)))
            edit.setStyleSheet(
                f"background: {card_background_color()}; color: {text_color()};"
                f" border: 1px solid {border_color()}; border-radius: 4px; padding: 3px;"
            )
            row_lbl = QLabel(label + ":", sc_content)
            row_lbl.setStyleSheet(f"color: {text_color()};")

            # 冲突提示标签
            conflict_lbl = QLabel("", sc_content)
            conflict_lbl.setStyleSheet("color: #e81123; font-size: 10px;")
            conflict_lbl.setVisible(False)

            # 垂直堆叠 edit + conflict_lbl
            edit_col = QWidget(sc_content)
            ecol_layout = QVBoxLayout(edit_col)
            ecol_layout.setContentsMargins(0, 0, 0, 0)
            ecol_layout.setSpacing(1)
            ecol_layout.addWidget(edit)
            ecol_layout.addWidget(conflict_lbl)

            sc_form.addRow(row_lbl, edit_col)
            self._shortcut_edits[action] = edit
            self._shortcut_labels.append(row_lbl)
            self._conflict_labels[action] = conflict_lbl
            edit.keySequenceChanged.connect(lambda ks, a=action: self._check_shortcut_conflict(a, ks))

        shortcuts_layout.addWidget(sc_content)

        btn_row = QHBoxLayout()
        apply_btn = PushButton("应用快捷键", self._shortcuts_card)
        apply_btn.clicked.connect(self._on_apply_shortcuts)
        reset_btn = PushButton("恢复默认", self._shortcuts_card)
        reset_btn.clicked.connect(self._on_reset_shortcuts)
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        shortcuts_layout.addLayout(btn_row)

        layout.addWidget(self._shortcuts_card)
        layout.addStretch()

    def _on_apply_shortcuts(self):
        """保存用户修改的快捷键"""
        mapping = {}
        for action, edit in self._shortcut_edits.items():
            mapping[action] = edit.keySequence().toString()
        shortcut_manager.apply_all(mapping)
        self.shortcuts_changed.emit()

    def _check_shortcut_conflict(self, changed_action: str, ks):
        """实时检测快捷键冲突"""
        ks_str = ks.toString() if not isinstance(ks, str) else ks
        # 清空所有冲突提示
        for a, lbl in self._conflict_labels.items():
            lbl.setVisible(False)
        if not ks_str:
            return
        # 找所有与此序列重复的 action
        conflicts = []
        for a, edit in self._shortcut_edits.items():
            if a != changed_action and edit.keySequence().toString() == ks_str:
                conflicts.append(a)
        if conflicts:
            from core.shortcut_manager import shortcut_manager as sm
            conflict_names = " / ".join(sm.LABELS.get(a, a) for a in conflicts)
            self._conflict_labels[changed_action].setText(f"与「{conflict_names}」冲突")
            self._conflict_labels[changed_action].setVisible(True)
            for a in conflicts:
                if a in self._conflict_labels:
                    cur_ks = self._shortcut_edits[changed_action].keySequence().toString()
                    changed_name = sm.LABELS.get(changed_action, changed_action)
                    self._conflict_labels[a].setText(f"与「{changed_name}」冲突")
                    self._conflict_labels[a].setVisible(True)

    def _on_reset_shortcuts(self):
        """恢复所有快捷键为默认值"""
        shortcut_manager.reset_to_defaults()
        from PySide6.QtGui import QKeySequence
        for action, edit in self._shortcut_edits.items():
            edit.setKeySequence(QKeySequence(shortcut_manager.get(action)))
        self.shortcuts_changed.emit()

    def on_theme_changed(self, index):
        themes = [Theme.LIGHT, Theme.DARK, Theme.AUTO]
        setTheme(themes[index])
        QTimer.singleShot(50, self._update_colors)

    def _update_colors(self):
        """更新界面颜色以适应新主题"""
        from ui.theme import card_background_color, border_color
        tc = text_color()
        pc = placeholder_color()
        self._title_label.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {tc};")
        self._appearance_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {tc};")
        self._theme_label.setStyleSheet(f"color: {tc};")
        if self._shortcuts_title:
            self._shortcuts_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {tc};")
        # 快捷键行标签
        for lbl in self._shortcut_labels:
            lbl.setStyleSheet(f"color: {tc};")
        # QKeySequenceEdit 样式
        bg = card_background_color()
        bc = border_color()
        for edit in self._shortcut_edits.values():
            edit.setStyleSheet(
                f"background: {bg}; color: {tc};"
                f" border: 1px solid {bc}; border-radius: 4px; padding: 3px;"
            )
        # hint label（找到快捷键卡片下方的说明标签）
        for lbl in self._shortcuts_card.findChildren(QLabel):
            ss = lbl.styleSheet()
            if 'font-size: 11px' in ss:
                lbl.setStyleSheet(f"color: {pc}; font-size: 11px;")