from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout
from qfluentwidgets import BodyLabel, LineEdit, PrimaryPushButton, PushButton


class PolarCalibrationDialog(QDialog):
    """极坐标校准配置对话框

    输入点A的角度和极径
    """

    def __init__(self, calibration, parent=None):
        super().__init__(parent)
        self._calibration = calibration
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("极坐标校准配置")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        info_label = BodyLabel("请设置极坐标的实际数值:", self)
        layout.addWidget(info_label)

        # 显示校准点信息
        info_text = BodyLabel(
            f"原点: ({self._calibration.x_start.x():.1f}, {self._calibration.x_start.y():.1f})\n"
            f"角度和极径点A: ({self._calibration.x_end.x():.1f}, {self._calibration.x_end.y():.1f})",
            self
        )
        info_text.setStyleSheet("color: gray; padding: 10px; background: #f0f0f0; border-radius: 5px;")
        layout.addWidget(info_text)

        form = QFormLayout()

        # 点A的角度
        self._angle_input = LineEdit("0", self)
        form.addRow("点A的角度 (度):", self._angle_input)

        # 点A的极径
        self._radius_input = LineEdit("1", self)
        form.addRow("点A的极径:", self._radius_input)

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
            "angle_A": float(self._angle_input.text()),
            "radius_A": float(self._radius_input.text()),
            "coord_type": "polar"
        }
