from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFormLayout


class PolarCalibrationDialog(QDialog):
    """极坐标校准配置对话框

    输入角度1、角度2、极径1的实际数值
    """

    def __init__(self, calibration, parent=None):
        super().__init__(parent)
        self._calibration = calibration
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("极坐标校准配置")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        info_label = QLabel("请设置极坐标的实际数值:", self)
        layout.addWidget(info_label)

        # 显示校准点信息
        info_text = QLabel(
            f"原点: ({self._calibration.x_start.x():.1f}, {self._calibration.x_start.y():.1f})\n"
            f"角度1点: ({self._calibration.x_end.x():.1f}, {self._calibration.x_end.y():.1f})\n"
            f"角度2点: ({self._calibration.y_start.x():.1f}, {self._calibration.y_start.y():.1f})\n"
            f"极径1点: ({self._calibration.y_end.x():.1f}, {self._calibration.y_end.y():.1f})",
            self
        )
        info_text.setStyleSheet("color: gray; padding: 10px; background: #f0f0f0; border-radius: 5px;")
        layout.addWidget(info_text)

        form = QFormLayout()

        # 角度1
        self._angle1_input = QLineEdit("0", self)
        form.addRow("角度1 (θ1):", self._angle1_input)

        # 角度2
        self._angle2_input = QLineEdit("90", self)
        form.addRow("角度2 (θ2):", self._angle2_input)

        # 极径1
        self._radius1_input = QLineEdit("1", self)
        form.addRow("极径1 (r1):", self._radius1_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self._ok_btn = QPushButton("确定", self)
        self._cancel_btn = QPushButton("取消", self)
        self._ok_btn.clicked.connect(self.accept)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self._ok_btn)
        btn_layout.addWidget(self._cancel_btn)
        layout.addLayout(btn_layout)

    def get_calibration_data(self) -> dict:
        """获取校准配置数据"""
        return {
            "angle1": float(self._angle1_input.text()),
            "angle2": float(self._angle2_input.text()),
            "radius1": float(self._radius1_input.text()),
            "coord_type": "polar"
        }
