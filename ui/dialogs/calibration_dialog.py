from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout
from qfluentwidgets import BodyLabel, LineEdit, PrimaryPushButton, PushButton


class CalibrationDialog(QDialog):
    """线性/对数校准配置对话框"""

    def __init__(self, calibration, coord_type="linear", parent=None):
        super().__init__(parent)
        self._calibration = calibration
        self._coord_type = coord_type
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("校准配置")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        info_label = BodyLabel("请设置坐标轴的实际数值范围:", self)
        layout.addWidget(info_label)

        info = BodyLabel(
            f"X轴起点: ({self._calibration.x_start.x():.1f}, {self._calibration.x_start.y():.1f})\n"
            f"X轴终点: ({self._calibration.x_end.x():.1f}, {self._calibration.x_end.y():.1f})\n"
            f"Y轴起点: ({self._calibration.y_start.x():.1f}, {self._calibration.y_start.y():.1f})\n"
            f"Y轴终点: ({self._calibration.y_end.x():.1f}, {self._calibration.y_end.y():.1f})",
            self
        )
        info.setStyleSheet("color: gray; padding: 10px; background: #f0f0f0; border-radius: 5px;")
        layout.addWidget(info)

        form = QFormLayout()

        # X轴范围
        x_layout = QHBoxLayout()
        self._x_min_input = LineEdit(self)
        self._x_max_input = LineEdit(self)
        self._x_min_input.setText("0")
        self._x_max_input.setText("1")
        x_layout.addWidget(BodyLabel("最小:", self))
        x_layout.addWidget(self._x_min_input)
        x_layout.addWidget(BodyLabel("最大:", self))
        x_layout.addWidget(self._x_max_input)
        form.addRow("X轴范围:", x_layout)

        # Y轴范围
        y_layout = QHBoxLayout()
        self._y_min_input = LineEdit(self)
        self._y_max_input = LineEdit(self)
        self._y_min_input.setText("0")
        self._y_max_input.setText("1")
        y_layout.addWidget(BodyLabel("最小:", self))
        y_layout.addWidget(self._y_min_input)
        y_layout.addWidget(BodyLabel("最大:", self))
        y_layout.addWidget(self._y_max_input)
        form.addRow("Y轴范围:", y_layout)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self._ok_btn = PrimaryPushButton("确定", self)
        self._cancel_btn = PushButton("取消", self)
        self._ok_btn.clicked.connect(self.accept)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self._ok_btn)
        btn_layout.addWidget(self._cancel_btn)
        layout.addLayout(btn_layout)

    def get_calibration_data(self) -> dict:
        """获取校准配置数据"""
        return {
            "x_range": (float(self._x_min_input.text()), float(self._x_max_input.text())),
            "y_range": (float(self._y_min_input.text()), float(self._y_max_input.text())),
            "coord_type": self._coord_type
        }
