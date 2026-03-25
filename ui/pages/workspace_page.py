from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QSplitter, QFileDialog, QInputDialog, QMessageBox, QTreeWidget, QTreeWidgetItem, QTabWidget, QSpinBox, QFormLayout, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont
from qfluentwidgets import CardWidget, ToolButton, LineEdit, SpinBox

from ui.theme import text_color, secondary_color, placeholder_color
from ui.widgets import ImageViewer
from ui.dialogs import CalibrationDialog
from core.project_manager import project_manager
from models.schemas import CalibrationData


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
        self._right_tabs = None
        self._image_viewer = None
        self._tool_buttons = []
        self._project_tree = None
        self._current_project_item = None
        self._current_image_item = None
        self._current_image_id = None
        self._current_curve_id = None
        self._current_curve_points = []
        self._active_tool = None  # 当前激活的工具按钮
        self.setup_ui()
        self._setup_viewer_signals()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        self._left_panel = self._create_left_panel()
        self._splitter.addWidget(self._left_panel)

        center_panel = QFrame(self)
        center_panel.setFrameShape(QFrame.Shape.StyledPanel)
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(5, 5, 5, 5)
        center_layout.setSpacing(0)

        self._image_viewer = ImageViewer(center_panel)
        self._image_viewer.image_loaded.connect(self._on_image_loaded)
        center_layout.addWidget(self._image_viewer)

        # 图片查看器工具栏 - 固定在底部靠右
        viewer_toolbar = QWidget(center_panel)
        viewer_toolbar_layout = QHBoxLayout(viewer_toolbar)
        viewer_toolbar_layout.setContentsMargins(0, 0, 5, 0)
        viewer_toolbar_layout.setSpacing(3)
        viewer_toolbar.setFixedHeight(28)
        viewer_toolbar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._show_curves_btn = ToolButton(FIF.VIEW, viewer_toolbar)
        self._show_curves_btn.setToolTip("显示/隐藏曲线")
        self._show_curves_btn.setCheckable(True)
        self._show_curves_btn.setChecked(True)
        self._show_curves_btn.clicked.connect(self._on_show_curves_toggled)
        self._show_curves_btn.setFixedSize(28, 28)
        viewer_toolbar_layout.addWidget(self._show_curves_btn)

        center_layout.addWidget(viewer_toolbar, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        self._splitter.addWidget(center_panel)

        self._right_panel = self._create_right_panel()
        self._splitter.addWidget(self._right_panel)

        self._splitter.setSizes([260, 600, 200])
        self._splitter.setStretchFactor(1, 1)

        main_layout.addWidget(self._splitter)

    def _setup_viewer_signals(self):
        self._image_viewer.calibration_complete.connect(self._on_calibration_complete)
        self._image_viewer.curve_point_added.connect(self._on_curve_point_added)
        self._image_viewer.calibration_step.connect(self._on_calibration_step)
        self._image_viewer.calibration_nudge.connect(self._on_calibration_nudge)

    def _create_left_panel(self) -> CardWidget:
        panel = CardWidget(self)
        panel.setFixedWidth(260)
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        toolbar_widget = QWidget(panel)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(2)

        self._new_project_btn = ToolButton(FIF.ADD, toolbar_widget)
        self._new_project_btn.setToolTip("新建项目")
        self._new_project_btn.clicked.connect(self._on_new_project)
        toolbar_layout.addWidget(self._new_project_btn)

        self._open_project_btn = ToolButton(FIF.FOLDER, toolbar_widget)
        self._open_project_btn.setToolTip("打开项目")
        self._open_project_btn.clicked.connect(self._on_open_project)
        toolbar_layout.addWidget(self._open_project_btn)

        self._save_project_btn = ToolButton(FIF.SAVE, toolbar_widget)
        self._save_project_btn.setToolTip("保存项目")
        self._save_project_btn.clicked.connect(self._on_save_project)
        toolbar_layout.addWidget(self._save_project_btn)

        self._close_project_btn = ToolButton(FIF.CLOSE, toolbar_widget)
        self._close_project_btn.setToolTip("关闭项目")
        self._close_project_btn.clicked.connect(self._on_close_project)
        toolbar_layout.addWidget(self._close_project_btn)

        line = QFrame(toolbar_widget)
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFixedWidth(1)
        line.setStyleSheet(f"background-color: {self._border_color()};")
        toolbar_layout.addWidget(line)

        self._add_image_btn = ToolButton(FIF.IMAGE_EXPORT, toolbar_widget)
        self._add_image_btn.setToolTip("添加图片到当前项目")
        self._add_image_btn.clicked.connect(self._on_add_image)
        toolbar_layout.addWidget(self._add_image_btn)

        self._add_curve_btn = ToolButton(FIF.PIE_SINGLE, toolbar_widget)
        self._add_curve_btn.setToolTip("添加新曲线到选中图片")
        self._add_curve_btn.clicked.connect(self._on_add_curve)
        toolbar_layout.addWidget(self._add_curve_btn)

        toolbar_layout.addStretch()
        layout.addWidget(toolbar_widget)

        self._project_tree = QTreeWidget(panel)
        self._project_tree.setHeaderHidden(True)
        self._project_tree.setIndentation(15)
        self._project_tree.setFont(QFont("Microsoft YaHei", 10))
        self._project_tree.setIconSize(QSize(20, 20))
        self._project_tree.itemClicked.connect(self._on_tree_item_clicked)
        self._project_tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        self._refresh_project_tree()
        layout.addWidget(self._project_tree)

        return panel

    def _create_right_panel(self) -> CardWidget:
        panel = CardWidget(self)
        panel.setFixedWidth(280)
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 标题
        title_label = QLabel("曲线数据", panel)
        title_label.setStyleSheet(f"font-weight: bold; color: {text_color()};")
        layout.addWidget(title_label)

        # 曲线数据表格
        self._curve_table = QTableWidget(panel)
        self._curve_table.setColumnCount(2)
        self._curve_table.setHorizontalHeaderLabels(["X", "Y"])
        self._curve_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._curve_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._curve_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._curve_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._curve_table.setFont(QFont("Microsoft YaHei", 9))
        layout.addWidget(self._curve_table)

        # 功能区标签
        func_label = QLabel("功能区", panel)
        func_label.setStyleSheet(f"font-weight: bold; color: {text_color()};")
        layout.addWidget(func_label)

        # 功能区页面
        self._right_tabs = QTabWidget(panel)
        extract_tab = self._create_extract_tab()
        self._right_tabs.addTab(extract_tab, "手动选点")

        layout.addWidget(self._right_tabs)

        return panel

    def _create_extract_tab(self) -> QWidget:
        """创建手动选点功能区"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 工具按钮区域 - 横向排列
        tools_label = QLabel("工具", tab)
        tools_label.setStyleSheet(f"font-weight: bold; color: {text_color()};")
        layout.addWidget(tools_label)

        tools_widget = QWidget(tab)
        tools_layout = QHBoxLayout(tools_widget)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(3)

        # 框选蒙版
        self._box_mask_btn = ToolButton(FIF.LAYOUT, tools_widget)
        self._box_mask_btn.setToolTip("框选蒙版")
        self._box_mask_btn.setCheckable(True)
        self._box_mask_btn.clicked.connect(lambda: self._on_tool_clicked("box_mask"))
        tools_layout.addWidget(self._box_mask_btn)

        # 涂刷蒙版
        self._brush_mask_btn = ToolButton(FIF.BRUSH, tools_widget)
        self._brush_mask_btn.setToolTip("涂刷蒙版")
        self._brush_mask_btn.setCheckable(True)
        self._brush_mask_btn.clicked.connect(lambda: self._on_tool_clicked("brush_mask"))
        tools_layout.addWidget(self._brush_mask_btn)

        # 橡皮擦
        self._eraser_btn = ToolButton(FIF.ERASE_TOOL, tools_widget)
        self._eraser_btn.setToolTip("橡皮擦")
        self._eraser_btn.setCheckable(True)
        self._eraser_btn.clicked.connect(lambda: self._on_tool_clicked("eraser"))
        tools_layout.addWidget(self._eraser_btn)

        # 校准
        self._calibrate_btn = ToolButton(FIF.ALIGNMENT, tools_widget)
        self._calibrate_btn.setToolTip("校准")
        self._calibrate_btn.setCheckable(True)
        self._calibrate_btn.clicked.connect(lambda: self._on_tool_clicked("calibrate"))
        tools_layout.addWidget(self._calibrate_btn)

        # 提取曲线
        self._extract_btn = ToolButton(FIF.PIE_SINGLE, tools_widget)
        self._extract_btn.setToolTip("提取曲线")
        self._extract_btn.setCheckable(True)
        self._extract_btn.clicked.connect(lambda: self._on_tool_clicked("extract"))
        tools_layout.addWidget(self._extract_btn)

        # 完成
        self._finish_curve_btn = ToolButton(FIF.ACCEPT, tools_widget)
        self._finish_curve_btn.setToolTip("完成")
        self._finish_curve_btn.clicked.connect(self._on_tool_finish_curve)
        tools_layout.addWidget(self._finish_curve_btn)

        layout.addWidget(tools_widget)

        # 参数设置区域 - 纵向排列，带标签和当前值
        params_label = QLabel("参数设置", tab)
        params_label.setStyleSheet(f"font-weight: bold; color: {text_color()};")
        layout.addWidget(params_label)

        params_widget = QWidget(tab)
        params_layout = QVBoxLayout(params_widget)
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(8)

        # 点大小
        point_size_row = QWidget(tab)
        point_size_layout = QHBoxLayout(point_size_row)
        point_size_layout.setContentsMargins(0, 0, 0, 0)
        point_size_layout.setSpacing(5)
        point_size_label = QLabel("点大小:", tab)
        point_size_label.setFixedWidth(60)
        self._point_size_spin = SpinBox(tab)
        self._point_size_spin.setRange(1, 50)
        self._point_size_spin.setValue(8)
        self._point_size_spin.setToolTip("曲线点大小")
        self._point_size_spin.setMaximumWidth(80)
        self._point_size_spin.valueChanged.connect(self._on_point_size_changed)
        point_size_layout.addWidget(point_size_label)
        point_size_layout.addWidget(self._point_size_spin)
        self._point_size_value_label = QLabel("8 px", tab)
        self._point_size_value_label.setStyleSheet(f"color: {placeholder_color()};")
        point_size_layout.addWidget(self._point_size_value_label)
        point_size_layout.addStretch()
        params_layout.addWidget(point_size_row)

        # 微调步长
        nudge_step_row = QWidget(tab)
        nudge_step_layout = QHBoxLayout(nudge_step_row)
        nudge_step_layout.setContentsMargins(0, 0, 0, 0)
        nudge_step_layout.setSpacing(5)
        nudge_step_label = QLabel("微调步长:", tab)
        nudge_step_label.setFixedWidth(60)
        self._nudge_step_spin = SpinBox(tab)
        self._nudge_step_spin.setRange(1, 20)
        self._nudge_step_spin.setValue(3)
        self._nudge_step_spin.setToolTip("方向键微调步长(像素)")
        self._nudge_step_spin.setMaximumWidth(80)
        self._nudge_step_spin.valueChanged.connect(self._on_nudge_step_changed)
        nudge_step_layout.addWidget(nudge_step_label)
        nudge_step_layout.addWidget(self._nudge_step_spin)
        self._nudge_step_value_label = QLabel("3 px", tab)
        self._nudge_step_value_label.setStyleSheet(f"color: {placeholder_color()};")
        nudge_step_layout.addWidget(self._nudge_step_value_label)
        nudge_step_layout.addStretch()
        params_layout.addWidget(nudge_step_row)

        # 橡皮大小
        eraser_size_row = QWidget(tab)
        eraser_size_layout = QHBoxLayout(eraser_size_row)
        eraser_size_layout.setContentsMargins(0, 0, 0, 0)
        eraser_size_layout.setSpacing(5)
        eraser_size_label = QLabel("橡皮大小:", tab)
        eraser_size_label.setFixedWidth(60)
        self._eraser_size_spin = SpinBox(tab)
        self._eraser_size_spin.setRange(1, 100)
        self._eraser_size_spin.setValue(20)
        self._eraser_size_spin.setToolTip("橡皮擦大小")
        self._eraser_size_spin.setMaximumWidth(80)
        self._eraser_size_spin.valueChanged.connect(self._on_eraser_size_changed)
        eraser_size_layout.addWidget(eraser_size_label)
        eraser_size_layout.addWidget(self._eraser_size_spin)
        self._eraser_size_value_label = QLabel("20 px", tab)
        self._eraser_size_value_label.setStyleSheet(f"color: {placeholder_color()};")
        eraser_size_layout.addWidget(self._eraser_size_value_label)
        eraser_size_layout.addStretch()
        params_layout.addWidget(eraser_size_row)

        layout.addWidget(params_widget)

        # 提示标签
        self._status_label = QLabel("", tab)
        self._status_label.setStyleSheet(f"color: {placeholder_color()}; font-size: 11px;")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        layout.addStretch()

        return tab

    def _border_color(self):
        from qfluentwidgets import isDarkTheme
        return "#3d3d3d" if isDarkTheme() else "#e0e0e0"

    def _selection_background_color(self):
        from qfluentwidgets import isDarkTheme
        return "#3d5a80" if isDarkTheme() else "#b8d4f0"

    def _update_curve_table(self):
        """更新曲线数据表格 - 显示选中曲线的实时数据"""
        self._curve_table.setRowCount(0)

        # 如果有选中的曲线，显示该曲线的数据
        if self._current_curve_id:
            curve = project_manager.get_curve(self._current_curve_id)
            if curve and curve.x_data:
                for i in range(len(curve.x_data)):
                    row = self._curve_table.rowCount()
                    self._curve_table.insertRow(row)

                    x_item = QTableWidgetItem(f"{curve.x_data[i]:.4f}")
                    y_item = QTableWidgetItem(f"{curve.y_data[i]:.4f}")
                    self._curve_table.setItem(row, 0, x_item)
                    self._curve_table.setItem(row, 1, y_item)
        elif self._current_image_id:
            # 如果没有选中曲线但有选中图片，显示该图片所有曲线的数据预览
            img = project_manager.get_image(self._current_image_id)
            if img:
                for curve in img.curves:
                    for i in range(len(curve.x_data)):
                        row = self._curve_table.rowCount()
                        self._curve_table.insertRow(row)

                        x_item = QTableWidgetItem(f"{curve.x_data[i]:.4f}")
                        y_item = QTableWidgetItem(f"{curve.y_data[i]:.4f}")
                        self._curve_table.setItem(row, 0, x_item)
                        self._curve_table.setItem(row, 1, y_item)

    def _refresh_project_tree(self):
        self._project_tree.clear()

        current_img_id = self._current_image_id
        current_curve_id = self._current_curve_id

        for project in project_manager.projects:
            project_item = QTreeWidgetItem(self._project_tree)
            project_item.setText(0, f"📁 {project.name}")
            project_item.setData(0, Qt.ItemDataRole.UserRole, ("project", project.id))
            project_item.setExpanded(True)

            if project.id == project_manager.current_project_id:
                font = project_item.font(0)
                font.setBold(True)
                project_item.setFont(0, font)
                self._current_project_item = project_item
                from PySide6.QtGui import QBrush, QColor
                bg_color = QColor(self._selection_background_color())
                project_item.setBackground(0, QBrush(bg_color))

            for img in project.images:
                img_item = QTreeWidgetItem(project_item)
                img_item.setText(0, f"🖼️ {img.name}")
                img_item.setData(0, Qt.ItemDataRole.UserRole, ("image", img.id, project.id))
                img_item.setExpanded(True)
                if img.id == current_img_id:
                    from PySide6.QtGui import QBrush, QColor
                    bg_color = QColor(self._selection_background_color())
                    img_item.setBackground(0, QBrush(bg_color))

                # 图片的曲线作为图片的子节点
                for curve in img.curves:
                    curve_item = QTreeWidgetItem(img_item)
                    curve_item.setText(0, f"📈 {curve.name}")
                    curve_item.setData(0, Qt.ItemDataRole.UserRole, ("curve", curve.id, project.id, img.id))
                    if curve.id == current_curve_id:
                        from PySide6.QtGui import QBrush, QColor
                        bg_color = QColor(self._selection_background_color())
                        curve_item.setBackground(0, QBrush(bg_color))

            # 项目级别的导入曲线
            for curve in project.imported_curves:
                curve_item = QTreeWidgetItem(project_item)
                curve_item.setText(0, f"📈 {curve.name}")
                curve_item.setData(0, Qt.ItemDataRole.UserRole, ("curve", curve.id, project.id))
                if curve.id == current_curve_id:
                    from PySide6.QtGui import QBrush, QColor
                    bg_color = QColor(self._selection_background_color())
                    curve_item.setBackground(0, QBrush(bg_color))

    def _on_tool_clicked(self, tool_name: str):
        """处理工具按钮点击"""
        if self._active_tool == tool_name:
            # 取消当前工具
            self._deactivate_all_tools()
            self._image_viewer.set_select_mode()
            self._active_tool = None
            self._status_label.setText("")
            return

        self._deactivate_all_tools()

        if tool_name == "calibrate":
            # 校准需要选中一个曲线
            if self._current_curve_id is None:
                QMessageBox.warning(self, "警告", "请先选择一个曲线进行校准")
                return
            self._activate_tool_button(self._calibrate_btn)
            self._image_viewer.set_calibrate_mode()
            self._active_tool = tool_name
            self._current_curve_points = []
            self._status_label.setText("请依次点击X轴起点、X轴终点、Y轴起点、Y轴终点")
        elif tool_name == "extract":
            # 提取曲线需要先选择或创建一个曲线
            if self._current_image_id is None:
                QMessageBox.warning(self, "警告", "请先选择一张图片")
                self._deactivate_all_tools()
                return
            self._activate_tool_button(self._extract_btn)
            self._image_viewer.set_extract_mode()
            self._active_tool = tool_name
            self._current_curve_points = []
            self._status_label.setText("点击图片选取曲线点，使用方向键或WASD微调")
        else:
            self._image_viewer.set_select_mode()
            self._active_tool = None
            self._status_label.setText("")

    def _activate_tool_button(self, btn):
        """激活工具按钮"""
        btn.setChecked(True)

    def _deactivate_all_tools(self):
        """取消所有工具按钮的激活状态"""
        self._box_mask_btn.setChecked(False)
        self._brush_mask_btn.setChecked(False)
        self._eraser_btn.setChecked(False)
        self._calibrate_btn.setChecked(False)
        self._extract_btn.setChecked(False)

    def _on_point_size_changed(self, value):
        self._image_viewer.set_point_size(float(value))
        self._point_size_value_label.setText(f"{value} px")

    def _on_nudge_step_changed(self, value):
        self._image_viewer.set_nudge_step(float(value))
        self._nudge_step_value_label.setText(f"{value} px")

    def _on_eraser_size_changed(self, value):
        self._eraser_size_value_label.setText(f"{value} px")

    def _on_tree_item_clicked(self, item, column):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None:
            return

        item_type = data[0]

        # 清除图片上的曲线显示（会在子节点处理中重新添加）
        self._image_viewer.clear_curves()

        if item_type == "project":
            project_id = data[1]
            project_manager.set_current_project(project_id)
            self._current_project_item = item
            self._current_image_id = None
            self._current_curve_id = None
            self._refresh_project_tree()
        elif item_type == "image":
            project_id = data[2]
            project_manager.set_current_project(project_id)
            project = project_manager.get_project(project_id)
            if project:
                img_id = data[1]
                for img in project.images:
                    if img.id == img_id:
                        self._image_viewer.load_image(img.image_path)
                        self._current_image_item = item
                        self._current_image_id = img_id
                        self._current_curve_id = None
                        self._update_curve_table()
                        self._refresh_project_tree()
                        self.current_image_changed.emit(img)
                        break
        elif item_type == "curve":
            curve_id = data[1]
            curve = project_manager.get_curve(curve_id)
            if curve is None:
                return

            self._current_curve_id = curve_id
            # 如果有image_id，说明是图片的子节点
            if len(data) >= 4:
                self._current_image_id = data[3]
                # 加载对应的图片
                project_id = data[2]
                project = project_manager.get_project(project_id)
                if project:
                    for img in project.images:
                        if img.id == self._current_image_id:
                            self._image_viewer.load_image(img.image_path)
                            break
            else:
                self._current_image_id = None

            # 清除图片上的曲线，只显示当前选中的
            self._image_viewer.clear_curves()
            self._display_curve_on_image(curve)
            self._update_curve_table()
            self._refresh_project_tree()

    def _on_tree_item_double_clicked(self, item, column):
        pass

    def _on_show_curves_toggled(self, checked):
        """显示/隐藏曲线切换"""
        if checked:
            self._image_viewer.set_curves_visible(True)
            self._show_curves_btn.setIcon(FIF.VIEW)
        else:
            self._image_viewer.set_curves_visible(False)
            self._show_curves_btn.setIcon(FIF.HIDE)

    def _display_curve_on_image(self, curve):
        """在图片查看器上显示曲线的点"""
        from ui.widgets.image_viewer import CurveOverlayItem

        if curve and curve.x_data and curve.y_data:
            curve_item = CurveOverlayItem(color=curve.color)
            curve_item.name = curve.name

            # 获取曲线的校准数据（如果有）
            calib = curve.calibration

            # 如果有校准数据，将实际坐标转换为像素坐标显示
            if calib:
                # 需要反向转换：将实际坐标转回像素坐标
                # 这需要根据校准数据计算
                for i in range(len(curve.x_data)):
                    x_actual = curve.x_data[i]
                    y_actual = curve.y_data[i]

                    # 计算x像素坐标
                    x_ratio = (x_actual - calib.x_range[0]) / (calib.x_range[1] - calib.x_range[0])
                    x_start = calib.x_start
                    x_end = calib.x_end
                    dx = x_end[0] - x_start[0]
                    dy_x = x_end[1] - x_start[1]

                    if abs(dx) > abs(dy_x):
                        px = x_start[0] + x_ratio * dx
                    else:
                        if dy_x != 0:
                            px = x_start[1] + x_ratio * dy_x
                        else:
                            px = x_start[0]

                    # 计算y像素坐标
                    y_ratio = (calib.y_range[1] - y_actual) / (calib.y_range[1] - calib.y_range[0])
                    y_start = calib.y_start
                    y_end = calib.y_end
                    dx_y = y_end[0] - y_start[0]
                    dy = y_end[1] - y_start[1]

                    if abs(dx_y) > abs(dy):
                        py = y_start[0] + y_ratio * dx_y
                    else:
                        if dy != 0:
                            py = y_start[1] + y_ratio * dy
                        else:
                            py = y_start[1]

                    curve_item.add_point(px, py)
            else:
                # 没有校准数据，直接使用原始数据作为像素坐标
                for i in range(len(curve.x_data)):
                    curve_item.add_point(curve.x_data[i], curve.y_data[i])

            self._image_viewer.add_curve_item(curve_item)

    def _on_new_project(self):
        name, ok = QInputDialog.getText(self, "新建项目", "请输入项目名称:")
        if ok and name:
            project_manager.create_new(name)
            self._refresh_project_tree()
            self.project_modified.emit()

    def _on_open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开项目", "", "PyLine 项目 (*.pyline);;所有文件 (*)"
        )
        if file_path:
            try:
                project_manager.open(file_path)
                self._refresh_project_tree()
                self.project_modified.emit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开项目:\n{str(e)}")

    def _on_save_project(self):
        if project_manager.current_project is None:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
            return

        file_path = project_manager.current_project.file_path
        if file_path is None:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存项目", f"{project_manager.current_project.name}.pyline", "PyLine 项目 (*.pyline)"
            )

        if file_path:
            try:
                project_manager.save(file_path)
                self._refresh_project_tree()
                QMessageBox.information(self, "成功", f"项目已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")

    def _on_close_project(self):
        if project_manager.current_project is None:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
            return

        if project_manager.current_project.is_modified:
            reply = QMessageBox.question(
                self, "项目已修改", "当前项目有未保存的更改，是否保存？",
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
        if project_manager.current_project is None:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;所有文件 (*)"
        )
        if file_path:
            image_work = project_manager.add_image(file_path)
            self._current_image_id = image_work.id
            self._current_curve_id = None
            self._image_viewer.load_image(file_path)
            self._refresh_project_tree()
            self.project_modified.emit()

    def _on_add_curve(self):
        """为当前选中图片添加新曲线"""
        if self._current_image_id is None:
            QMessageBox.warning(self, "警告", "请先选择一张图片")
            return

        img = project_manager.get_image(self._current_image_id)
        if img is None:
            return

        # 创建新曲线
        curve = project_manager.add_curve_to_image(
            self._current_image_id,
            x_data=[],
            y_data=[],
            name=f"曲线 {len(img.curves) + 1}"
        )

        if curve:
            self._current_curve_id = curve.id
            self._refresh_project_tree()
            self.project_modified.emit()

    def _on_image_loaded(self, file_path: str):
        # 清除图片上的曲线
        self._image_viewer.clear_curves()

        # 只显示当前选中的曲线
        if self._current_curve_id:
            curve = project_manager.get_curve(self._current_curve_id)
            if curve:
                self._display_curve_on_image(curve)

        self._update_curve_table()
        self._refresh_project_tree()

    def load_image(self, file_path: str) -> bool:
        if self._image_viewer:
            return self._image_viewer.load_image(file_path)
        return False

    def update_theme_colors(self):
        pass

    # ==================== 校准和曲线提取 ====================

    def _on_calibration_complete(self, calibration_overlay):
        if self._current_curve_id is None:
            return

        dialog = CalibrationDialog(calibration_overlay, self)
        if dialog.exec():
            data = dialog.get_calibration_data()

            calib_data = CalibrationData(
                x_start=(calibration_overlay.x_start.x(), calibration_overlay.x_start.y()),
                x_end=(calibration_overlay.x_end.x(), calibration_overlay.x_end.y()),
                y_start=(calibration_overlay.y_start.x(), calibration_overlay.y_start.y()),
                y_end=(calibration_overlay.y_end.x(), calibration_overlay.y_end.y()),
                x_range=data["x_range"],
                y_range=data["y_range"],
                coord_type=data["coord_type"]
            )

            project_manager.update_curve_calibration(self._current_curve_id, calib_data)
            self._deactivate_all_tools()
            self._active_tool = None
            self._image_viewer.set_select_mode()
            self._status_label.setText("校准完成！")
            self._refresh_project_tree()
            self.project_modified.emit()

    def _on_calibration_step(self, step_type: str):
        step_hints = {
            "x_start": "请点击X轴起点",
            "x_end": "请点击X轴终点",
            "y_start": "请点击Y轴起点",
            "y_end": "请点击Y轴终点",
            "complete": "校准完成！"
        }
        self._status_label.setText(step_hints.get(step_type, ""))

    def _on_calibration_nudge(self, dx: float, dy: float):
        pass

    def _on_curve_point_added(self, px: float, py: float):
        if self._current_image_id is None:
            return
        self._current_curve_points.append((px, py))
        self._status_label.setText(f"已选取 {len(self._current_curve_points)} 个点")

    def _on_tool_finish_curve(self):
        if not self._current_curve_points or self._current_image_id is None:
            return

        img = project_manager.get_image(self._current_image_id)
        if img is None:
            return

        x_data = []
        y_data = []

        # 如果有选中的曲线，使用该曲线的校准数据
        curve_id = self._current_curve_id if self._current_curve_id else None

        for px, py in self._current_curve_points:
            if curve_id:
                x, y = project_manager.pixel_to_actual_coords(curve_id, px, py)
            else:
                x, y = px, py
            x_data.append(x)
            y_data.append(y)

        # 如果有选中曲线，添加到该曲线；否则创建新曲线
        if self._current_curve_id:
            curve = project_manager.get_curve(self._current_curve_id)
            if curve:
                curve.x_data = x_data
                curve.y_data = y_data
        else:
            curve = project_manager.add_curve_to_image(
                self._current_image_id, x_data, y_data, name=f"曲线 {len(img.curves) + 1}"
            )

        if curve:
            self._deactivate_all_tools()
            self._active_tool = None
            self._image_viewer.set_select_mode()
            self._current_curve_points = []
            self._status_label.setText("曲线已保存！")
            self._update_curve_table()
            self._refresh_project_tree()
            self.project_modified.emit()


# 需要导入 FIF
from qfluentwidgets.common.icon import FluentIcon as FIF
