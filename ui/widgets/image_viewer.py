from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QPixmap, QPainter, QWheelEvent, QMouseEvent, QResizeEvent, QPen, QColor, QBrush, QKeyEvent, QPainterPath


class CurvePoint:
    """曲线上的单个点"""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class CurveOverlayItem:
    """曲线覆盖层数据"""
    def __init__(self, color: str = "#0078D4", point_shape: str = "circle"):
        self.points: list = []  # 存储 (x, y) 元组
        self.color = color
        self.name = "曲线"
        self.point_shape = point_shape

    def add_point(self, x: float, y: float):
        self.points.append((x, y))


class MaskOverlay:
    """蒙版覆盖层"""
    def __init__(self):
        self.enabled = False
        self.include_mode = True  # True=包含模式, False=排除模式
        self.polygons = []  # 多边形列表，每个多边形是 [(x,y), ...] 点列表

    def reset(self):
        self.enabled = False
        self.polygons.clear()

    def add_polygon(self, polygon):
        self.polygons.append(polygon)
        self.enabled = True

    def is_point_inside(self, x: float, y: float) -> bool:
        """检查点是否在蒙版内"""
        if not self.enabled or not self.polygons:
            return True  # 无蒙版时默认包含

        inside = False
        for polygon in self.polygons:
            if self._point_in_polygon(x, y, polygon):
                inside = True
                break
        return inside if self.include_mode else not inside

    def _point_in_polygon(self, x: float, y: float, polygon) -> bool:
        """射线法判断点是否在多边形内"""
        n = len(polygon)
        if n < 3:
            return False
        inside = False
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def clear_points(self):
        self.points.clear()

    def get_points(self):
        return self.points


class CalibrationOverlay:
    """校准点覆盖层

    四个标定点：
    - x起点: X轴起点 (对应x_range[0])
    - x终点: X轴终点 (对应x_range[1])
    - y起点: Y轴起点 (对应y_range[0])
    - y终点: Y轴终点 (对应y_range[1])
    """
    def __init__(self):
        self.x_start = None   # QPointF - X轴起点
        self.x_end = None     # QPointF - X轴终点
        self.y_start = None   # QPointF - Y轴起点
        self.y_end = None     # QPointF - Y轴终点
        self.x_range = (0.0, 1.0)
        self.y_range = (0.0, 1.0)
        self.coord_type = "linear"

    def reset(self):
        self.x_start = None
        self.x_end = None
        self.y_start = None
        self.y_end = None

    def is_complete(self) -> bool:
        return (self.x_start is not None and self.x_end is not None and
                self.y_start is not None and self.y_end is not None)

    def next_point_type(self) -> str:
        """返回下一个要设置的点的类型"""
        if self.x_start is None:
            return "x_start"
        elif self.x_end is None:
            return "x_end"
        elif self.y_start is None:
            return "y_start"
        elif self.y_end is None:
            return "y_end"
        return "complete"

    def get_current_point(self) -> QPointF:
        """获取当前正在编辑的点"""
        if self.x_start is None:
            return self.x_start
        elif self.x_end is None:
            return self.x_end
        elif self.y_start is None:
            return self.y_start
        elif self.y_end is None:
            return self.y_end
        return None

    def set_current_point(self, pos: QPointF):
        """设置当前正在编辑的点"""
        if self.x_start is None:
            self.x_start = pos
        elif self.x_end is None:
            self.x_end = pos
        elif self.y_start is None:
            self.y_start = pos
        elif self.y_end is None:
            self.y_end = pos

    def nudge_current_point(self, dx: float, dy: float):
        """微调当前正在设置的点"""
        if self.x_start is None:
            pass
        elif self.x_end is None:
            self.x_start = QPointF(self.x_start.x() + dx, self.x_start.y() + dy)
        elif self.y_start is None:
            self.x_end = QPointF(self.x_end.x() + dx, self.x_end.y() + dy)
        elif self.y_end is None:
            self.y_start = QPointF(self.y_start.x() + dx, self.y_start.y() + dy)
        else:
            self.y_end = QPointF(self.y_end.x() + dx, self.y_end.y() + dy)



class ImageViewer(QWidget):
    """图片查看器 - 支持缩放/平移/拖放"""

    image_loaded = Signal(str)  # 图片加载信号
    calibration_complete = Signal(object)  # 校准完成信号，发送 CalibrationOverlay
    curve_point_added = Signal(float, float)  # 曲线点添加信号 (x, y 像素坐标)
    calibration_step = Signal(str)  # 校准步骤信号，发送下一个需要设置的点类型
    calibration_nudge = Signal(float, float)  # 微调信号 (dx, dy)
    eraser_point = Signal(float, float)  # 橡皮擦信号 (x, y 像素坐标)
    toggle_eraser_mode = Signal()  # 切换橡皮擦模式信号
    mask_changed = Signal()  # 蒙版改变信号

    # 工具模式
    MODE_SELECT = "select"
    MODE_CALIBRATE = "calibrate"
    MODE_EXTRACT = "extract"
    MODE_ERASER = "eraser"
    MODE_BOX_MASK = "box_mask"
    MODE_BRUSH_MASK = "brush_mask"

    # 默认配置
    DEFAULT_POINT_SIZE = 8.0
    DEFAULT_NUDGE_STEP = 3.0

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

        # 覆盖层
        self._curve_items: list = []  # CurveOverlayItem 列表
        self._current_curve: CurveOverlayItem = None  # 当前正在绘制的曲线
        self._calibration = CalibrationOverlay()
        self._curves_visible: bool = True  # 曲线可见性

        # 工具模式
        self._current_tool = self.MODE_SELECT

        # 校准状态
        self._calibration_step_hint = ""

        # 配置参数
        self._point_size = self.DEFAULT_POINT_SIZE
        self._nudge_step = self.DEFAULT_NUDGE_STEP
        self._eraser_size = 20.0

        # 蒙版
        self._mask = MaskOverlay()
        self._mask_start_point = None
        self._mask_current_polygon = []

        # 鼠标位置(图片坐标)
        self._mouse_image_pos = None

        self.setup_ui()

    def setup_ui(self):
        """初始化界面"""
        self.setAcceptDrops(True)
        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _bg_color(self):
        """获取背景颜色"""
        from qfluentwidgets import isDarkTheme
        return "#2d2d2d" if isDarkTheme() else "#f5f5f5"

    # ==================== 配置方法 ====================

    def set_point_size(self, size: float):
        """设置点的大小"""
        self._point_size = max(1.0, size)
        self.update()

    def get_point_size(self) -> float:
        """获取点的大小"""
        return self._point_size

    def set_nudge_step(self, step: float):
        """设置微调步长（像素）"""
        self._nudge_step = max(1.0, step)

    def get_nudge_step(self) -> float:
        """获取微调步长"""
        return self._nudge_step

    # ==================== 图片加载 ====================

    def load_image(self, file_path: str) -> bool:
        """加载图片"""
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return False
        self._pixmap = pixmap
        self._scale = 1.0
        self._offset = QPointF()
        self.fit_to_window()
        self.update()
        self.image_loaded.emit(file_path)
        return True

    def clear_image(self):
        """清除图片"""
        self._pixmap = None
        self._scale = 1.0
        self._offset = QPointF()
        self._curve_items.clear()
        self._current_curve = None
        self._calibration.reset()
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
        fit_scale = min(
            self.width() / self._pixmap.width(),
            self.height() / self._pixmap.height()
        )
        self._scale = fit_scale
        self._min_scale = fit_scale
        self._offset = QPointF()
        self.update()

    # ==================== 工具模式控制 ====================

    def set_select_mode(self):
        """切换到选择模式"""
        self._current_tool = self.MODE_SELECT
        self._calibration_step_hint = ""
        self.update()

    def set_calibrate_mode(self):
        """切换到校准模式"""
        self._current_tool = self.MODE_CALIBRATE
        # 不再进入时重置，保留当前校准坐标直到校准完成
        next_type = self._calibration.next_point_type()
        if next_type != "complete":
            hint_map = {
                "x_start": "点击设置 X 轴起点",
                "x_end": "点击设置 X 轴终点",
                "y_start": "点击设置 Y 轴起点",
                "y_end": "点击设置 Y 轴终点"
            }
            self._calibration_step_hint = hint_map.get(next_type, "")
            self.calibration_step.emit(next_type)
        self.update()

    def set_extract_mode(self):
        """切换到曲线提取模式"""
        self._current_tool = self.MODE_EXTRACT
        self._calibration_step_hint = ""
        self._current_curve = CurveOverlayItem()
        self.update()

    def set_eraser_mode(self):
        """切换到橡皮擦模式"""
        self._current_tool = self.MODE_ERASER
        self._calibration_step_hint = ""
        self.update()

    def set_box_mask_mode(self):
        """切换到框选蒙版模式"""
        self._current_tool = self.MODE_BOX_MASK
        self._calibration_step_hint = ""
        self._mask.reset()
        self.update()

    def set_brush_mask_mode(self):
        """切换到画笔蒙版模式"""
        self._current_tool = self.MODE_BRUSH_MASK
        self._calibration_step_hint = ""
        self._mask_current_polygon = []
        self.update()

    def set_eraser_size(self, size: float):
        """设置橡皮擦大小"""
        self._eraser_size = max(1.0, size)

    def get_eraser_size(self) -> float:
        """获取橡皮擦大小"""
        return getattr(self, '_eraser_size', 20.0)

    def get_mask(self) -> MaskOverlay:
        """获取蒙版"""
        return self._mask

    def get_current_tool(self) -> str:
        """获取当前工具模式"""
        return self._current_tool

    # ==================== 曲线操作 ====================

    def set_curve_items(self, items: list):
        """设置曲线覆盖层列表"""
        self._curve_items = items
        self.update()

    def add_curve_item(self, item: CurveOverlayItem):
        """添加曲线覆盖层"""
        self._curve_items.append(item)
        self.update()

    def clear_curves(self):
        """清除所有曲线"""
        self._curve_items.clear()
        self._current_curve = None
        self.update()

    def get_curves(self) -> list:
        """获取所有曲线"""
        return self._curve_items

    def set_curves_visible(self, visible: bool):
        """设置曲线是否可见"""
        self._curves_visible = visible
        self.update()

    def clear_curves(self):
        """清除所有曲线"""
        self._curve_items.clear()
        self._current_curve = None
        self.update()

    def get_current_curve(self) -> CurveOverlayItem:
        """获取当前曲线"""
        return self._current_curve

    # ==================== 校准操作 ====================

    def get_calibration(self) -> CalibrationOverlay:
        """获取校准数据"""
        return self._calibration

    def set_calibration(self, calibration: CalibrationOverlay):
        """设置校准数据"""
        self._calibration = calibration
        self.update()

    def _complete_calibration(self):
        """完成校准"""
        if self._calibration.is_complete():
            self.calibration_complete.emit(self._calibration)
            self._current_tool = self.MODE_SELECT

    # ==================== 坐标转换 ====================

    def _widget_to_image_coords(self, pos: QPointF) -> QPointF:
        """将窗口坐标转换为图片坐标"""
        center = self.rect().center()
        offset_x = center.x() + self._offset.x()
        offset_y = center.y() + self._offset.y()

        img_center_x = self._pixmap.rect().center().x()
        img_center_y = self._pixmap.rect().center().y()

        x = (pos.x() - offset_x) / self._scale + img_center_x
        y = (pos.y() - offset_y) / self._scale + img_center_y

        return QPointF(x, y)

    # ==================== 绘制 ====================

    def paintEvent(self, event):
        """绘制图片"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), self._bg_color())

        if self._pixmap is None:
            painter.setPen(Qt.GlobalColor.gray)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "拖放图片到此处\n或使用上方「添加图片」按钮")
            painter.end()
            return

        painter.save()

        center = self.rect().center()
        offset_x = center.x() + self._offset.x()
        offset_y = center.y() + self._offset.y()

        painter.translate(offset_x, offset_y)
        painter.scale(self._scale, self._scale)
        painter.translate(-self._pixmap.rect().center().x(), -self._pixmap.rect().center().y())

        painter.drawPixmap(self._pixmap.rect(), self._pixmap)

        self._draw_calibration_points(painter)
        if self._curves_visible:
            self._draw_curve_points(painter)

        self._draw_mask_overlay(painter)
        self._draw_eraser_cursor(painter)

        painter.restore()

        if self._calibration_step_hint:
            painter.setPen(QColor("#FFD700"))
            painter.drawText(self.rect().adjusted(10, 10, -10, -50),
                           Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                           self._calibration_step_hint)

        scale_text = f"{int(self._scale * 100)}%"
        painter.setPen(Qt.GlobalColor.gray)
        painter.drawText(self.rect().adjusted(0, 0, -10, -10),
                        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, scale_text)

        painter.end()

    def _draw_calibration_points(self, painter: QPainter):
        """绘制校准点"""
        if self._calibration.x_start is None:
            return

        # 获取图片尺寸用于绘制延伸到边缘的线
        if self._pixmap is None:
            return

        img_width = self._pixmap.width()
        img_height = self._pixmap.height()

        # X轴：垂直线 (取x坐标)
        pen_x = QPen(QColor("#4CAF50"))
        pen_x.setWidthF(2.0 / self._scale)
        painter.setPen(pen_x)

        # X轴起点垂直线
        x1 = self._calibration.x_start.x()
        painter.drawLine(QPointF(x1, 0), QPointF(x1, img_height))

        # X轴终点垂直线
        if self._calibration.x_end:
            x2 = self._calibration.x_end.x()
            painter.drawLine(QPointF(x2, 0), QPointF(x2, img_height))

        # Y轴：水平线 (取y坐标)
        pen_y = QPen(QColor("#2196F3"))
        pen_y.setWidthF(2.0 / self._scale)
        painter.setPen(pen_y)

        # Y轴起点水平线
        if self._calibration.y_start:
            y1 = self._calibration.y_start.y()
            painter.drawLine(QPointF(0, y1), QPointF(img_width, y1))

        # Y轴终点水平线
        if self._calibration.y_end:
            y2 = self._calibration.y_end.y()
            painter.drawLine(QPointF(0, y2), QPointF(img_width, y2))

        # 绘制校准点标记
        r = self._point_size / self._scale
        self._draw_point_marker(painter, self._calibration.x_start, "#FF5722", "Xs")
        if self._calibration.x_end:
            self._draw_point_marker(painter, self._calibration.x_end, "#4CAF50", "Xe")
        if self._calibration.y_start:
            self._draw_point_marker(painter, self._calibration.y_start, "#9C27B0", "Ys")
        if self._calibration.y_end:
            self._draw_point_marker(painter, self._calibration.y_end, "#2196F3", "Ye")

    def _draw_point_marker(self, painter: QPainter, pos: QPointF, color: str, label: str):
        """绘制点标记"""
        r = self._point_size / self._scale
        painter.setPen(QPen(QColor(color), 2.0 / self._scale))
        painter.setBrush(QBrush(QColor(color)))
        painter.drawEllipse(pos, r, r)

        font = painter.font()
        font.setPixelSize(int(12 / self._scale))
        painter.setFont(font)
        painter.drawText(pos + QPointF(r, -r), label)

    def _draw_curve_points(self, painter: QPainter):
        """绘制曲线点"""
        for curve_item in self._curve_items:
            self._draw_single_curve(painter, curve_item)

        if self._current_curve and self._current_curve.points:
            self._draw_single_curve(painter, self._current_curve)

    def _draw_single_curve(self, painter: QPainter, curve_item: CurveOverlayItem):
        """绘制单条曲线"""
        if not curve_item.points:
            return

        color = QColor(curve_item.color)
        r = self._point_size / self._scale
        painter.setPen(QPen(color, 2.0 / self._scale))
        painter.setBrush(QBrush(color))

        shape = getattr(curve_item, 'point_shape', 'circle')

        for px, py in curve_item.points:
            if shape == 'square':
                rect = QRectF(px - r, py - r, r * 2, r * 2)
                painter.drawRect(rect)
            elif shape == 'triangle':
                path = QPainterPath()
                path.moveTo(px, py - r)
                path.lineTo(px + r, py + r)
                path.lineTo(px - r, py + r)
                path.closeSubpath()
                painter.drawPath(path)
            elif shape == 'diamond':
                path = QPainterPath()
                path.moveTo(px, py - r)
                path.lineTo(px + r, py)
                path.lineTo(px, py + r)
                path.lineTo(px - r, py)
                path.closeSubpath()
                painter.drawPath(path)
            elif shape == 'inv_triangle':
                path = QPainterPath()
                path.moveTo(px, py + r)
                path.lineTo(px + r, py - r)
                path.lineTo(px - r, py - r)
                path.closeSubpath()
                painter.drawPath(path)
            elif shape == 'cross':
                pen_width = max(1.0, r * 0.3)
                painter.setPen(QPen(color, pen_width))
                painter.drawLine(QPointF(px - r, py - r), QPointF(px + r, py + r))
                painter.drawLine(QPointF(px + r, py - r), QPointF(px - r, py + r))
                painter.setPen(QPen(color, 2.0 / self._scale))
            elif shape == 'star':
                # 绘制星号(*)形状
                pen_width = max(1.0, r * 0.25)
                painter.setPen(QPen(color, pen_width))
                painter.drawLine(QPointF(px, py - r), QPointF(px, py + r))
                painter.drawLine(QPointF(px - r, py), QPointF(px + r, py))
                painter.drawLine(QPointF(px - r * 0.7, py - r * 0.7), QPointF(px + r * 0.7, py + r * 0.7))
                painter.drawLine(QPointF(px + r * 0.7, py - r * 0.7), QPointF(px - r * 0.7, py + r * 0.7))
                painter.setPen(QPen(color, 2.0 / self._scale))
            elif shape == 'pentagram':
                self._draw_star(painter, px, py, r, color, 5)
            else:  # circle
                painter.drawEllipse(QPointF(px, py), r, r)

    def _draw_star(self, painter: QPainter, cx: float, cy: float, r: float, color: QColor, points: int = 5):
        """绘制五角星"""
        import math
        path = QPainterPath()
        inner_r = r * 0.4
        angle_offset = -math.pi / 2

        for i in range(points * 2):
            radius = r if i % 2 == 0 else inner_r
            angle = angle_offset + (i * math.pi / points)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        painter.drawPath(path)

    def _draw_mask_overlay(self, painter: QPainter):
        """绘制蒙版覆盖层"""
        if self._pixmap is None:
            return

        # 绘制已有多边形
        if self._mask.polygons:
            pen = QPen(QColor("#FF9800"))
            pen.setWidthF(2.0 / self._scale)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor("#40FF9800")))

            for polygon in self._mask.polygons:
                if len(polygon) >= 3:
                    points = [QPointF(p[0], p[1]) for p in polygon]
                    path = QPainterPath()
                    path.moveTo(points[0])
                    for p in points[1:]:
                        path.lineTo(p)
                    path.closeSubpath()
                    painter.drawPath(path)

        # 绘制当前正在绘制的多边形
        if self._mask_current_polygon and len(self._mask_current_polygon) >= 2:
            pen = QPen(QColor("#FF5722"))
            pen.setWidthF(2.0 / self._scale)
            painter.setPen(pen)
            points = self._mask_current_polygon
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])

        # 绘制框选蒙版的起始点
        if self._mask_start_point:
            pen = QPen(QColor("#FF5722"))
            pen.setWidthF(2.0 / self._scale)
            painter.setPen(pen)
            r = self._point_size / self._scale
            painter.setBrush(QBrush(QColor("#40FF5722")))
            painter.drawEllipse(self._mask_start_point, r * 2, r * 2)

    def _draw_eraser_cursor(self, painter: QPainter):
        """绘制橡皮擦光标"""
        if self._mouse_image_pos is None:
            return

        if self._current_tool == self.MODE_ERASER:
            pen = QPen(QColor("#F44336"))
            pen.setWidthF(2.0 / self._scale)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor("#20F44336")))
            r = self._eraser_size
            painter.drawEllipse(self._mouse_image_pos, r, r)

    # ==================== 键盘事件 ====================

    def keyPressEvent(self, event: QKeyEvent):
        """键盘按下 - 支持方向键和WASD微调"""
        if self._current_tool == self.MODE_CALIBRATE:
            dx = 0
            dy = 0

            if event.key() in (Qt.Key_Left, Qt.Key_A):
                dx = -self._nudge_step
            elif event.key() in (Qt.Key_Right, Qt.Key_D):
                dx = self._nudge_step
            elif event.key() in (Qt.Key_Up, Qt.Key_W):
                dy = -self._nudge_step
            elif event.key() in (Qt.Key_Down, Qt.Key_S):
                dy = self._nudge_step
            else:
                super().keyPressEvent(event)
                return

            self._calibration.nudge_current_point(dx, dy)
            self.calibration_nudge.emit(dx, dy)
            self.update()
        elif self._current_tool in (self.MODE_EXTRACT, self.MODE_ERASER):
            # E键切换橡皮擦和提取模式
            if event.key() == Qt.Key_E:
                self.toggle_eraser_mode.emit()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    # ==================== 鼠标事件 ====================

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下"""
        if self._pixmap is None:
            return

        pos = event.position()

        if self._current_tool == self.MODE_CALIBRATE:
            self._handle_calibrate_click(pos)
        elif self._current_tool == self.MODE_EXTRACT:
            self._handle_extract_click(pos)
        elif self._current_tool == self.MODE_ERASER:
            if event.button() == Qt.MouseButton.LeftButton:
                self._handle_eraser_click(pos)
        elif self._current_tool == self.MODE_BOX_MASK:
            if event.button() == Qt.MouseButton.LeftButton:
                self._mask_start_point = self._widget_to_image_coords(pos)
        elif self._current_tool == self.MODE_BRUSH_MASK:
            if event.button() == Qt.MouseButton.LeftButton:
                self._mask_current_polygon = [self._widget_to_image_coords(pos)]
        elif self._current_tool == self.MODE_SELECT:
            if event.button() == Qt.MouseButton.LeftButton:
                self._pan = True
                self._pan_start = pos - self._offset

    def _handle_eraser_click(self, pos: QPointF):
        """处理橡皮擦点击"""
        img_pos = self._widget_to_image_coords(pos)
        self.eraser_point.emit(img_pos.x(), img_pos.y())

    def _handle_calibrate_click(self, pos: QPointF):
        """处理校准模式点击"""
        img_pos = self._widget_to_image_coords(pos)
        next_type = self._calibration.next_point_type()

        if next_type == "x_start":
            self._calibration.x_start = img_pos
            self._calibration_step_hint = "点击设置 X 轴终点"
            self.calibration_step.emit("x_end")
        elif next_type == "x_end":
            self._calibration.x_end = img_pos
            self._calibration_step_hint = "点击设置 Y 轴起点"
            self.calibration_step.emit("y_start")
        elif next_type == "y_start":
            self._calibration.y_start = img_pos
            self._calibration_step_hint = "点击设置 Y 轴终点"
            self.calibration_step.emit("y_end")
        elif next_type == "y_end":
            self._calibration.y_end = img_pos
            self._calibration_step_hint = "校准完成!"
            self.calibration_step.emit("complete")
            self._complete_calibration()

        self.update()

    def _handle_extract_click(self, pos: QPointF):
        """处理曲线提取模式点击"""
        img_pos = self._widget_to_image_coords(pos)

        if self._current_curve is None:
            self._current_curve = CurveOverlayItem()

        self._current_curve.add_point(img_pos.x(), img_pos.y())
        self.curve_point_added.emit(img_pos.x(), img_pos.y())
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动（平移）"""
        # 跟踪鼠标位置
        if self._pixmap:
            self._mouse_image_pos = self._widget_to_image_coords(event.position())
        else:
            self._mouse_image_pos = None

        if self._pan and self._pixmap and self._current_tool == self.MODE_SELECT:
            new_offset = event.position() - self._pan_start
            self._offset = self._clamp_offset(new_offset)
            self.update()
        elif self._current_tool == self.MODE_ERASER and event.buttons() & Qt.MouseButton.LeftButton:
            # 橡皮擦模式下的拖动
            pos = event.position()
            img_pos = self._widget_to_image_coords(pos)
            self.eraser_point.emit(img_pos.x(), img_pos.y())
        elif self._current_tool == self.MODE_BRUSH_MASK and event.buttons() & Qt.MouseButton.LeftButton:
            # 画笔蒙版模式下的拖动
            self._mask_current_polygon.append(self._widget_to_image_coords(event.position()))
            self.update()
        elif self._current_tool in (self.MODE_ERASER, self.MODE_BOX_MASK, self.MODE_BRUSH_MASK):
            # 这些模式下需要重绘以显示鼠标位置
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._pan = False
            if self._current_tool == self.MODE_BOX_MASK and self._mask_start_point:
                # 框选蒙版完成
                end_point = self._widget_to_image_coords(event.position())
                x1, y1 = self._mask_start_point.x(), self._mask_start_point.y()
                x2, y2 = end_point.x(), end_point.y()
                # 创建矩形多边形
                polygon = [(min(x1, x2), min(y1, y2)),
                          (max(x1, x2), min(y1, y2)),
                          (max(x1, x2), max(y1, y2)),
                          (min(x1, x2), max(y1, y2))]
                self._mask.add_polygon(polygon)
                self.mask_changed.emit()
                self._mask_start_point = None
                self.update()
            elif self._current_tool == self.MODE_BRUSH_MASK and self._mask_current_polygon:
                # 画笔蒙版完成
                if len(self._mask_current_polygon) >= 3:
                    points = [(p.x(), p.y()) for p in self._mask_current_polygon]
                    self._mask.add_polygon(points)
                    self.mask_changed.emit()
                self._mask_current_polygon = []
                self.update()

    def wheelEvent(self, event: QWheelEvent):
        """鼠标滚轮缩放"""
        if self._pixmap is None:
            return

        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_in()
        elif delta < 0:
            self.zoom_out()

    def _clamp_offset(self, offset: QPointF) -> QPointF:
        """限制偏移量使图片不超过窗口边界"""
        if self._pixmap is None:
            return offset

        scaled_width = self._pixmap.width() * self._scale
        scaled_height = self._pixmap.height() * self._scale

        max_offset_x = max(0, (scaled_width - self.width()) / 2)
        max_offset_y = max(0, (scaled_height - self.height()) / 2)

        clamped_x = max(-max_offset_x, min(offset.x(), max_offset_x))
        clamped_y = max(-max_offset_y, min(offset.y(), max_offset_y))

        return QPointF(clamped_x, clamped_y)

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
        if self._pixmap:
            self.fit_to_window()
