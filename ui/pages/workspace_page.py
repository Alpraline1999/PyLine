from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QSplitter, QFileDialog, QInputDialog, QMessageBox, QTreeWidget, QTreeWidgetItem, QTabWidget, QSpinBox, QFormLayout, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMenu
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor
from qfluentwidgets import CardWidget, ToolButton, LineEdit, SpinBox

from ui.theme import text_color, secondary_color, placeholder_color
from ui.widgets import ImageViewer
from ui.dialogs import CalibrationDialog, CoordTypeDialog, PolarCalibrationDialog
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
        self._hidden_curves = set()  # 隐藏的曲线ID集合
        # 撤销/重做系统
        self._undo_stack = []  #撤销栈
        self._redo_stack = []  #重做栈
        self._max_history = 50  #最大历史记录数
        self._is_undo_redo = False  #防止在撤销/重做中重复记录
        self.setup_ui()
        self._setup_viewer_signals()
        self._setup_shortcuts()
        # 初始化点大小
        self._image_viewer.set_point_size(self._point_size_spin.value())

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
        self._image_viewer.eraser_point.connect(self._on_eraser_point)
        self._image_viewer.toggle_eraser_mode.connect(self._on_toggle_eraser_mode)
        self._image_viewer.mask_changed.connect(self._on_mask_changed)
        self._image_viewer.mask_about_to_add.connect(self._on_mask_about_to_add)

    def _setup_shortcuts(self):
        """设置键盘快捷键"""
        from PySide6.QtGui import QShortcut, QKeySequence
        # Ctrl+Z 撤销
        self._undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self._undo_shortcut.activated.connect(self._undo)
        # Ctrl+Y 重做
        self._redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        self._redo_shortcut.activated.connect(self._redo)

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
        self._project_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._project_tree.customContextMenuRequested.connect(self._on_tree_context_menu)
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
        auto_extract_tab = self._create_auto_extract_tab()
        self._right_tabs.addTab(auto_extract_tab, "自动选点")

        layout.addWidget(self._right_tabs)

        # 公用工具区
        self._common_tools_widget = self._create_common_tools_widget(panel)
        layout.addWidget(self._common_tools_widget)

        # 提示标签
        self._status_label = QLabel("", panel)
        self._status_label.setStyleSheet(f"color: {placeholder_color()}; font-size: 11px;")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        return panel

    def _create_common_tools_widget(self, parent) -> QWidget:
        """创建公用工具区域"""
        from qfluentwidgets import TransparentTogglePushButton, PushButton

        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(8)

        # 工具按钮行 - 橡皮擦和排序
        tools_widget = QWidget(widget)
        tools_layout = QHBoxLayout(tools_widget)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(5)

        # 橡皮擦
        self._eraser_btn = TransparentTogglePushButton("橡皮擦", tools_widget)
        self._eraser_btn.setIcon(FIF.ERASE_TOOL)
        self._eraser_btn.setToolTip("橡皮擦")
        self._eraser_btn.setCheckable(True)
        self._eraser_btn.clicked.connect(lambda: self._on_tool_clicked("eraser"))
        tools_layout.addWidget(self._eraser_btn)

        # 按X排序
        self._sort_x_btn = PushButton("X", tools_widget)
        self._sort_x_btn.setIcon(FIF.DOWN)
        self._sort_x_btn.setToolTip("按X坐标排序")
        self._sort_x_btn.clicked.connect(self._on_sort_by_x)
        tools_layout.addWidget(self._sort_x_btn)

        # 按Y排序
        self._sort_y_btn = PushButton("Y", tools_widget)
        self._sort_y_btn.setIcon(FIF.DOWN)
        self._sort_y_btn.setToolTip("按Y坐标排序")
        self._sort_y_btn.clicked.connect(self._on_sort_by_y)
        tools_layout.addWidget(self._sort_y_btn)

        tools_layout.addStretch()
        layout.addWidget(tools_widget)

        # 操作按钮行 - 清除、撤销、重做
        ops_widget = QWidget(widget)
        ops_layout = QHBoxLayout(ops_widget)
        ops_layout.setContentsMargins(0, 0, 0, 0)
        ops_layout.setSpacing(5)

        # 清除所有点
        self._clear_points_btn = PushButton("清除", ops_widget)
        self._clear_points_btn.setIcon(FIF.DELETE)
        self._clear_points_btn.setToolTip("清除所有点")
        self._clear_points_btn.clicked.connect(self._on_clear_all_points)
        ops_layout.addWidget(self._clear_points_btn)

        # 撤销
        self._undo_btn = ToolButton(FIF.LEFT_ARROW, ops_widget)
        self._undo_btn.setToolTip("撤销 (Ctrl+Z)")
        self._undo_btn.clicked.connect(self._undo)
        ops_layout.addWidget(self._undo_btn)

        # 重做
        self._redo_btn = ToolButton(FIF.RIGHT_ARROW, ops_widget)
        self._redo_btn.setToolTip("重做 (Ctrl+Y)")
        self._redo_btn.clicked.connect(self._redo)
        ops_layout.addWidget(self._redo_btn)

        ops_layout.addStretch()
        layout.addWidget(ops_widget)

        # 颜色和形状行
        style_row = QWidget(widget)
        style_layout = QHBoxLayout(style_row)
        style_layout.setContentsMargins(0, 0, 0, 0)
        style_layout.setSpacing(5)

        # 颜色选择
        color_label = QLabel("颜色:", style_row)
        color_label.setFixedWidth(40)
        style_layout.addWidget(color_label)

        from qfluentwidgets import ColorPickerButton
        self._color_btn = ColorPickerButton(QColor("#0078D4"), "", widget)
        self._color_btn.setToolTip("曲线颜色")
        self._color_btn.setFixedSize(32, 32)
        self._color_btn.colorChanged.connect(self._on_color_changed)
        style_layout.addWidget(self._color_btn)

        # 形状选择
        shape_label = QLabel("形状:", style_row)
        shape_label.setFixedWidth(40)
        style_layout.addWidget(shape_label)

        self._shape_combo = QComboBox(style_row)
        self._shape_combo.addItems(["圆形", "方形", "三角形", "菱形", "倒三角", "叉号", "星号"])
        self._shape_combo.setToolTip("曲线点形状")
        self._shape_combo.setFixedWidth(70)
        self._shape_combo.currentIndexChanged.connect(self._on_shape_changed)
        style_layout.addWidget(self._shape_combo)

        style_layout.addStretch()
        layout.addWidget(style_row)

        # 参数设置列
        params_widget = QWidget(widget)
        params_layout = QVBoxLayout(params_widget)
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(5)

        # 点大小
        point_size_row = QWidget(params_widget)
        point_size_layout = QHBoxLayout(point_size_row)
        point_size_layout.setContentsMargins(0, 0, 0, 0)
        point_size_layout.setSpacing(5)
        point_size_label = QLabel("点大小:", point_size_row)
        point_size_label.setFixedWidth(60)
        self._point_size_spin = SpinBox(point_size_row)
        self._point_size_spin.setRange(1, 50)
        self._point_size_spin.setValue(3)
        self._point_size_spin.setToolTip("点大小")
        self._point_size_spin.setFixedWidth(60)
        self._point_size_spin.valueChanged.connect(self._on_point_size_changed)
        self._point_size_value_label = QLabel("3 px", point_size_row)
        self._point_size_value_label.setStyleSheet(f"color: {placeholder_color()};")
        point_size_layout.addWidget(point_size_label)
        point_size_layout.addWidget(self._point_size_spin)
        point_size_layout.addWidget(self._point_size_value_label)
        point_size_layout.addStretch()
        params_layout.addWidget(point_size_row)

        # 微调步长
        nudge_step_row = QWidget(params_widget)
        nudge_step_layout = QHBoxLayout(nudge_step_row)
        nudge_step_layout.setContentsMargins(0, 0, 0, 0)
        nudge_step_layout.setSpacing(5)
        nudge_step_label = QLabel("微调步长:", nudge_step_row)
        nudge_step_label.setFixedWidth(60)
        self._nudge_step_spin = SpinBox(nudge_step_row)
        self._nudge_step_spin.setRange(1, 20)
        self._nudge_step_spin.setValue(3)
        self._nudge_step_spin.setToolTip("微调步长")
        self._nudge_step_spin.setFixedWidth(60)
        self._nudge_step_spin.valueChanged.connect(self._on_nudge_step_changed)
        self._nudge_step_value_label = QLabel("3 px", nudge_step_row)
        self._nudge_step_value_label.setStyleSheet(f"color: {placeholder_color()};")
        nudge_step_layout.addWidget(nudge_step_label)
        nudge_step_layout.addWidget(self._nudge_step_spin)
        nudge_step_layout.addWidget(self._nudge_step_value_label)
        nudge_step_layout.addStretch()
        params_layout.addWidget(nudge_step_row)

        # 橡皮大小
        eraser_size_row = QWidget(params_widget)
        eraser_size_layout = QHBoxLayout(eraser_size_row)
        eraser_size_layout.setContentsMargins(0, 0, 0, 0)
        eraser_size_layout.setSpacing(5)
        eraser_size_label = QLabel("橡皮大小:", eraser_size_row)
        eraser_size_label.setFixedWidth(60)
        self._eraser_size_spin = SpinBox(eraser_size_row)
        self._eraser_size_spin.setRange(1, 100)
        self._eraser_size_spin.setValue(20)
        self._eraser_size_spin.setToolTip("橡皮大小")
        self._eraser_size_spin.setFixedWidth(60)
        self._eraser_size_spin.valueChanged.connect(self._on_eraser_size_changed)
        self._eraser_size_value_label = QLabel("20 px", eraser_size_row)
        self._eraser_size_value_label.setStyleSheet(f"color: {placeholder_color()};")
        eraser_size_layout.addWidget(eraser_size_label)
        eraser_size_layout.addWidget(self._eraser_size_spin)
        eraser_size_layout.addWidget(self._eraser_size_value_label)
        eraser_size_layout.addStretch()
        params_layout.addWidget(eraser_size_row)

        layout.addWidget(params_widget)

        return widget

    def _create_extract_tab(self) -> QWidget:
        """创建手动选点功能区"""
        from qfluentwidgets import TransparentTogglePushButton

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 第一行按钮
        buttons_widget = QWidget(tab)
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)

        # 校准
        self._calibrate_btn = TransparentTogglePushButton("校准", buttons_widget)
        self._calibrate_btn.setIcon(FIF.ALIGNMENT)
        self._calibrate_btn.setToolTip("校准")
        self._calibrate_btn.setCheckable(True)
        self._calibrate_btn.clicked.connect(lambda: self._on_tool_clicked("calibrate"))
        buttons_layout.addWidget(self._calibrate_btn)

        # 提取曲线
        self._extract_btn = TransparentTogglePushButton("提取曲线", buttons_widget)
        self._extract_btn.setIcon(FIF.PIE_SINGLE)
        self._extract_btn.setToolTip("提取曲线")
        self._extract_btn.setCheckable(True)
        self._extract_btn.clicked.connect(lambda: self._on_tool_clicked("extract"))
        buttons_layout.addWidget(self._extract_btn)

        buttons_layout.addStretch()
        layout.addWidget(buttons_widget)
        layout.addStretch()

        return tab

    def _create_auto_extract_tab(self) -> QWidget:
        """创建自动选点功能区"""
        from qfluentwidgets import TransparentTogglePushButton, PushButton

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 第一行按钮
        buttons_widget = QWidget(tab)
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)

        # 框选蒙版
        self._box_mask_btn = TransparentTogglePushButton("框选蒙版", buttons_widget)
        self._box_mask_btn.setIcon(FIF.LAYOUT)
        self._box_mask_btn.setToolTip("框选蒙版")
        self._box_mask_btn.setCheckable(True)
        self._box_mask_btn.clicked.connect(lambda: self._on_tool_clicked("box_mask"))
        buttons_layout.addWidget(self._box_mask_btn)

        # 涂刷蒙版
        self._brush_mask_btn = TransparentTogglePushButton("画笔蒙版", buttons_widget)
        self._brush_mask_btn.setIcon(FIF.BRUSH)
        self._brush_mask_btn.setToolTip("画笔蒙版")
        self._brush_mask_btn.setCheckable(True)
        self._brush_mask_btn.clicked.connect(lambda: self._on_tool_clicked("brush_mask"))
        buttons_layout.addWidget(self._brush_mask_btn)

        buttons_layout.addStretch()
        layout.addWidget(buttons_widget)

        # 第二行按钮
        clear_widget = QWidget(tab)
        clear_layout = QHBoxLayout(clear_widget)
        clear_layout.setContentsMargins(0, 0, 0, 0)
        clear_layout.setSpacing(5)

        # 删除所有蒙版
        self._clear_masks_btn = PushButton("清除蒙版", clear_widget)
        self._clear_masks_btn.setIcon(FIF.DELETE)
        self._clear_masks_btn.setToolTip("删除所有蒙版区域")
        self._clear_masks_btn.clicked.connect(self._on_clear_masks)
        clear_layout.addWidget(self._clear_masks_btn)

        clear_layout.addStretch()
        layout.addWidget(clear_widget)
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
                # 如果曲线有校准数据，显示实际坐标；否则显示像素坐标
                has_calibration = curve.calibration is not None
                # 更新表头
                if has_calibration:
                    self._curve_table.setHorizontalHeaderLabels(["X (实际)", "Y (实际)"])
                else:
                    self._curve_table.setHorizontalHeaderLabels(["X (像素)", "Y (像素)"])

                for i in range(len(curve.x_data)):
                    row = self._curve_table.rowCount()
                    self._curve_table.insertRow(row)

                    if has_calibration and curve.x_actual and curve.y_actual:
                        x_item = QTableWidgetItem(f"{curve.x_actual[i]:.4f}")
                        y_item = QTableWidgetItem(f"{curve.y_actual[i]:.4f}")
                    else:
                        x_item = QTableWidgetItem(f"{curve.x_data[i]:.4f}")
                        y_item = QTableWidgetItem(f"{curve.y_data[i]:.4f}")
                    self._curve_table.setItem(row, 0, x_item)
                    self._curve_table.setItem(row, 1, y_item)
        elif self._current_image_id:
            # 如果没有选中曲线但有选中图片，显示该图片所有曲线的数据预览
            img = project_manager.get_image(self._current_image_id)
            if img:
                self._curve_table.setHorizontalHeaderLabels(["X", "Y"])
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
                    # 如果曲线被隐藏，使用不同的图标
                    if curve.id in self._hidden_curves:
                        curve_item.setText(0, f"🔵 {curve.name} (已隐藏)")
                    else:
                        curve_item.setText(0, f"📈 {curve.name}")
                    curve_item.setData(0, Qt.ItemDataRole.UserRole, ("curve", curve.id, project.id, img.id))
                    if curve.id == current_curve_id:
                        from PySide6.QtGui import QBrush, QColor
                        bg_color = QColor(self._selection_background_color())
                        curve_item.setBackground(0, QBrush(bg_color))

            # 项目级别的导入曲线
            for curve in project.imported_curves:
                curve_item = QTreeWidgetItem(project_item)
                if curve.id in self._hidden_curves:
                    curve_item.setText(0, f"🔵 {curve.name} (已隐藏)")
                else:
                    curve_item.setText(0, f"📈 {curve.name}")
                curve_item.setData(0, Qt.ItemDataRole.UserRole, ("curve", curve.id, project.id))
                if curve.id == current_curve_id:
                    from PySide6.QtGui import QBrush, QColor
                    bg_color = QColor(self._selection_background_color())
                    curve_item.setBackground(0, QBrush(bg_color))

    def _on_tool_clicked(self, tool_name: str):
        """处理工具按钮点击"""
        # 如果已经激活了同一个工具，检查是否需要完成校准
        if self._active_tool == tool_name:
            # 校准模式下，检查是否已完成点设置
            if tool_name == "calibrate":
                calib = self._image_viewer.get_calibration()
                if calib.is_complete():
                    # 校准点已设置完成，弹出对话框完成校准
                    self._on_calibration_complete(calib)
                    return
                else:
                    # 校准未完成，提示用户
                    next_type = calib.next_point_type()
                    hints = {
                        "x_start": "请先完成X轴起点的设置",
                        "x_end": "请先完成X轴终点的设置",
                        "y_start": "请先完成Y轴起点的设置",
                        "y_end": "请先完成Y轴终点的设置",
                        "origin": "请先完成原点的设置",
                        "angle_point1": "请先完成A点(角度θ1)的设置",
                        "angle_point2": "请先完成B点(角度θ2)的设置",
                        "radius_point": "请先完成C点(极径r1)的设置",
                        "complete": "校准点已设置完成，请再次点击校准按钮",
                    }
                    self._status_label.setText(hints.get(next_type, "请继续设置校准点"))
                    return
            # 取消当前工具
            if self._active_tool == "extract" and self._current_curve_points:
                # 提取模式下取消，自动保存曲线
                self._save_extracted_curve()
            self._deactivate_all_tools()
            self._image_viewer.set_select_mode()
            self._active_tool = None
            self._status_label.setText("")
            return

        # 如果切换到其他工具，且当前是提取模式，先保存曲线
        if self._active_tool == "extract" and self._current_curve_points:
            self._save_extracted_curve()

        self._deactivate_all_tools()

        if tool_name == "calibrate":
            # 校准需要选中一个曲线
            if self._current_curve_id is None:
                QMessageBox.warning(self, "警告", "请先选择一个曲线进行校准")
                return

            # 检查是否有现有校准坐标
            calib = self._image_viewer.get_calibration()
            if calib.is_complete():
                reply = QMessageBox.question(
                    self, "确认", "开始校准将清除当前的校准坐标，确定要继续吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
                # 重置校准坐标
                calib.reset()

            # 弹出坐标类型选择对话框
            coord_dialog = CoordTypeDialog(self)
            if coord_dialog.exec():
                coord_type = coord_dialog.get_coord_type()
            else:
                return

            self._activate_tool_button(self._calibrate_btn)
            self._image_viewer.set_calibrate_mode(coord_type)
            self._active_tool = tool_name
            self._current_curve_points = []

            if coord_type == "linear":
                self._status_label.setText("请依次点击X轴起点、X轴终点、Y轴起点、Y轴终点")
            elif coord_type == "log":
                self._status_label.setText("请依次点击X轴起点、X轴终点、Y轴起点、Y轴终点（对数刻度）")
            elif coord_type == "polar":
                self._status_label.setText("请依次点击原点、A点(角度θ1)、B点(角度θ2)、C点(极径r1)")
        elif tool_name == "extract":
            # 提取曲线需要先选择或创建一个曲线
            if self._current_image_id is None:
                QMessageBox.warning(self, "警告", "请先选择一张图片")
                self._deactivate_all_tools()
                return
            if self._current_curve_id is None:
                QMessageBox.warning(self, "警告", "请先选择一条曲线")
                self._deactivate_all_tools()
                return
            self._activate_tool_button(self._extract_btn)
            self._image_viewer.set_extract_mode()
            self._active_tool = tool_name
            self._current_curve_points = []
            self._status_label.setText("点击添加点，E键切换橡皮擦模式")
        elif tool_name == "eraser":
            # 橡皮擦需要先选择一条曲线
            if self._current_image_id is None or self._current_curve_id is None:
                QMessageBox.warning(self, "警告", "请先选择一张图片和一条曲线")
                self._deactivate_all_tools()
                return
            self._activate_tool_button(self._eraser_btn)
            self._image_viewer.set_eraser_mode()
            self._active_tool = tool_name
            eraser_size = int(self._eraser_size_spin.value())
            self._status_label.setText(f"橡皮擦范围: {eraser_size}px，点击或拖动擦除")
        elif tool_name == "box_mask":
            # 框选蒙版需要先选择一张图片
            if self._current_image_id is None:
                QMessageBox.warning(self, "警告", "请先选择一张图片")
                self._deactivate_all_tools()
                return
            self._activate_tool_button(self._box_mask_btn)
            self._image_viewer.set_box_mask_mode()
            self._active_tool = tool_name
            self._status_label.setText("拖动绘制矩形蒙版区域")
        elif tool_name == "brush_mask":
            # 画笔蒙版需要先选择一张图片
            if self._current_image_id is None:
                QMessageBox.warning(self, "警告", "请先选择一张图片")
                self._deactivate_all_tools()
                return
            self._activate_tool_button(self._brush_mask_btn)
            self._image_viewer.set_brush_mask_mode()
            self._active_tool = tool_name
            self._status_label.setText("点击并拖动绘制多边形蒙版区域")
        else:
            self._image_viewer.set_select_mode()
            self._active_tool = None
            self._status_label.setText("")
            self._auto_status_label.setText("")

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

    def _on_clear_masks(self):
        """清除所有蒙版区域"""
        mask = self._image_viewer.get_mask()
        if mask:
            mask.reset()
            self._image_viewer.update()
            self._status_label.setText("已清除所有蒙版区域")
            self.project_modified.emit()

    def _on_point_size_changed(self, value):
        self._image_viewer.set_point_size(float(value))
        self._point_size_value_label.setText(f"{value} px")

    def _on_nudge_step_changed(self, value):
        self._image_viewer.set_nudge_step(float(value))
        self._nudge_step_value_label.setText(f"{value} px")

    def _on_eraser_size_changed(self, value):
        self._image_viewer.set_eraser_size(float(value))
        self._eraser_size_value_label.setText(f"{value} px")

    def _on_color_changed(self, color):
        """颜色改变"""
        if isinstance(color, QColor):
            color_str = color.name(QColor.NameFormat.HexRgb)
        else:
            color_str = str(color)
        if self._current_curve_id:
            curve = project_manager.get_curve(self._current_curve_id)
            if curve:
                curve.color = color_str
                self._display_current_curve_on_image()
                self.project_modified.emit()

    def _on_shape_changed(self, index):
        """形状改变"""
        shape_map = {"圆形": "circle", "方形": "square", "三角形": "triangle", "菱形": "diamond", "倒三角": "inv_triangle", "叉号": "cross", "星号": "star", "五角星": "pentagram"}
        shape = shape_map.get(self._shape_combo.currentText(), "circle")
        if self._current_curve_id:
            curve = project_manager.get_curve(self._current_curve_id)
            if curve:
                curve.point_shape = shape
                self._display_current_curve_on_image()
                self.project_modified.emit()

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
                        # 只有当点击不同图片时才改变曲线
                        if self._current_image_id != img_id:
                            self._current_image_id = img_id
                            # 自动选择该图片的第一条曲线
                            if img.curves:
                                self._current_curve_id = img.curves[0].id
                                self._display_current_curve_on_image()
                            else:
                                self._current_curve_id = None
                                self._image_viewer.clear_curves()
                            self._update_curve_table()
                        else:
                            # 同一图片，只刷新校准显示
                            if self._current_curve_id:
                                self._display_current_curve_on_image()
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

            # 清除图片上的曲线，显示当前选中的曲线和校准
            self._display_current_curve_on_image()
            self._update_curve_table()
            self._refresh_project_tree()

    def _on_tree_item_double_clicked(self, item, column):
        pass

    def _on_tree_context_menu(self, pos):
        """显示项目树右键菜单"""
        item = self._project_tree.itemAt(pos)
        if item is None:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None or data[0] != "curve":
            return

        menu = QMenu(self)

        curve_id = data[1]
        is_hidden = curve_id in self._hidden_curves if hasattr(self, '_hidden_curves') else False

        # 显示/隐藏曲线
        if is_hidden:
            # 曲线已隐藏，点击应该显示
            show_action = menu.addAction("显示曲线")
            show_action.triggered.connect(lambda checked, cid=curve_id: self._toggle_curve_visibility(cid, False))
        else:
            # 曲线已显示，点击应该隐藏
            hide_action = menu.addAction("隐藏曲线")
            hide_action.triggered.connect(lambda checked, cid=curve_id: self._toggle_curve_visibility(cid, True))

        # 删除曲线
        delete_action = menu.addAction("删除曲线")
        delete_action.triggered.connect(lambda checked, cid=curve_id: self._delete_curve(cid))

        menu.exec(self._project_tree.mapToGlobal(pos))

    def _toggle_curve_visibility(self, curve_id: str, hidden: bool):
        """切换曲线可见性"""
        if not hasattr(self, '_hidden_curves'):
            self._hidden_curves = set()

        if hidden:
            self._hidden_curves.add(curve_id)
        else:
            self._hidden_curves.discard(curve_id)

        # 如果当前显示的是这条曲线，更新显示
        if self._current_curve_id == curve_id:
            if hidden:
                self._image_viewer.clear_curves()
                # 隐藏时也清除校准
                calib = self._image_viewer.get_calibration()
                calib.reset()
                self._image_viewer.update()
            else:
                self._display_current_curve_on_image()

        self._refresh_project_tree()

    def _delete_curve(self, curve_id: str):
        """删除曲线"""
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这条曲线吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        curve = project_manager.get_curve(curve_id)
        if curve is None:
            return

        # 从对应的图片中移除
        if curve.source_image_id:
            img = project_manager.get_image(curve.source_image_id)
            if img:
                img.curves = [c for c in img.curves if c.id != curve_id]
        else:
            project = project_manager.current_project
            if project:
                project.imported_curves = [c for c in project.imported_curves if c.id != curve_id]

        # 从隐藏集合中移除
        self._hidden_curves.discard(curve_id)

        if self._current_curve_id == curve_id:
            self._current_curve_id = None
            self._image_viewer.clear_curves()
            # 重置校准
            calib = self._image_viewer.get_calibration()
            calib.reset()

        self._refresh_project_tree()
        self._update_curve_table()
        self.project_modified.emit()

    def _display_curve_on_image(self, curve):
        """在图片查看器上显示曲线的点（使用像素坐标）"""
        from ui.widgets.image_viewer import CurveOverlayItem

        if curve and curve.x_data and curve.y_data:
            curve_item = CurveOverlayItem(color=curve.color, point_shape=getattr(curve, 'point_shape', 'circle'))
            curve_item.name = curve.name

            # 直接使用存储的像素坐标
            for i in range(len(curve.x_data)):
                curve_item.add_point(curve.x_data[i], curve.y_data[i])

            self._image_viewer.add_curve_item(curve_item)

    def _display_current_curve_on_image(self):
        """显示当前选中曲线到图片"""
        self._image_viewer.clear_curves()
        if self._current_curve_id:
            curve = project_manager.get_curve(self._current_curve_id)
            if curve:
                # 显示曲线点
                self._display_curve_on_image(curve)
                # 更新颜色和形状选择器
                if hasattr(self, '_color_btn'):
                    self._color_btn.blockSignals(True)
                    self._color_btn.setColor(QColor(curve.color))
                    self._color_btn.blockSignals(False)
                if hasattr(self, '_shape_combo'):
                    shape_map = {"circle": "圆形", "square": "方形", "triangle": "三角形", "diamond": "菱形", "inv_triangle": "倒三角", "cross": "叉号", "star": "星号", "pentagram": "五角星"}
                    shape_text = shape_map.get(getattr(curve, 'point_shape', 'circle'), "圆形")
                    idx = self._shape_combo.findText(shape_text)
                    if idx >= 0:
                        self._shape_combo.blockSignals(True)
                        self._shape_combo.setCurrentIndex(idx)
                        self._shape_combo.blockSignals(False)
                # 设置校准覆盖层（无论曲线是否有数据都要显示校准）
                if curve.calibration:
                    self._apply_calibration_to_viewer(curve.calibration)
                else:
                    calib = self._image_viewer.get_calibration()
                    calib.reset()
                self._image_viewer.update()

    def _apply_calibration_to_viewer(self, calib_data):
        """将校准数据应用到图片查看器"""
        from PySide6.QtCore import QPointF
        calib = self._image_viewer.get_calibration()
        calib.reset()
        if calib_data.x_start:
            calib.x_start = QPointF(calib_data.x_start[0], calib_data.x_start[1])
        if calib_data.x_end:
            calib.x_end = QPointF(calib_data.x_end[0], calib_data.x_end[1])
        if calib_data.y_start:
            calib.y_start = QPointF(calib_data.y_start[0], calib_data.y_start[1])
        if calib_data.y_end:
            calib.y_end = QPointF(calib_data.y_end[0], calib_data.y_end[1])
        calib.x_range = calib_data.x_range
        calib.y_range = calib_data.y_range
        calib.coord_type = calib_data.coord_type

    def _create_calibration_overlay(self, calib_data):
        """从 CalibrationData 创建 CalibrationOverlay"""
        from PySide6.QtCore import QPointF
        overlay = self._image_viewer.get_calibration()
        overlay.reset()
        if calib_data.x_start:
            overlay.x_start = QPointF(calib_data.x_start[0], calib_data.x_start[1])
        if calib_data.x_end:
            overlay.x_end = QPointF(calib_data.x_end[0], calib_data.x_end[1])
        if calib_data.y_start:
            overlay.y_start = QPointF(calib_data.y_start[0], calib_data.y_start[1])
        if calib_data.y_end:
            overlay.y_end = QPointF(calib_data.y_end[0], calib_data.y_end[1])
        overlay.x_range = calib_data.x_range
        overlay.y_range = calib_data.y_range
        overlay.coord_type = calib_data.coord_type
        return overlay

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

        # 继承同一图片中上一条曲线的校准数据、颜色和形状
        calib = None
        color = "#0078D4"
        point_shape = "circle"
        if img.curves:
            prev_curve = img.curves[-1]
            calib = prev_curve.calibration
            color = prev_curve.color
            point_shape = getattr(prev_curve, 'point_shape', 'circle')

        # 创建新曲线
        curve = project_manager.add_curve_to_image(
            self._current_image_id,
            x_data=[],
            y_data=[],
            name=f"曲线 {len(img.curves) + 1}",
            color=color,
            point_shape=point_shape,
            calibration=calib
        )

        if curve:
            self._current_curve_id = curve.id
            self._display_current_curve_on_image()
            self._update_curve_table()
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

        # 根据坐标类型选择对应的对话框
        coord_type = calibration_overlay.coord_type
        if coord_type == "polar":
            dialog = PolarCalibrationDialog(calibration_overlay, self)
        else:
            dialog = CalibrationDialog(calibration_overlay, coord_type, self)

        if dialog.exec():
            data = dialog.get_calibration_data()

            if coord_type == "polar":
                calib_data = CalibrationData(
                    x_start=(calibration_overlay.x_start.x(), calibration_overlay.x_start.y()),
                    x_end=(calibration_overlay.x_end.x(), calibration_overlay.x_end.y()),
                    coord_type="polar",
                    angle_A=data["angle_A"],
                    radius_A=data["radius_A"]
                )
            else:
                calib_data = CalibrationData(
                    x_start=(calibration_overlay.x_start.x(), calibration_overlay.x_start.y()),
                    x_end=(calibration_overlay.x_end.x(), calibration_overlay.x_end.y()),
                    y_start=(calibration_overlay.y_start.x(), calibration_overlay.y_start.y()),
                    y_end=(calibration_overlay.y_end.x(), calibration_overlay.y_end.y()),
                    x_range=data["x_range"],
                    y_range=data["y_range"],
                    coord_type=data["coord_type"]
                )

            # 更新校准
            project_manager.update_curve_calibration(self._current_curve_id, calib_data)

            # 重新计算实际坐标
            curve = project_manager.get_curve(self._current_curve_id)
            if curve and curve.x_data:
                x_actual = []
                y_actual = []
                for px, py in zip(curve.x_data, curve.y_data):
                    x, y = project_manager.pixel_to_actual_coords(self._current_curve_id, px, py)
                    x_actual.append(x)
                    y_actual.append(y)
                curve.x_actual = x_actual
                curve.y_actual = y_actual

            self._deactivate_all_tools()
            self._active_tool = None
            self._image_viewer.set_select_mode()
            self._status_label.setText("校准完成！")
            self._display_current_curve_on_image()
            self._update_curve_table()
            self._refresh_project_tree()
            self.project_modified.emit()

    def _on_calibration_step(self, step_type: str):
        step_hints = {
            "x_start": "请点击X轴起点",
            "x_end": "请点击X轴终点",
            "y_start": "请点击Y轴起点",
            "y_end": "请点击Y轴终点",
            "origin": "请点击原点(极点)",
            "x_axis": "请点击正X轴方向点",
            "y_axis": "请点击Y轴正方向点",
            "angle_ref": "请点击角度参考点",
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

        # 记录撤销信息（添加点）
        if self._current_curve_id:
            calib = None
            curve = project_manager.get_curve(self._current_curve_id)
            if curve:
                calib = curve.calibration
            if calib:
                x_actual, y_actual = project_manager.pixel_to_actual_coords(self._current_curve_id, px, py)
            else:
                x_actual, y_actual = px, py
            self._record_state("add_point", self._current_curve_id, {
                "index": len(self._current_curve_points) - 1,
                "x": px,
                "y": py,
                "x_actual": x_actual,
                "y_actual": y_actual
            })

    def _on_eraser_point(self, px: float, py: float):
        """处理橡皮擦擦除点"""
        eraser_radius = self._image_viewer.get_eraser_size()
        mask = self._image_viewer.get_mask()

        # 擦除曲线点 - 逐点记录用于撤销
        if self._current_curve_id is not None:
            curve = project_manager.get_curve(self._current_curve_id)
            if curve is not None and curve.x_data:
                points_to_remove = []
                for i in range(len(curve.x_data)):
                    dx = curve.x_data[i] - px
                    dy = curve.y_data[i] - py
                    distance = (dx * dx + dy * dy) ** 0.5
                    if distance <= eraser_radius:
                        points_to_remove.append(i)

                # 逐点记录并删除
                for i in reversed(points_to_remove):
                    # 记录被删除的点用于撤销
                    self._record_state("remove_point", self._current_curve_id, {
                        "index": i,
                        "x": curve.x_data[i],
                        "y": curve.y_data[i],
                        "x_actual": curve.x_actual[i] if curve.x_actual and i < len(curve.x_actual) else None,
                        "y_actual": curve.y_actual[i] if curve.y_actual and i < len(curve.y_actual) else None
                    })
                    # 删除点
                    del curve.x_data[i]
                    del curve.y_data[i]
                    if curve.x_actual and i < len(curve.x_actual):
                        del curve.x_actual[i]
                        del curve.y_actual[i]

                if points_to_remove:
                    self._display_current_curve_on_image()
                    self._update_curve_table()
                    self.project_modified.emit()

        # 擦除蒙版多边形 - 记录用于撤销
        if mask and mask.enabled and mask.polygons:
            polygon_to_remove = mask.get_polygon_at_point(px, py)
            if polygon_to_remove >= 0:
                # 记录被删除的蒙版用于撤销
                self._record_state("remove_mask", None, {
                    "polygon": list(mask.polygons[polygon_to_remove])
                })
                # 执行删除
                del mask.polygons[polygon_to_remove]
                if not mask.polygons:
                    mask.enabled = False
                self._image_viewer.update()
                self._status_label.setText(f"蒙版区域: {len(mask.polygons)} 个")
                self.project_modified.emit()

    def _on_toggle_eraser_mode(self):
        """切换橡皮擦模式"""
        if self._active_tool == "extract":
            self._on_tool_clicked("eraser")
        elif self._active_tool == "eraser":
            self._on_tool_clicked("extract")

    def _on_mask_changed(self):
        """蒙版改变时的处理"""
        mask = self._image_viewer.get_mask()
        if mask and mask.enabled:
            self._status_label.setText(f"蒙版区域: {len(mask.polygons)} 个")
        self.project_modified.emit()

    def _on_mask_about_to_add(self, polygon):
        """蒙版即将添加时记录撤销信息"""
        self._record_state("add_mask", None, {"polygon": list(polygon)})

    def _save_extracted_curve(self):
        """保存提取的曲线点"""
        if not self._current_curve_points or self._current_image_id is None:
            return

        img = project_manager.get_image(self._current_image_id)
        if img is None:
            return

        curve = None
        if self._current_curve_id:
            curve = project_manager.get_curve(self._current_curve_id)

        calib = curve.calibration if curve else None
        color = self._color_btn.color.name(QColor.NameFormat.HexRgb) if hasattr(self, '_color_btn') else "#0078D4"
        shape_map = {"圆形": "circle", "方形": "square", "三角形": "triangle", "菱形": "diamond", "倒三角": "inv_triangle", "叉号": "cross", "星号": "star", "五角星": "pentagram"}
        point_shape = shape_map.get(self._shape_combo.currentText(), "circle") if hasattr(self, '_shape_combo') else "circle"

        # 如果有选中曲线，追加点；否则创建新曲线
        if self._current_curve_id and curve:
            for px, py in self._current_curve_points:
                curve.x_data.append(px)
                curve.y_data.append(py)
                if calib:
                    x, y = project_manager.pixel_to_actual_coords(self._current_curve_id, px, py)
                    curve.x_actual.append(x)
                    curve.y_actual.append(y)
                else:
                    curve.x_actual.append(px)
                    curve.y_actual.append(py)
        else:
            x_data = []
            y_data = []
            x_actual = []
            y_actual = []
            for px, py in self._current_curve_points:
                x_data.append(px)
                y_data.append(py)
                if calib:
                    x, y = project_manager.pixel_to_actual_coords(None, px, py)
                    x_actual.append(x)
                    y_actual.append(y)
                else:
                    x_actual.append(px)
                    y_actual.append(py)
            curve = project_manager.add_curve_to_image(
                self._current_image_id, x_data, y_data, name=f"曲线 {len(img.curves) + 1}",
                color=color, point_shape=point_shape
            )
            if curve and calib:
                curve.x_actual = x_actual
                curve.y_actual = y_actual

        if curve:
            self._current_curve_points = []
            self._status_label.setText("曲线已保存！")
            self._display_current_curve_on_image()
            self._update_curve_table()
            self._refresh_project_tree()
            self.project_modified.emit()

    def _on_sort_by_x(self):
        """按X坐标排序当前曲线"""
        if self._current_curve_id is None:
            return
        curve = project_manager.get_curve(self._current_curve_id)
        if curve is None:
            return

        # 先保存当前提取的曲线点（如果有）
        if self._current_curve_points:
            self._save_extracted_curve()

        # 如果曲线没有数据，直接返回
        if not curve.x_data:
            return

        # 保存校准数据
        saved_calibration = curve.calibration

        # 获取排序后的索引
        indices = sorted(range(len(curve.x_data)), key=lambda i: curve.x_data[i])

        curve.x_data = [curve.x_data[i] for i in indices]
        curve.y_data = [curve.y_data[i] for i in indices]
        if curve.x_actual and curve.y_actual:
            curve.x_actual = [curve.x_actual[i] for i in indices]
            curve.y_actual = [curve.y_actual[i] for i in indices]

        # 先应用校准，再显示曲线
        if saved_calibration:
            self._apply_calibration_to_viewer(saved_calibration)
        self._display_current_curve_on_image()
        self._update_curve_table()
        self.project_modified.emit()

    def _on_sort_by_y(self):
        """按Y坐标排序当前曲线"""
        if self._current_curve_id is None:
            return
        curve = project_manager.get_curve(self._current_curve_id)
        if curve is None:
            return

        # 先保存当前提取的曲线点（如果有）
        if self._current_curve_points:
            self._save_extracted_curve()

        # 如果曲线没有数据，直接返回
        if not curve.y_data:
            return

        # 保存校准数据
        saved_calibration = curve.calibration

        # 获取排序后的索引
        indices = sorted(range(len(curve.y_data)), key=lambda i: curve.y_data[i])

        curve.x_data = [curve.x_data[i] for i in indices]
        curve.y_data = [curve.y_data[i] for i in indices]
        if curve.x_actual and curve.y_actual:
            curve.x_actual = [curve.x_actual[i] for i in indices]
            curve.y_actual = [curve.y_actual[i] for i in indices]

        # 先应用校准，再显示曲线
        if saved_calibration:
            self._apply_calibration_to_viewer(saved_calibration)
        self._display_current_curve_on_image()
        self._update_curve_table()
        self.project_modified.emit()

    def _on_clear_all_points(self):
        """清除当前曲线的所有点"""
        if self._current_curve_id is None:
            return
        curve = project_manager.get_curve(self._current_curve_id)
        if curve is None:
            return

        if not curve.x_data:
            return

        # 记录状态用于撤销
        self._record_state("clear_points", self._current_curve_id)

        # 清除所有点
        curve.x_data = []
        curve.y_data = []
        curve.x_actual = []
        curve.y_actual = []

        # 清除当前提取的点
        self._current_curve_points = []

        # 重新显示
        self._display_current_curve_on_image()
        self._update_curve_table()
        self.project_modified.emit()
        self._status_label.setText("已清除所有点")

    def _record_state(self, action_type: str, curve_id: str = None, data: dict = None):
        """记录操作到撤销栈

        精细化操作记录：
        - add_point: 添加点 - 记录点数据
        - remove_point: 删除点 - 记录点和索引
        - clear_curve: 清除曲线 - 记录所有点
        - add_mask: 添加蒙版 - 记录蒙版多边形
        - remove_mask: 删除蒙版 - 记录蒙版多边形
        """
        if self._is_undo_redo:
            return

        if curve_id is None:
            curve_id = self._current_curve_id

        # 构建操作记录
        state = {
            "type": action_type,
            "curve_id": curve_id,
            "data": data
        }

        self._undo_stack.append(state)
        # 清空重做栈
        self._redo_stack.clear()

        # 限制历史记录数量
        if len(self._undo_stack) > self._max_history:
            self._undo_stack.pop(0)

    def _undo(self):
        """撤销上一个操作"""
        if not self._undo_stack:
            self._status_label.setText("没有可撤销的操作")
            return

        self._is_undo_redo = True
        state = self._undo_stack.pop()

        action_type = state["type"]
        curve_id = state.get("curve_id")
        data = state.get("data", {})
        curve = project_manager.get_curve(curve_id) if curve_id else None

        if action_type == "add_point":
            # 撤销添加点 = 删除最后添加的点
            # 先检查点是否在_current_curve_points中（未保存）
            if self._current_curve_points:
                # 保存到重做栈
                pt = self._current_curve_points[-1]
                self._redo_stack.append({
                    "type": "add_point",
                    "curve_id": curve_id,
                    "data": {
                        "x": pt[0],
                        "y": pt[1],
                        "x_actual": data.get("x_actual"),
                        "y_actual": data.get("y_actual")
                    }
                })
                # 从当前点列表中删除
                self._current_curve_points.pop()
            elif curve and curve.x_data:
                # 点已在curve中，从curve删除
                self._redo_stack.append({
                    "type": "add_point",
                    "curve_id": curve_id,
                    "data": {
                        "index": len(curve.x_data) - 1,
                        "x": curve.x_data[-1],
                        "y": curve.y_data[-1],
                        "x_actual": curve.x_actual[-1] if curve.x_actual else None,
                        "y_actual": curve.y_actual[-1] if curve.y_actual else None
                    }
                })
                del curve.x_data[-1]
                del curve.y_data[-1]
                if curve.x_actual:
                    del curve.x_actual[-1]
                    del curve.y_actual[-1]

        elif action_type == "remove_point":
            # 撤销删除点 = 恢复被删除的点
            if curve:
                # 保存当前状态到重做栈
                self._redo_stack.append({
                    "type": "remove_point",
                    "curve_id": curve_id,
                    "data": {
                        "index": data["index"],
                        "x": data["x"],
                        "y": data["y"],
                        "x_actual": data.get("x_actual"),
                        "y_actual": data.get("y_actual")
                    }
                })
                # 执行撤销：在原位置恢复点
                index = data["index"]
                curve.x_data.insert(index, data["x"])
                curve.y_data.insert(index, data["y"])
                if data.get("x_actual") is not None:
                    if not curve.x_actual:
                        curve.x_actual = []
                        curve.y_actual = []
                    curve.x_actual.insert(index, data["x_actual"])
                    curve.y_actual.insert(index, data["y_actual"])

        elif action_type == "clear_curve":
            # 撤销清除 = 恢复所有点
            if curve and data.get("points"):
                # 保存当前状态到重做栈
                self._redo_stack.append({
                    "type": "clear_curve",
                    "curve_id": curve_id,
                    "data": {
                        "points": [(x, y) for x, y in zip(curve.x_data, curve.y_data)] if curve.x_data else [],
                        "x_actual": list(curve.x_actual) if curve.x_actual else [],
                        "y_actual": list(curve.y_actual) if curve.y_actual else []
                    }
                })
                # 执行撤销
                curve.x_data = [p[0] for p in data["points"]]
                curve.y_data = [p[1] for p in data["points"]]
                curve.x_actual = list(data.get("x_actual", []))
                curve.y_actual = list(data.get("y_actual", []))

        elif action_type == "remove_mask":
            # 撤销删除蒙版 = 恢复蒙版
            mask = self._image_viewer.get_mask()
            if mask and data.get("polygon") is not None:
                # 保存当前状态到重做栈
                self._redo_stack.append({
                    "type": "remove_mask",
                    "curve_id": None,
                    "data": {"polygon": data["polygon"]}
                })
                # 执行撤销
                mask.polygons.append(data["polygon"])
                mask.enabled = True

        elif action_type == "add_mask":
            # 撤销添加蒙版 = 删除最后添加的蒙版
            mask = self._image_viewer.get_mask()
            if mask and mask.polygons:
                # 保存当前状态到重做栈
                self._redo_stack.append({
                    "type": "add_mask",
                    "curve_id": None,
                    "data": {"polygon": mask.polygons[-1]}
                })
                # 执行撤销
                del mask.polygons[-1]
                if not mask.polygons:
                    mask.enabled = False

        # 更新显示
        if curve:
            self._display_current_curve_on_image()
            self._update_curve_table()
        self._image_viewer.update()
        self.project_modified.emit()
        self._is_undo_redo = False
        self._status_label.setText(f"已撤销: {action_type}")

    def _redo(self):
        """重做上一个撤销的操作"""
        if not self._redo_stack:
            self._status_label.setText("没有可重做的操作")
            return

        self._is_undo_redo = True
        state = self._redo_stack.pop()

        action_type = state["type"]
        curve_id = state.get("curve_id")
        data = state.get("data", {})
        curve = project_manager.get_curve(curve_id) if curve_id else None

        if action_type == "add_point":
            # 重做添加点 = 重新添加点
            if curve:
                # 保存当前状态到撤销栈
                self._undo_stack.append({
                    "type": "remove_point",
                    "curve_id": curve_id,
                    "data": {
                        "index": data["index"],
                        "x": data["x"],
                        "y": data["y"],
                        "x_actual": data.get("x_actual"),
                        "y_actual": data.get("y_actual")
                    }
                })
                # 执行重做
                curve.x_data.append(data["x"])
                curve.y_data.append(data["y"])
                if data.get("x_actual") is not None:
                    if not curve.x_actual:
                        curve.x_actual = []
                        curve.y_actual = []
                    curve.x_actual.append(data["x_actual"])
                    curve.y_actual.append(data["y_actual"])

        elif action_type == "remove_point":
            # 重做删除点 = 重新删除点
            if curve:
                # 保存当前状态到撤销栈
                redo_data = {
                    "index": data["index"],
                    "x": data["x"],
                    "y": data["y"],
                    "x_actual": data.get("x_actual"),
                    "y_actual": data.get("y_actual")
                }
                self._undo_stack.append({
                    "type": "remove_point",
                    "curve_id": curve_id,
                    "data": redo_data
                })
                # 执行重做
                index = data["index"]
                if index < len(curve.x_data):
                    del curve.x_data[index]
                    del curve.y_data[index]
                    if curve.x_actual and index < len(curve.x_actual):
                        del curve.x_actual[index]
                        del curve.y_actual[index]

        elif action_type == "clear_curve":
            # 重做清除 = 重新清除
            if curve and data.get("points"):
                # 保存当前状态到撤销栈
                self._undo_stack.append({
                    "type": "clear_curve",
                    "curve_id": curve_id,
                    "data": {
                        "points": [(x, y) for x, y in zip(curve.x_data, curve.y_data)] if curve.x_data else [],
                        "x_actual": list(curve.x_actual) if curve.x_actual else [],
                        "y_actual": list(curve.y_actual) if curve.y_actual else []
                    }
                })
                # 执行重做
                curve.x_data = []
                curve.y_data = []
                curve.x_actual = []
                curve.y_actual = []

        elif action_type == "remove_mask":
            # 重做删除蒙版 = 重新删除
            mask = self._image_viewer.get_mask()
            if mask and data.get("polygon") is not None:
                # 保存当前状态到撤销栈
                self._undo_stack.append({
                    "type": "remove_mask",
                    "curve_id": None,
                    "data": {"polygon": data["polygon"]}
                })
                # 执行重做 - 找到并删除该蒙版
                for i, poly in enumerate(mask.polygons):
                    if poly == data["polygon"]:
                        del mask.polygons[i]
                        break
                if not mask.polygons:
                    mask.enabled = False

        elif action_type == "add_mask":
            # 重做添加蒙版 = 重新添加
            mask = self._image_viewer.get_mask()
            if mask and data.get("polygon") is not None:
                # 保存当前状态到撤销栈
                self._undo_stack.append({
                    "type": "add_mask",
                    "curve_id": None,
                    "data": {"polygon": data["polygon"]}
                })
                # 执行重做
                mask.polygons.append(data["polygon"])
                mask.enabled = True

        # 更新显示
        if curve:
            self._display_current_curve_on_image()
            self._update_curve_table()
        self._image_viewer.update()
        self.project_modified.emit()
        self._is_undo_redo = False
        self._status_label.setText(f"已重做: {action_type}")


# 需要导入 FIF
from qfluentwidgets.common.icon import FluentIcon as FIF
