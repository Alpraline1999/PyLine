from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPixmap, QImage, QPainter, QWheelEvent, QMouseEvent, QResizeEvent


class ImageViewer(QWidget):
    """图片查看器 - 支持缩放/平移/拖放"""

    image_loaded = Signal(str)  # 图片加载信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._scale = 1.0
        self._min_scale = 0.1
        self._max_scale = 10.0
        self._pan = False
        self._pan_start = QPointF()
        self._offset = QPointF()
        self._drag_pos = QPointF()
        self.setup_ui()

    def setup_ui(self):
        """初始化界面"""
        self.setAcceptDrops(True)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #2d2d2d;" if self._is_dark_mode() else "background-color: #f5f5f5;")

    def _is_dark_mode(self):
        """检测是否为深色模式"""
        from qfluentwidgets import isDarkTheme
        return isDarkTheme()

    def load_image(self, file_path: str) -> bool:
        """加载图片"""
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return False
        self._pixmap = pixmap
        self._scale = 1.0
        self._offset = QPointF()
        self.update()
        self.image_loaded.emit(file_path)
        return True

    def clear_image(self):
        """清除图片"""
        self._pixmap = None
        self._scale = 1.0
        self._offset = QPointF()
        self.update()

    def zoom_in(self):
        """放大"""
        self._scale = min(self._scale * 1.2, self._max_scale)
        self.update()

    def zoom_out(self):
        """缩小"""
        self._scale = max(self._scale / 1.2, self._min_scale)
        self.update()

    def zoom_reset(self):
        """重置缩放"""
        self._scale = 1.0
        self._offset = QPointF()
        self.update()

    def fit_to_window(self):
        """适应窗口大小"""
        if self._pixmap is None:
            return
        self._scale = min(
            self.width() / self._pixmap.width(),
            self.height() / self._pixmap.height()
        )
        self._offset = QPointF()
        self.update()

    def paintEvent(self, event):
        """绘制图片"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 填充背景
        bg_color = "#2d2d2d" if self._is_dark_mode() else "#f5f5f5"
        painter.fillRect(self.rect(), bg_color)

        if self._pixmap is None:
            # 显示占位文字
            painter.setPen(Qt.GlobalColor.gray)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "拖放图片到此处\n或使用 文件 > 打开")
            return

        # 保存 painter 状态
        painter.save()

        # 移动到中心并应用缩放
        center = self.rect().center()
        painter.translate(center + self._offset)
        painter.scale(self._scale, self._scale)
        painter.translate(-self._pixmap.rect().center())

        # 绘制图片
        painter.drawPixmap(self._pixmap.rect(), self._pixmap)

        painter.restore()

        # 绘制缩放比例
        scale_text = f"{int(self._scale * 100)}%"
        painter.setPen(Qt.GlobalColor.gray)
        painter.drawText(self.rect().adjusted(0, 0, -10, -10), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, scale_text)

    def wheelEvent(self, event: QWheelEvent):
        """鼠标滚轮缩放"""
        if self._pixmap is None:
            return

        angle = event.angleDelta().y()
        if angle > 0:
            self._scale = min(self._scale * 1.15, self._max_scale)
        else:
            self._scale = max(self._scale / 1.15, self._min_scale)
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._pan = True
            self._pan_start = event.position() - self._offset
        elif event.button() == Qt.MouseButton.RightButton:
            # 右键菜单预留
            pass

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动（平移）"""
        if self._pan and self._pixmap:
            self._offset = event.position() - self._pan_start
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._pan = False

    def dragEnterEvent(self, event):
        """拖拽进入"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """拖拽放下"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path:
                self.load_image(file_path)

    def resizeEvent(self, event: QResizeEvent):
        """窗口大小变化"""
        super().resizeEvent(event)
        self.update()
