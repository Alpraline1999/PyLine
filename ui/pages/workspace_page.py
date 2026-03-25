from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QSplitter, QFileDialog, QInputDialog, QMessageBox, QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import CardWidget, ToolButton

from ui.theme import text_color, secondary_color, placeholder_color
from ui.widgets import ImageViewer
from core.project_manager import project_manager


class WorkspacePage(QWidget):
    """工作区页面 - 主功能区"""

    project_modified = Signal()  # 项目修改信号
    current_project_changed = Signal(object)  # 当前项目切换信号
    current_image_changed = Signal(object)  # 当前图片切换信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._splitter = None
        self._left_panel = None
        self._right_panel = None
        self._image_viewer = None
        self._tool_buttons = []
        self._project_tree = None
        self._current_project_item = None
        self._current_image_item = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 使用 QSplitter 实现可拖动的分割
        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧面板（项目树）
        self._left_panel = self._create_left_panel()
        self._splitter.addWidget(self._left_panel)

        # 中间区域（图片查看器）
        center_panel = QFrame(self)
        center_panel.setFrameShape(QFrame.Shape.StyledPanel)
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(5, 5, 5, 5)

        # 图片查看器（直接填满，无标题）
        self._image_viewer = ImageViewer(center_panel)
        self._image_viewer.image_loaded.connect(self._on_image_loaded)
        center_layout.addWidget(self._image_viewer)

        # 底部工具栏
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

        # 设置分割比例
        self._splitter.setSizes([260, 600, 200])
        self._splitter.setStretchFactor(1, 1)

        main_layout.addWidget(self._splitter)

    def _create_left_panel(self) -> CardWidget:
        """创建左侧面板"""
        panel = CardWidget(self)
        panel.setFixedWidth(260)
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 工具按钮区域
        toolbar_widget = QWidget(panel)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(2)

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

        # 分隔线
        line = QFrame(toolbar_widget)
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFixedWidth(1)
        line.setStyleSheet(f"background-color: {self._border_color()};")
        toolbar_layout.addWidget(line)

        # 添加图片按钮
        self._add_image_btn = ToolButton(FIF.CAMERA, toolbar_widget)
        self._add_image_btn.setToolTip("添加图片到当前项目")
        self._add_image_btn.clicked.connect(self._on_add_image)
        toolbar_layout.addWidget(self._add_image_btn)

        toolbar_layout.addStretch()
        layout.addWidget(toolbar_widget)

        # 项目树
        self._project_tree = QTreeWidget(panel)
        self._project_tree.setHeaderHidden(True)
        self._project_tree.setIndentation(15)
        self._project_tree.itemClicked.connect(self._on_tree_item_clicked)
        self._project_tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        self._refresh_project_tree()
        layout.addWidget(self._project_tree)

        return panel

    def _border_color(self):
        """获取边框颜色"""
        from qfluentwidgets import isDarkTheme
        return "#3d3d3d" if isDarkTheme() else "#e0e0e0"

    def _refresh_project_tree(self):
        """刷新项目树"""
        self._project_tree.clear()

        # 添加所有项目
        for project in project_manager.projects:
            # 项目节点
            project_item = QTreeWidgetItem(self._project_tree)
            project_item.setText(0, f"📁 {project.name}")
            project_item.setData(0, Qt.ItemDataRole.UserRole, ("project", project.id))
            project_item.setExpanded(True)

            # 如果是当前项目，高亮显示
            if project.id == project_manager.current_project_id:
                font = project_item.font(0)
                font.setBold(True)
                project_item.setFont(0, font)
                self._current_project_item = project_item

            # 图片子节点
            for img in project.images:
                img_item = QTreeWidgetItem(project_item)
                img_item.setText(0, f"🖼️ {img.name}")
                img_item.setData(0, Qt.ItemDataRole.UserRole, ("image", img.id, project.id))

            # 曲线子节点
            for curve in project.imported_curves:
                curve_item = QTreeWidgetItem(project_item)
                curve_item.setText(0, f"📈 {curve.name}")
                curve_item.setData(0, Qt.ItemDataRole.UserRole, ("curve", curve.id, project.id))

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

    def _on_tree_item_clicked(self, item, column):
        """树节点点击"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None:
            return

        item_type = data[0]
        if item_type == "project":
            # 点击项目，设置为当前项目
            project_id = data[1]
            project_manager.set_current_project(project_id)
            self._current_project_item = item
            self._refresh_project_tree()
        elif item_type == "image":
            # 点击图片，加载到查看器
            project_id = data[2]
            project = project_manager.get_project(project_id)
            if project:
                img_id = data[1]
                for img in project.images:
                    if img.id == img_id:
                        self._image_viewer.load_image(img.image_path)
                        self._current_image_item = item
                        self.current_image_changed.emit(img)
                        break

    def _on_tree_item_double_clicked(self, item, column):
        """树节点双击"""
        # 预留：双击编辑
        pass

    def _on_new_project(self):
        """新建项目"""
        name, ok = QInputDialog.getText(self, "新建项目", "请输入项目名称:")
        if ok and name:
            project_manager.create_new(name)
            self._refresh_project_tree()
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
                self._refresh_project_tree()
                self.project_modified.emit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开项目:\n{str(e)}")

    def _on_save_project(self):
        """保存项目"""
        if project_manager.current_project is None:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
            return

        file_path = project_manager.current_project.file_path
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
                self._refresh_project_tree()
                QMessageBox.information(self, "成功", f"项目已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")

    def _on_close_project(self):
        """关闭项目"""
        if project_manager.current_project is None:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
            return

        # 检查是否有未保存的更改
        if project_manager.current_project.is_modified:
            reply = QMessageBox.question(
                self,
                "项目已修改",
                "当前项目有未保存的更改，是否保存？",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self._on_save_project()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        project_manager.close_current_project()
        self._image_viewer.clear_image()
        self._refresh_project_tree()
        self.project_modified.emit()

    def _on_add_image(self):
        """添加图片到当前项目"""
        if project_manager.current_project is None:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;所有文件 (*)"
        )
        if file_path:
            project_manager.add_image(file_path)
            self._image_viewer.load_image(file_path)
            self._refresh_project_tree()
            self.project_modified.emit()

    def _on_image_loaded(self, file_path: str):
        """图片加载完成"""
        self._refresh_project_tree()

    def load_image(self, file_path: str) -> bool:
        """加载图片到查看器"""
        if self._image_viewer:
            return self._image_viewer.load_image(file_path)
        return False

    def update_theme_colors(self):
        """更新主题颜色（供外部调用）"""
        for btn in self._tool_buttons:
            btn.setStyleSheet(f"padding: 5px 10px; color: {text_color()}; background-color: {secondary_color()}; border-radius: 3px;")


# 需要导入 FIF
from qfluentwidgets.common.icon import FluentIcon as FIF
