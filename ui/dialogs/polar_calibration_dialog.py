from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFormLayout
from PySide6.QtCore import Qt


class PolarCalibrationDialog(QDialog):
    """极坐标校准配置对话框"""

    def __init__(self, calibration, parent=None):
        super().__init__(parent)
        self._calibration = calibration
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("极坐标校准配置")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        info_label = QLabel("请设置极坐标的实际数值范围:", self)
        layout.addWidget(info_label)

        info_text = QLabel(
            f"原点: ({self._calibration.x_start.x():.1f}, {self._calibration.x_start.y():.1f})\n"
            f"X轴方向点: ({self._calibration.x_end.x():.1f}, {self._calibration.x_end.y():.1f})\n"
            f"Y轴方向点: ({self._calibration.y_start.x():.1f}, {self._calibration.y_start.y():.1f})\n"
            f"角度参考点: ({self._calibration.y_end.x():.1f}, {self._calibration.y_end.y():.1f})",
            self
        )
        info_text.setStyleSheet("color: gray; padding: 10px; background: #f0f0f0; border-radius: 5px;")
        layout.addWidget(info_text)

        form = QFormLayout()

        # 半径范围
        r_layout = QHBoxLayout()
        self._r_min_input = QLineEdit("0", self)
        self._r_max_input = QLineEdit("1", self)
        r_layout.addWidget(QLabel("最小:", self))
        r_layout.addWidget(self._r_min_input)
        r_layout.addWidget(QLabel("最大:", self))
        r_layout.addWidget(self._r_max_input)
        form.addRow("半径范围:", r_layout)

        # 角度范围
        theta_layout = QHBoxLayout()
        self._theta_min_input = QLineEdit("0", self)
        self._theta_max_input = QLineEdit("360", self)
        theta_layout.addWidget(QLabel("最小:", self))
        theta_layout.addWidget(self._theta_min_input)
        theta_layout.addWidget(QLabel("最大:", self))
        theta_layout.addWidget(self._theta_max_input)
        form.addRow("角度范围(度):", theta_layout)

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
            "x_range": (float(self._r_min_input.text()), float(self._r_max_input.text())),
            "y_range": (float(self._theta_min_input.text()), float(self._theta_max_input.text())),
            "coord_type": "polar"
        }
