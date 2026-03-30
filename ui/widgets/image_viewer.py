from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import BodyLabel
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

    def get_polygon_at_point(self, x: float, y: float) -> int:
        """检查哪个蒙版多边形包含指定点，返回多边形索引，不存在返回-1"""
        if not self.enabled or not self.polygons:
            return -1

        for idx, polygon in enumerate(self.polygons):
            if self._point_in_polygon(x, y, polygon):
                return idx
        return -1

    def remove_polygon_at_point(self, x: float, y: float, radius: float) -> bool:
        """删除与橡皮擦区域相交的多边形（用于橡皮擦），成功删除返回True"""
        if not self.enabled or not self.polygons:
            return False

        for idx, polygon in enumerate(self.polygons):
            # 检查是否与橡皮擦区域相交
            if self._polygon_circle_intersect(polygon, x, y, radius):
                del self.polygons[idx]
                return True
        return False

    def _polygon_circle_intersect(self, polygon, cx: float, cy: float, r: float) -> bool:
        """检查多边形是否与圆相交"""
        # 检查是否有顶点在圆内
        for px, py in polygon:
            dx = px - cx
            dy = py - cy
            if dx * dx + dy * dy <= r * r:
                return True

        # 检查圆心是否在多边形内
        if self._point_in_polygon(cx, cy, polygon):
            return True

        # 检查圆是否与多边形的任意边相交
        n = len(polygon)
        for i in range(n):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % n]
            if self._circle_segment_intersect(cx, cy, r, p1, p2):
                return True

        return False

    def _circle_segment_intersect(self, cx: float, cy: float, r: float, p1: tuple, p2: tuple) -> bool:
        """检查圆是否与线段相交"""
        # 向量从p1到p2
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]

        # 线段长度平方
        len_sq = dx * dx + dy * dy
        if len_sq == 0:
            return False

        # 圆心到线段起点的向量
        fx = p1[0] - cx
        fy = p1[1] - cy

        # 计算投影
        t = max(0, min(1, -(fx * dx + fy * dy) / len_sq))

        # 最近点
        nearest_x = p1[0] + t * dx
        nearest_y = p1[1] + t * dy

        # 圆心到最近点的距离
        dx_n = nearest_x - cx
        dy_n = nearest_y - cy
        dist_sq = dx_n * dx_n + dy_n * dy_n

        return dist_sq <= r * r

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

    线性/对数坐标系的四个标定点：
    - x_start: X轴起点 (对应x_range[0])
    - x_end: X轴终点 (对应x_range[1])
    - y_start: Y轴起点 (对应y_range[0])
    - y_end: Y轴终点 (对应y_range[1])

    极坐标系的四个标定点：
    - origin: 原点(极点)
    - angle_point1: A点(自定义角度θ1)
    - angle_point2: B点(自定义角度θ2)
    - radius_point: C点(自定义极径r1)
    """
    def __init__(self):
        self.x_start = None   # QPointF - X轴起点 或 原点(极坐标)
        self.x_end = None     # QPointF - X轴终点 或 A点-角度θ1(极坐标)
        self.y_start = None   # QPointF - Y轴起点 或 B点-角度θ2(极坐标)
        self.y_end = None     # QPointF - Y轴终点 或 C点-极径r1(极坐标)
        self.x_range = (0.0, 1.0)
        self.y_range = (0.0, 1.0)
        self.coord_type = "linear"

    def reset(self):
        self.x_start = None
        self.x_end = None
        self.y_start = None
        self.y_end = None
        self.coord_type = "linear"
        self.x_range = (0.0, 1.0)
        self.y_range = (0.0, 1.0)

    def is_complete(self) -> bool:
        if self.coord_type == "polar":
            # 极坐标只需要2个点：原点和角度极径点
            return self.x_start is not None and self.x_end is not None
        else:
            # 线性/对数坐标需要4个点
            return (self.x_start is not None and self.x_end is not None and
                    self.y_start is not None and self.y_end is not None)

    def next_point_type(self) -> str:
        """返回下一个要设置的点的类型"""
        if self.coord_type == "polar":
            # 极坐标使用 2 点: origin, angle_radius_point
            if self.x_start is None:
                return "origin"
            elif self.x_end is None:
                return "angle_radius_point"
            return "complete"
        else:
            # 线性/对数坐标使用 x_start, x_end, y_start, y_end
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
        if self.coord_type == "polar":
            # 极坐标使用 2 点: origin, angle_radius_point
            if self.x_start is None:
                return self.x_start
            elif self.x_end is None:
                return self.x_end
        else:
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
        if self.coord_type == "polar":
            # 极坐标使用 2 点: origin, angle_radius_point
            if self.x_start is None:
                self.x_start = pos  # origin
            elif self.x_end is None:
                self.x_end = pos    # angle_radius_point
        else:
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
        if self.coord_type == "polar":
            # 极坐标: origin, angle_radius_point
            if self.x_start is None:
                pass
            elif self.x_end is None:
                self.x_start = QPointF(self.x_start.x() + dx, self.x_start.y() + dy)
            else:
                self.x_end = QPointF(self.x_end.x() + dx, self.x_end.y() + dy)
        else:
            # 线性/对数坐标
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
    curve_point_moved = Signal(int, float, float)  # 曲线点移动信号 (index, x, y 像素坐标)
    calibration_step = Signal(str)  # 校准步骤信号，发送下一个需要设置的点类型
    calibration_nudge = Signal(float, float)  # 微调信号 (dx, dy)
    eraser_point = Signal(float, float)  # 橡皮擦信号 (x, y 像素坐标)
    toggle_eraser_mode = Signal()  # 切换橡皮擦模式信号
    mask_changed = Signal()  # 蒙版改变信号
    mask_about_to_add = Signal(object)  # 蒙版即将添加信号，携带多边形数据
    color_picked = Signal(object)  # 取色信号，发送 QColor
    file_dropped = Signal(str)  # 文件拖入信号，发送文件路径
    assisted_region_selected = Signal(float, float, float, float)  # 辅助选点区域信号 (x1,y1,x2,y2)
    mouse_moved = Signal(float, float)  # 鼠标移动信号 (x, y 图片像素坐标)

    # 工具模式
    MODE_SELECT = "select"
    MODE_CALIBRATE = "calibrate"
    MODE_EXTRACT = "extract"
    MODE_ERASER = "eraser"
    MODE_BOX_MASK = "box_mask"
    MODE_BRUSH_MASK = "brush_mask"
    MODE_COLOR_PICK = "color_pick"
    MODE_ASSISTED = "assisted"

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
        self._eraser_pressed = False
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

        # 曲线点选中/微调
        self._selected_point_index: int = -1
        self._point_nudge_mode: bool = False

        # 校准状态
        self._calibration_step_hint = ""

        # 配置参数
        self._point_size = self.DEFAULT_POINT_SIZE
        self._nudge_step = self.DEFAULT_NUDGE_STEP
        self._eraser_size = 20.0

        # 蒙版
        self._mask = MaskOverlay()
        self._mask_start_point = None
        self._mask_drag_current = None   # 框选蒙版拖动时的当前端点
        self._mask_current_polygon = []  # 画笔蒙版笔触点列表（QPointF）
        self._brush_painting = False     # 画笔蒙版是否正在按下绘制
        self._brush_last_pt = None       # 画笔蒙版上次圆心位置（用于间距控制）

        # 预览点（自动检测结果）
        self._preview_points: list = []

        # 当前图片路径
        self._image_path: str = ""

        # 辅助选点（两次点击定义矩形区域）
        self._assist_point1 = None   # QPointF - 第一次点击
        self._assist_shape = "rect"  # "rect" 或 "ellipse"

        # 鼠标位置(图片坐标)
        self._mouse_image_pos = None

        self.setup_ui()

    def setup_ui(self):
        """初始化界面"""
        self.setAcceptDrops(True)
        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)  # 鼠标移动时无需按下按键即可触发 mouseMoveEvent

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

    def event(self, ev):
        """拦截 ShortcutOverride，在提取/校准模式下预先主张方向键和WASD"""
        from PySide6.QtCore import QEvent
        if ev.type() == QEvent.Type.ShortcutOverride:
            mods = ev.modifiers()
            plain = not (mods & Qt.KeyboardModifier.ControlModifier or
                         mods & Qt.KeyboardModifier.AltModifier or
                         mods & Qt.KeyboardModifier.MetaModifier)
            if plain and self._current_tool in (self.MODE_EXTRACT, self.MODE_CALIBRATE):
                if ev.key() in (
                    Qt.Key.Key_Left, Qt.Key.Key_Right,
                    Qt.Key.Key_Up,   Qt.Key.Key_Down,
                    Qt.Key.Key_W,    Qt.Key.Key_A,
                    Qt.Key.Key_S,    Qt.Key.Key_D,
                    Qt.Key.Key_E,    Qt.Key.Key_Escape,
                ):
                    ev.accept()
                    return True
        return super().event(ev)

    def load_image(self, file_path: str) -> bool:
        """加载图片"""
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return False
        self._pixmap = pixmap
        self._image_path = file_path
        self._scale = 1.0
        self._offset = QPointF()
        self.fit_to_window()
        self.update()
        self.image_loaded.emit(file_path)
        return True

    def clear_image(self):
        """清除图片"""
        self._pixmap = None
        self._image_path = ""
        self._scale = 1.0
        self._offset = QPointF()
        self._curve_items.clear()
        self._current_curve = None
        self._preview_points = []
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
        # 清除当前提取的曲线点，避免在非提取模式下显示
        self._current_curve = None
        self.update()

    def set_calibrate_mode(self, coord_type: str = "linear"):
        """切换到校准模式"""
        self._current_tool = self.MODE_CALIBRATE
        self._calibration.coord_type = coord_type
        # 不再进入时重置，保留当前校准坐标直到校准完成
        next_type = self._calibration.next_point_type()
        if next_type != "complete":
            if coord_type == "polar":
                hint_map = {
                    "origin": "点击设置原点",
                    "angle_radius_point": "点击设置角度和极径点A"
                }
            else:
                hint_map = {
                    "x_start": "点击设置 X 轴起点",
                    "x_end": "点击设置 X 轴终点",
                    "y_start": "点击设置 Y 轴起点",
                    "y_end": "点击设置 Y 轴终点"
                }
            self._calibration_step_hint = hint_map.get(next_type, "")
            self.calibration_step.emit(next_type)
        self.update()

    def set_extract_mode(self, color: str = "#0078D4", point_shape: str = "circle"):
        """切换到曲线提取模式"""
        self._current_tool = self.MODE_EXTRACT
        self._calibration_step_hint = ""
        self._current_curve = CurveOverlayItem(color=color, point_shape=point_shape)
        self._selected_point_index = -1
        self._point_nudge_mode = False
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
        """切换到画笔蒙版模式（涂刷式）"""
        self._current_tool = self.MODE_BRUSH_MASK
        self._calibration_step_hint = ""
        self._mask_current_polygon = []
        self.update()

    def set_assisted_mode(self, shape: str = "rect"):
        """切换到辅助选点模式（两次点击定区域）"""
        self._current_tool = self.MODE_ASSISTED
        self._calibration_step_hint = ""
        self._assist_point1 = None
        self._assist_shape = shape
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

    def get_image_path(self) -> str:
        """获取当前图片路径"""
        return self._image_path

    def set_preview_points(self, points: list) -> None:
        """设置预览点（自动检测结果），格式 [(x, y), ...]"""
        self._preview_points = list(points)
        self.update()

    def clear_preview_points(self) -> None:
        """清除预览点"""
        self._preview_points = []
        self.update()

    def get_preview_points(self) -> list:
        """获取预览点列表"""
        return self._preview_points

    def set_color_pick_mode(self) -> None:
        """切换到取色模式"""
        self._current_tool = self.MODE_COLOR_PICK
        self._calibration_step_hint = ""
        self.update()

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

        self._draw_preview_points(painter)
        self._draw_mask_overlay(painter)
        self._draw_eraser_cursor(painter)
        self._draw_assisted_preview(painter)

        painter.restore()

        if self._calibration_step_hint:
            painter.setPen(QColor("#FFD700"))
            painter.drawText(self.rect().adjusted(10, 10, -10, -50),
                           Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                           self._calibration_step_hint)

        if self._current_tool == self.MODE_COLOR_PICK:
            painter.setPen(QColor("#FFD700"))
            painter.drawText(self.rect().adjusted(10, 10, -10, -50),
                           Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                           "取色模式：点击图片上的曲线颜色")

        if self._current_tool == self.MODE_ASSISTED:
            painter.setPen(QColor("#FFD700"))
            hint = ("辅助选点：点击第二个端点，自动提取两点间区域的曲线"
                    if self._assist_point1 is not None
                    else "辅助选点：点击第一个端点（矩形/椭圆区域起点）")
            painter.drawText(self.rect().adjusted(10, 10, -10, -50),
                           Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                           hint)

        scale_text = f"{int(self._scale * 100)}%"
        painter.setPen(Qt.GlobalColor.gray)
        painter.drawText(self.rect().adjusted(0, 0, -10, -10),
                        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, scale_text)

        painter.end()

    def _draw_calibration_points(self, painter: QPainter):
        """绘制校准点"""
        if self._calibration.x_start is None:
            return

        if self._pixmap is None:
            return

        # ── 极坐标：十字标记 + 连线 ──────────────────────────────────────
        if self._calibration.coord_type == "polar":
            arm = 14.0 / self._scale
            pen = QPen(QColor("#FF9800"))
            pen.setWidthF(1.5 / self._scale)
            painter.setPen(pen)

            origin_pt = self._calibration.x_start
            a_pt = self._calibration.x_end

            # 十字：原点
            ox, oy = origin_pt.x(), origin_pt.y()
            painter.drawLine(QPointF(ox - arm, oy), QPointF(ox + arm, oy))
            painter.drawLine(QPointF(ox, oy - arm), QPointF(ox, oy + arm))

            if a_pt:
                # 十字：A 点
                ax, ay = a_pt.x(), a_pt.y()
                painter.drawLine(QPointF(ax - arm, ay), QPointF(ax + arm, ay))
                painter.drawLine(QPointF(ax, ay - arm), QPointF(ax, ay + arm))

                # 两点连线
                pen_line = QPen(QColor("#FF9800"))
                pen_line.setWidthF(1.5 / self._scale)
                pen_line.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen_line)
                painter.drawLine(origin_pt, a_pt)

            # 标记标签
            self._draw_point_marker(painter, origin_pt, "#FF5722", "O")
            if a_pt:
                self._draw_point_marker(painter, a_pt, "#4CAF50", "A")
            return

        # ── 线性/对数：纵横延长线 ────────────────────────────────────────
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

        # 只在提取模式下绘制当前正在提取的曲线
        if self._current_tool == self.MODE_EXTRACT and self._current_curve and self._current_curve.points:
            sel_idx = self._selected_point_index if self._point_nudge_mode else -1
            self._draw_single_curve(painter, self._current_curve, selected_index=sel_idx)

    def _draw_single_curve(self, painter: QPainter, curve_item: CurveOverlayItem, selected_index: int = -1):
        """绘制单条曲线"""
        if not curve_item.points:
            return

        color = QColor(curve_item.color)
        r = self._point_size / self._scale
        painter.setPen(QPen(color, 2.0 / self._scale))
        painter.setBrush(QBrush(color))

        shape = getattr(curve_item, 'point_shape', 'circle')

        for idx, (px, py) in enumerate(curve_item.points):
            # 选中点：外圈高亮
            if idx == selected_index:
                ring_r = r * 2.2
                painter.save()
                painter.setPen(QPen(QColor("#FFD700"), 2.0 / self._scale))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(px, py), ring_r, ring_r)
                painter.restore()
                painter.setPen(QPen(color, 2.0 / self._scale))
                painter.setBrush(QBrush(color))
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

    def _draw_preview_points(self, painter: QPainter):
        """绘制预览点（自动检测结果，黄色空心圆）"""
        if not self._preview_points:
            return
        r = max(2.0, self._point_size * 0.7) / self._scale
        pen = QPen(QColor("#FFD700"))
        pen.setWidthF(1.5 / self._scale)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for px, py in self._preview_points:
            painter.drawEllipse(QPointF(px, py), r, r)

    def _draw_mask_overlay(self, painter: QPainter):
        """绘制蒙版覆盖层（合并渲染，统一透明度；颜色随 include_mode 变化）"""
        if self._pixmap is None:
            return

        if self._mask.polygons:
            # 根据 include_mode 选色:
            #   include_mode=True  (感兴趣区域, 蒙版外不识别): 橙色
            #   include_mode=False (屏蔽区域, 蒙版内不识别):   蓝色
            if self._mask.include_mode:
                stroke_color = QColor("#FF9800")
                fill_color   = QColor("#50FF9800")
            else:
                stroke_color = QColor("#2196F3")
                fill_color   = QColor("#502196F3")

            # Step 1: 合并所有多边形到一个 QPainterPath，统一填充（无叠加加深）
            combined = QPainterPath()
            for polygon in self._mask.polygons:
                if len(polygon) >= 3:
                    pts = [QPointF(p[0], p[1]) for p in polygon]
                    sub = QPainterPath()
                    sub.moveTo(pts[0])
                    for p in pts[1:]:
                        sub.lineTo(p)
                    sub.closeSubpath()
                    combined = combined.united(sub)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(fill_color))
            painter.drawPath(combined)

            # Step 2: 单独描边每个多边形轮廓（保持边界清晰）
            pen = QPen(stroke_color)
            pen.setWidthF(1.5 / self._scale)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for polygon in self._mask.polygons:
                if len(polygon) >= 3:
                    pts = [QPointF(p[0], p[1]) for p in polygon]
                    path = QPainterPath()
                    path.moveTo(pts[0])
                    for p in pts[1:]:
                        path.lineTo(p)
                    path.closeSubpath()
                    painter.drawPath(path)

        # 绘制框选蒙版实时预览矩形
        if self._mask_start_point and self._mask_drag_current:
            pen = QPen(QColor("#FF5722"))
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setWidthF(1.5 / self._scale)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor("#30FF5722")))
            p1 = self._mask_start_point
            p2 = self._mask_drag_current
            x = min(p1.x(), p2.x())
            y = min(p1.y(), p2.y())
            w = abs(p2.x() - p1.x())
            h = abs(p2.y() - p1.y())
            painter.drawRect(QRectF(x, y, w, h))
        elif self._mask_start_point:
            pen = QPen(QColor("#FF5722"))
            pen.setWidthF(2.0 / self._scale)
            painter.setPen(pen)
            r = self._point_size / self._scale
            painter.setBrush(QBrush(QColor("#40FF5722")))
            painter.drawEllipse(self._mask_start_point, r * 2, r * 2)

    def _draw_eraser_cursor(self, painter: QPainter):
        """绘制橡皮擦/画笔蒙版光标（仅在按下时显示）"""
        if self._mouse_image_pos is None:
            return
        if self._current_tool == self.MODE_ERASER and self._eraser_pressed:
            pen = QPen(QColor("#F44336"))
            pen.setWidthF(2.0 / self._scale)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor("#20F44336")))
            r = self._eraser_size
            painter.drawEllipse(self._mouse_image_pos, r, r)
        elif self._current_tool == self.MODE_BRUSH_MASK and self._brush_painting:
            pen = QPen(QColor("#FF9800"))
            pen.setWidthF(2.0 / self._scale)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor("#30FF9800")))
            r = self._eraser_size
            painter.drawEllipse(self._mouse_image_pos, r, r)

    def _draw_assisted_preview(self, painter: QPainter):
        """绘制辅助选点预览（两点点击模式）"""
        if self._current_tool != self.MODE_ASSISTED:
            return
        r = max(4.0, self._point_size * 1.5) / self._scale
        if self._assist_point1 is not None:
            # 绘制第一个点（黄色大圆圈 + 十字）
            pen = QPen(QColor("#FFD700"))
            pen.setWidthF(2.5 / self._scale)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor("#60FFD700")))
            painter.drawEllipse(self._assist_point1, r, r)
            painter.drawLine(
                QPointF(self._assist_point1.x() - r * 1.5, self._assist_point1.y()),
                QPointF(self._assist_point1.x() + r * 1.5, self._assist_point1.y())
            )
            painter.drawLine(
                QPointF(self._assist_point1.x(), self._assist_point1.y() - r * 1.5),
                QPointF(self._assist_point1.x(), self._assist_point1.y() + r * 1.5)
            )
            # 若鼠标位置已知，绘制预览区域
            if self._mouse_image_pos is not None:
                p1 = self._assist_point1
                p2 = self._mouse_image_pos
                x1 = min(p1.x(), p2.x())
                y1 = min(p1.y(), p2.y())
                w = abs(p2.x() - p1.x())
                h = abs(p2.y() - p1.y())
                dash_pen = QPen(QColor("#FFD700"))
                dash_pen.setWidthF(1.5 / self._scale)
                dash_pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(dash_pen)
                painter.setBrush(QBrush(QColor("#15FFD700")))
                if self._assist_shape == "ellipse":
                    painter.drawEllipse(QRectF(x1, y1, w, h))
                else:
                    painter.drawRect(QRectF(x1, y1, w, h))

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
        elif self._current_tool == self.MODE_EXTRACT:
            # E键切换橡皮擦和提取模式
            if event.key() == Qt.Key_E:
                self.toggle_eraser_mode.emit()
                return
            # Escape 退出微调模式
            if event.key() == Qt.Key_Escape:
                self._selected_point_index = -1
                self._point_nudge_mode = False
                self.update()
                return
            # 方向键微调选中点
            if self._point_nudge_mode and self._selected_point_index >= 0 and self._current_curve:
                pts = self._current_curve.points
                if self._selected_point_index < len(pts):
                    dx, dy = 0, 0
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
                    old_x, old_y = pts[self._selected_point_index]
                    new_x = old_x + dx
                    new_y = old_y + dy
                    self._current_curve.points[self._selected_point_index] = (new_x, new_y)
                    self.curve_point_moved.emit(self._selected_point_index, new_x, new_y)
                    self.update()
                    return
            super().keyPressEvent(event)
        elif self._current_tool == self.MODE_ERASER:
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

        # 任意模式下右键拖动图片
        if event.button() == Qt.MouseButton.RightButton:
            self._pan = True
            self._pan_start = pos - self._offset
            return

        if self._current_tool == self.MODE_CALIBRATE:
            self._handle_calibrate_click(pos)
        elif self._current_tool == self.MODE_EXTRACT:
            self._handle_extract_click(pos)
        elif self._current_tool == self.MODE_COLOR_PICK:
            if event.button() == Qt.MouseButton.LeftButton:
                self._handle_color_pick_click(pos)
        elif self._current_tool == self.MODE_ERASER:
            if event.button() == Qt.MouseButton.LeftButton:
                self._eraser_pressed = True
                self._mouse_image_pos = self._widget_to_image_coords(pos)
                self.update()
                self._handle_eraser_click(pos)
        elif self._current_tool == self.MODE_BOX_MASK:
            if event.button() == Qt.MouseButton.LeftButton:
                self._mask_start_point = self._widget_to_image_coords(pos)
                self._mask_drag_current = None
        elif self._current_tool == self.MODE_BRUSH_MASK:
            if event.button() == Qt.MouseButton.LeftButton:
                self._brush_painting = True
                pt = self._widget_to_image_coords(pos)
                self._brush_last_pt = pt
                self._add_brush_circle(pt)
        elif self._current_tool == self.MODE_ASSISTED:
            if event.button() == Qt.MouseButton.LeftButton:
                img_pos = self._widget_to_image_coords(pos)
                if self._assist_point1 is None:
                    self._assist_point1 = img_pos
                else:
                    x1, y1 = self._assist_point1.x(), self._assist_point1.y()
                    x2, y2 = img_pos.x(), img_pos.y()
                    if abs(x2 - x1) > 3 or abs(y2 - y1) > 3:
                        self.assisted_region_selected.emit(x1, y1, x2, y2)
                    self._assist_point1 = None
                self.update()
    def _handle_color_pick_click(self, pos: QPointF):
        """处理取色模式点击 - 采集该像素颜色"""
        if self._pixmap is None:
            return
        img_pos = self._widget_to_image_coords(pos)
        x = int(img_pos.x())
        y = int(img_pos.y())
        w = self._pixmap.width()
        h = self._pixmap.height()
        if 0 <= x < w and 0 <= y < h:
            qimage = self._pixmap.toImage()
            color = qimage.pixelColor(x, y)
            self.color_picked.emit(color)
        # 取色后自动退回 select 模式
        self._current_tool = self.MODE_SELECT
        self.update()

    def _handle_eraser_click(self, pos: QPointF):
        """处理橡皮擦点击"""
        img_pos = self._widget_to_image_coords(pos)
        self.eraser_point.emit(img_pos.x(), img_pos.y())

    def _handle_calibrate_click(self, pos: QPointF):
        """处理校准模式点击"""
        img_pos = self._widget_to_image_coords(pos)
        next_type = self._calibration.next_point_type()

        if self._calibration.coord_type == "polar":
            # 极坐标校准点: origin, angle_radius_point (2点)
            if next_type == "origin":
                self._calibration.x_start = img_pos
                self._calibration_step_hint = "请点击设置角度和极径点A"
                self.calibration_step.emit("angle_radius_point")
            elif next_type == "angle_radius_point":
                self._calibration.x_end = img_pos
                self._calibration_step_hint = "校准点已设置完成，请再次点击校准按钮完成校准"
                self.calibration_step.emit("complete")
        else:
            # 线性/对数坐标校准点: x_start, x_end, y_start, y_end
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
                self._calibration_step_hint = "校准点已设置完成，请再次点击校准按钮完成校准"
                self.calibration_step.emit("complete")

        self.update()

    def _handle_extract_click(self, pos: QPointF):
        """处理曲线提取模式点击"""
        self.setFocus()  # 确保键盘焦点
        img_pos = self._widget_to_image_coords(pos)

        if self._current_curve is None:
            self._current_curve = CurveOverlayItem()

        self._current_curve.add_point(img_pos.x(), img_pos.y())
        # 新取的点自动进入微调模式
        self._selected_point_index = len(self._current_curve.points) - 1
        self._point_nudge_mode = True
        self.curve_point_added.emit(img_pos.x(), img_pos.y())
        self.update()

    def mouseDoubleClickEvent(self, event):
        """双击 - 在提取模式下选中最近的曲线点进入微调"""
        if self._current_tool != self.MODE_EXTRACT:
            super().mouseDoubleClickEvent(event)
            return
        if self._current_curve is None or not self._current_curve.points:
            return
        pos = event.position()
        img_pos = self._widget_to_image_coords(pos)
        mx, my = img_pos.x(), img_pos.y()
        threshold = (self._point_size / self._scale) * 4.0  # 选中判定半径
        best_idx = -1
        best_dist = float('inf')
        for i, (px, py) in enumerate(self._current_curve.points):
            dist = ((px - mx) ** 2 + (py - my) ** 2) ** 0.5
            if dist < threshold and dist < best_dist:
                best_dist = dist
                best_idx = i
        if best_idx >= 0:
            self._selected_point_index = best_idx
            self._point_nudge_mode = True
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动"""
        # 跟踪鼠标位置
        if self._pixmap:
            self._mouse_image_pos = self._widget_to_image_coords(event.position())
            self.mouse_moved.emit(self._mouse_image_pos.x(), self._mouse_image_pos.y())
        else:
            self._mouse_image_pos = None

        # 右键或左键在 SELECT 模式下拖动平移
        if self._pan and self._pixmap:
            new_offset = event.position() - self._pan_start
            self._offset = self._clamp_offset(new_offset)
            self.update()
            return

        if self._current_tool == self.MODE_ERASER and event.buttons() & Qt.MouseButton.LeftButton:
            pos = event.position()
            img_pos = self._widget_to_image_coords(pos)
            self.eraser_point.emit(img_pos.x(), img_pos.y())
            self.update()
        elif self._current_tool == self.MODE_BOX_MASK and self._mask_start_point and event.buttons() & Qt.MouseButton.LeftButton:
            # 框选蒙版实时预览：记录当前鼠标位置
            self._mask_drag_current = self._widget_to_image_coords(event.position())
            self.update()
        elif self._current_tool == self.MODE_BRUSH_MASK and self._brush_painting and event.buttons() & Qt.MouseButton.LeftButton:
            new_pt = self._widget_to_image_coords(event.position())
            if self._brush_last_pt is not None:
                dx = new_pt.x() - self._brush_last_pt.x()
                dy = new_pt.y() - self._brush_last_pt.y()
                if (dx*dx + dy*dy) ** 0.5 >= self._eraser_size * 0.5:
                    self._brush_last_pt = new_pt
                    self._add_brush_circle(new_pt)
            else:
                self._brush_last_pt = new_pt
                self._add_brush_circle(new_pt)
            self.update()
        elif self._current_tool in (self.MODE_ERASER, self.MODE_BOX_MASK, self.MODE_BRUSH_MASK, self.MODE_ASSISTED):
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放"""
        if event.button() == Qt.MouseButton.RightButton:
            self._pan = False
            self.update()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            if self._current_tool == self.MODE_ERASER:
                self._eraser_pressed = False
                self.update()
            if self._current_tool == self.MODE_BOX_MASK and self._mask_start_point:
                end_point = self._widget_to_image_coords(event.position())
                x1, y1 = self._mask_start_point.x(), self._mask_start_point.y()
                x2, y2 = end_point.x(), end_point.y()
                if abs(x2 - x1) > 2 or abs(y2 - y1) > 2:
                    polygon = [(min(x1, x2), min(y1, y2)),
                               (max(x1, x2), min(y1, y2)),
                               (max(x1, x2), max(y1, y2)),
                               (min(x1, x2), max(y1, y2))]
                    self.mask_about_to_add.emit(polygon)
                    self._mask.add_polygon(polygon)
                    self.mask_changed.emit()
                self._mask_start_point = None
                self._mask_drag_current = None
                self.update()
            elif self._current_tool == self.MODE_BRUSH_MASK:
                self._brush_painting = False
                self._brush_last_pt = None
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
        """拖拽放下 - 发射信号而非自己加载，由外层决定如何处理"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path:
                self.file_dropped.emit(file_path)

    def _add_brush_circle(self, pt: QPointF):
        """在指定位置添加一个圆形蒙版叠加（类橡皮擦逻辑）"""
        import math
        x, y = pt.x(), pt.y()
        r = self._eraser_size
        n = 16
        circle = [
            (x + r * math.cos(2 * math.pi * i / n),
             y + r * math.sin(2 * math.pi * i / n))
            for i in range(n)
        ]
        self.mask_about_to_add.emit(circle)
        self._mask.add_polygon(circle)
        self.mask_changed.emit()
        self.update()

    def _add_brush_circle(self, pt: QPointF):
        """在指定位置添加一个圆形蒙版叠加（类橡皮擦逻辑）"""
        import math
        x, y = pt.x(), pt.y()
        r = self._eraser_size
        n = 16
        circle = [
            (x + r * math.cos(2 * math.pi * i / n),
             y + r * math.sin(2 * math.pi * i / n))
            for i in range(n)
        ]
        self.mask_about_to_add.emit(circle)
        self._mask.add_polygon(circle)
        self.mask_changed.emit()
        self.update()

    @staticmethod
    def _stroke_to_polygon(points: list, radius: float) -> list:
        """将笔触转换为轮廓多边形（粗笔形状）"""
        import math
        if not points:
            return []
        if len(points) == 1:
            cx, cy = points[0]
            n = 12
            return [(cx + radius * math.cos(2 * math.pi * i / n),
                     cy + radius * math.sin(2 * math.pi * i / n))
                    for i in range(n)]

        left_side = []
        right_side = []
        for i in range(len(points)):
            cx, cy = points[i]
            if i == 0:
                dx = points[1][0] - points[0][0]
                dy = points[1][1] - points[0][1]
            elif i == len(points) - 1:
                dx = points[-1][0] - points[-2][0]
                dy = points[-1][1] - points[-2][1]
            else:
                dx = points[i+1][0] - points[i-1][0]
                dy = points[i+1][1] - points[i-1][1]
            dist = (dx*dx + dy*dy) ** 0.5
            if dist < 1e-9:
                dx, dy, dist = 1.0, 0.0, 1.0
            px = -dy / dist * radius
            py = dx / dist * radius
            left_side.append((cx + px, cy + py))
            right_side.append((cx - px, cy - py))

        # start cap
        scx, scy = points[0]
        sdx = points[0][0] - points[1][0] if len(points) > 1 else -1
        sdy = points[0][1] - points[1][1] if len(points) > 1 else 0
        sd = (sdx*sdx + sdy*sdy) ** 0.5 or 1
        s_angle = math.atan2(sdy/sd, sdx/sd)
        start_cap = [(scx + radius * math.cos(s_angle + math.pi * i / 6),
                      scy + radius * math.sin(s_angle + math.pi * i / 6))
                     for i in range(7)]

        # end cap
        ecx, ecy = points[-1]
        edx = points[-1][0] - points[-2][0] if len(points) > 1 else 1
        edy = points[-1][1] - points[-2][1] if len(points) > 1 else 0
        ed = (edx*edx + edy*edy) ** 0.5 or 1
        e_angle = math.atan2(edy/ed, edx/ed)
        end_cap = [(ecx + radius * math.cos(e_angle + math.pi * i / 6),
                    ecy + radius * math.sin(e_angle + math.pi * i / 6))
                   for i in range(7)]

        return start_cap + left_side + end_cap + list(reversed(right_side))

    def resizeEvent(self, event: QResizeEvent):
        """窗口大小变化"""
        super().resizeEvent(event)
        if self._pixmap:
            self.fit_to_window()
