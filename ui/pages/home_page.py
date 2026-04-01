from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QFrame
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (PrimaryPushButton, PushButton, FluentIcon as FIF,
    BodyLabel, LargeTitleLabel, SubtitleLabel, SmoothScrollArea,
    InfoBar, MessageBox, MessageBoxBase, LineEdit)

from ui.theme import text_color, secondary_color, placeholder_color
from core.project_manager import project_manager
from core.recent_projects import load_recent, remove_recent



class _InputDialog(MessageBoxBase):
    """输入对话框"""
    def __init__(self, title: str, placeholder: str = '', text: str = '', parent=None):
        super().__init__(parent)
        self._title_lbl = SubtitleLabel(title, self.widget)
        self._edit = LineEdit(self.widget)
        self._edit.setText(text)
        self._edit.setPlaceholderText(placeholder)
        self._edit.setClearButtonEnabled(True)
        self.viewLayout.addWidget(self._title_lbl)
        self.viewLayout.addWidget(self._edit)
        self.widget.setMinimumWidth(350)

    def value(self) -> str:
        return self._edit.text()


class HomePage(QWidget):
    """首页 - 项目列表/新建/打开"""

    project_created = Signal(str)  # 项目创建/打开后信号
    project_opened = Signal(str)  # 项目打开后信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._title = None
        self._subtitle = None
        self._recent_label = None
        self._no_recent = None
        self._new_btn = None
        self._open_btn = None
        self._recent_scroll = None
        self._recent_items_widget = None
        self._recent_items_layout = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        # 左侧边距需要足够大，避免被导航栏遮挡
        layout.setContentsMargins(40, 40, 40, 40)

        # 标题
        self._title = BodyLabel("PyLine", self)
        self._title.setStyleSheet("font-size: 48px; font-weight: bold;")
        layout.addWidget(self._title, alignment=Qt.AlignCenter)

        # 副标题
        self._subtitle = BodyLabel("曲线数据提取工具", self)
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

        self._open_btn = PrimaryPushButton("打开项目", self)
        self._open_btn.setFixedWidth(150)
        self._open_btn.clicked.connect(self.on_open_project)
        btn_layout.addWidget(self._open_btn)

        layout.addLayout(btn_layout)
        btn_layout.setAlignment(Qt.AlignCenter)

        # 最近项目
        layout.addSpacing(40)
        recent_header = QHBoxLayout()
        self._recent_label = BodyLabel("最近项目", self)
        self._recent_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        recent_header.addWidget(self._recent_label)
        recent_header.addStretch()
        layout.addLayout(recent_header)

        # 无最近项目占位
        self._no_recent = BodyLabel("暂无最近项目", self)
        self._no_recent.setStyleSheet("font-style: italic;")
        layout.addWidget(self._no_recent, alignment=Qt.AlignLeft)

        # 最近项目scroll区域
        self._recent_scroll = SmoothScrollArea(self)
        self._recent_scroll.setWidgetResizable(True)
        self._recent_scroll.setFrameShape(QFrame.NoFrame)
        self._recent_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._recent_scroll.setMaximumHeight(280)
        self._recent_scroll.hide()

        self._recent_items_widget = QWidget()
        self._recent_items_layout = QVBoxLayout(self._recent_items_widget)
        self._recent_items_layout.setSpacing(4)
        self._recent_items_layout.setContentsMargins(0, 0, 0, 0)
        self._recent_items_layout.addStretch()
        self._recent_scroll.setWidget(self._recent_items_widget)
        self._recent_scroll.setStyleSheet("SmoothScrollArea { background: transparent; border: none; }")
        self._recent_items_widget.setStyleSheet("background: transparent;")
        layout.addWidget(self._recent_scroll)

        layout.addStretch()

        # 初始应用主题颜色 & 加载最近项目
        self._apply_theme_colors()
        self.refresh_recent()

    def showEvent(self, event):
        """页面显示时刷新最近项目"""
        super().showEvent(event)
        self.refresh_recent()

    def _apply_theme_colors(self):
        """应用当前主题颜色"""
        tc = text_color()
        sc = secondary_color()
        pc = placeholder_color()
        self._title.setStyleSheet(f"font-size: 48px; font-weight: bold; color: {tc};")
        self._subtitle.setStyleSheet(f"font-size: 18px; color: {sc};")
        self._recent_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {tc};")
        self._no_recent.setStyleSheet(f"color: {pc}; font-style: italic;")

    def refresh_recent(self):
        """刷新最近项目列表"""
        recents = load_recent()

        if not recents:
            self._no_recent.show()
            self._recent_scroll.hide()
            return

        self._no_recent.hide()
        self._recent_scroll.show()

        # 清除旧条目（保留 stretch）
        while self._recent_items_layout.count() > 1:
            item = self._recent_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tc = text_color()
        sc = secondary_color()
        pc = placeholder_color()

        for entry in recents:
            path = entry.get("path", "")
            name = entry.get("name", "未知项目")
            opened_at = entry.get("opened_at", "")[:10]

            row = QWidget()
            row.setFixedHeight(54)
            row.setStyleSheet(
                f"QWidget {{border-radius: 6px; background: transparent;}}"
                f"QWidget:hover {{background: rgba(128,128,128,0.12);}}"
            )
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 4, 8, 4)
            row_layout.setSpacing(12)

            info_col = QVBoxLayout()
            info_col.setSpacing(2)
            name_lbl = BodyLabel(name)
            name_lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {tc};")
            path_lbl = BodyLabel(path)
            path_lbl.setStyleSheet(f"font-size: 11px; color: {pc};")
            path_lbl.setToolTip(path)
            info_col.addWidget(name_lbl)
            info_col.addWidget(path_lbl)
            row_layout.addLayout(info_col, 1)

            date_lbl = BodyLabel(opened_at)
            date_lbl.setStyleSheet(f"font-size: 11px; color: {sc};")
            date_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_layout.addWidget(date_lbl)

            remove_btn = PushButton("", row)
            remove_btn.setFixedSize(24, 24)
            remove_btn.setIcon(FIF.CLOSE.icon())
            remove_btn.setStyleSheet("border: none; background: transparent;")
            remove_btn.setToolTip("从列表移除")
            remove_btn.clicked.connect(lambda _, p=path: self._on_remove_recent(p))
            row_layout.addWidget(remove_btn)

            # 点击行打开项目（排除删除按钮区域）
            row.mousePressEvent = lambda e, p=path: self._on_open_recent(p)
            row.setCursor(Qt.PointingHandCursor)

            self._recent_items_layout.insertWidget(
                self._recent_items_layout.count() - 1, row
            )

    def _on_open_recent(self, path: str):
        """打开最近项目"""
        import os
        if not os.path.exists(path):
            InfoBar.warning(title="文件不存在", content=f"项目文件已移动或删除:\n{path}", parent=self, duration=5000)
            remove_recent(path)
            self.refresh_recent()
            return
        try:
            project_manager.open(path)
            self.project_opened.emit(path)
        except Exception as e:
            InfoBar.error(title="错误", content=f"无法打开项目:\n{str(e)}", parent=self, duration=5000)

    def _on_remove_recent(self, path: str):
        """从最近列表移除"""
        remove_recent(path)
        self.refresh_recent()

    def update_theme(self):
        """更新主题颜色（供外部调用）"""
        self._apply_theme_colors()
        self.refresh_recent()

    def on_new_project(self):
        """新建项目"""
        dlg = _InputDialog("新建项目", "请输入项目名称:", parent=self)
        if not dlg.exec():
            return
        name = dlg.value().strip()
        if name:
            base_dir = QFileDialog.getExistingDirectory(self, "选择项目保存目录", "")
            if not base_dir:
                return
            try:
                project_manager.create_new(name, parent_dir=base_dir, create_structure=True)
                self.project_created.emit(name)
            except Exception as e:
                InfoBar.error(title="错误", content=f"创建项目失败:\n{str(e)}", parent=self, duration=5000)

    def on_open_project(self):
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
                self.project_opened.emit(file_path)
            except Exception as e:
                InfoBar.error(title="错误", content=f"无法打开项目:\n{str(e)}", parent=self, duration=5000)
