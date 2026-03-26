import json
import os
import uuid
from typing import Optional, List, Tuple
from datetime import datetime

from models.schemas import Project, ImageWork, Curve, CalibrationData


class ProjectManager:
    """项目管理器 - 支持多项目管理和当前项目概念"""

    def __init__(self):
        self._projects: List[Project] = []
        self._current_project_id: Optional[str] = None

    @property
    def projects(self) -> List[Project]:
        """所有已打开的项目"""
        return self._projects

    @property
    def current_project(self) -> Optional[Project]:
        """当前选中的项目"""
        if self._current_project_id is None:
            return None
        for p in self._projects:
            if p.id == self._current_project_id:
                return p
        return None

    @property
    def current_project_id(self) -> Optional[str]:
        """当前项目ID"""
        return self._current_project_id

    def get_project(self, project_id: str) -> Optional[Project]:
        """根据ID获取项目"""
        for p in self._projects:
            if p.id == project_id:
                return p
        return None

    def set_current_project(self, project_id: str):
        """设置当前项目"""
        if self.get_project(project_id):
            self._current_project_id = project_id

    def create_new(self, name: str) -> Project:
        """创建新项目并设为当前项目"""
        project = Project.create_new(name)
        self._projects.append(project)
        self._current_project_id = project.id
        return project

    def save(self, file_path: Optional[str] = None) -> str:
        """保存当前项目到文件"""
        if self.current_project is None:
            raise ValueError("没有当前项目")

        if file_path is None:
            file_path = self.current_project.file_path
            if file_path is None:
                raise ValueError("没有指定文件路径")

        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        # 更新时间戳
        self.current_project.updated_at = datetime.now().isoformat()

        # 保存为 JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.current_project.model_dump(), f, indent=2, ensure_ascii=False)

        self.current_project.file_path = file_path
        self.current_project.is_modified = False
        return file_path

    def open(self, file_path: str) -> Project:
        """从文件打开项目"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"项目文件不存在: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        project = Project(**data)
        project.file_path = file_path
        project.is_modified = False

        # 检查是否已打开该项目
        existing = self.get_project(project.id)
        if existing:
            # 更新已存在的项目
            idx = self._projects.index(existing)
            self._projects[idx] = project
        else:
            self._projects.append(project)

        self._current_project_id = project.id
        return project

    def close_current_project(self):
        """关闭当前项目"""
        if self._current_project_id:
            self._projects = [p for p in self._projects if p.id != self._current_project_id]
            self._current_project_id = None

    def close_project(self, project_id: str):
        """关闭指定项目"""
        self._projects = [p for p in self._projects if p.id != project_id]
        if self._current_project_id == project_id:
            self._current_project_id = self._projects[0].id if self._projects else None

    def add_image(self, image_path: str, name: Optional[str] = None) -> ImageWork:
        """向当前项目添加图片"""
        if self.current_project is None:
            raise ValueError("没有当前项目")

        image_work = ImageWork(
            id=str(uuid.uuid4()),
            name=name or os.path.basename(image_path),
            image_path=image_path
        )
        self.current_project.images.append(image_work)
        self.current_project.is_modified = True
        return image_work

    def get_image(self, image_id: str) -> Optional[ImageWork]:
        """根据ID获取图片"""
        if self.current_project is None:
            return None
        for img in self.current_project.images:
            if img.id == image_id:
                return img
        return None

    def add_curve_to_image(self, image_id: str, x_data: List[float], y_data: List[float],
                          name: str = "新曲线", color: str = "#0078D4",
                          point_shape: str = "circle",
                          calibration: Optional[CalibrationData] = None) -> Optional[Curve]:
        """向指定图片添加曲线"""
        if self.current_project is None:
            return None

        image = self.get_image(image_id)
        if image is None:
            return None

        # 计算实际坐标
        x_actual = []
        y_actual = []
        for px, py in zip(x_data, y_data):
            if calibration:
                x, y = self._compute_actual_coords(calibration, px, py)
            else:
                x, y = px, py
            x_actual.append(x)
            y_actual.append(y)

        curve = Curve(
            id=str(uuid.uuid4()),
            name=name,
            x_data=x_data,
            y_data=y_data,
            x_actual=x_actual,
            y_actual=y_actual,
            color=color,
            point_shape=point_shape,
            source_image_id=image_id,
            calibration=calibration
        )
        image.curves.append(curve)
        self.current_project.is_modified = True
        return curve

    def _compute_actual_coords(self, calib: CalibrationData, px: float, py: float) -> Tuple[float, float]:
        """将像素坐标转换为实际坐标（支持多种坐标类型）"""
        if calib.coord_type == "polar":
            return self._compute_polar_coords(calib, px, py)
        elif calib.coord_type == "log":
            return self._compute_log_coords(calib, px, py)
        else:
            return self._compute_linear_coords(calib, px, py)

    def _compute_linear_coords(self, calib: CalibrationData, px: float, py: float) -> Tuple[float, float]:
        """线性坐标转换"""
        # X轴计算：点在线段x_start到x_end上的比例
        x_start = calib.x_start
        x_end = calib.x_end
        dx = x_end[0] - x_start[0]
        dy_x = x_end[1] - x_start[1]

        if abs(dx) > abs(dy_x):  # 主要沿X方向
            if dx != 0:
                t = (px - x_start[0]) / dx
            else:
                t = 0
        else:  # 主要沿Y方向
            if dy_x != 0:
                t = (py - x_start[1]) / dy_x
            else:
                t = 0

        x_actual = calib.x_range[0] + t * (calib.x_range[1] - calib.x_range[0])

        # Y轴计算：点在线段y_start到y_end上的比例
        y_start = calib.y_start
        y_end = calib.y_end
        dx_y = y_end[0] - y_start[0]
        dy = y_end[1] - y_start[1]

        if abs(dx_y) > abs(dy):  # 主要沿X方向
            if dx_y != 0:
                t_y = (px - y_start[0]) / dx_y
            else:
                t_y = 0
        else:  # 主要沿Y方向
            if dy != 0:
                t_y = (py - y_start[1]) / dy
            else:
                t_y = 0

        y_actual = calib.y_range[1] - t_y * (calib.y_range[1] - calib.y_range[0])  # Y轴反转

        return (x_actual, y_actual)

    def _compute_log_coords(self, calib: CalibrationData, px: float, py: float) -> Tuple[float, float]:
        """对数坐标转换"""
        import math
        # 首先计算线性比例
        x_start = calib.x_start
        x_end = calib.x_end
        dx = x_end[0] - x_start[0]
        dy_x = x_end[1] - x_start[1]

        if abs(dx) > abs(dy_x):
            if dx != 0:
                t = (px - x_start[0]) / dx
            else:
                t = 0
        else:
            if dy_x != 0:
                t = (py - x_start[1]) / dy_x
            else:
                t = 0

        # 对数变换
        log_min = math.log10(max(calib.x_range[0], 1e-10))
        log_max = math.log10(max(calib.x_range[1], 1e-10))
        x_actual = math.pow(10, log_min + t * (log_max - log_min))

        # Y轴类似处理
        y_start = calib.y_start
        y_end = calib.y_end
        dx_y = y_end[0] - y_start[0]
        dy = y_end[1] - y_start[1]

        if abs(dx_y) > abs(dy):
            if dx_y != 0:
                t_y = (px - y_start[0]) / dx_y
            else:
                t_y = 0
        else:
            if dy != 0:
                t_y = (py - y_start[1]) / dy
            else:
                t_y = 0

        log_min_y = math.log10(max(calib.y_range[0], 1e-10))
        log_max_y = math.log10(max(calib.y_range[1], 1e-10))
        y_actual = math.pow(10, log_min_y + (1 - t_y) * (log_max_y - log_min_y))

        return (x_actual, y_actual)

    def _compute_polar_coords(self, calib: CalibrationData, px: float, py: float) -> Tuple[float, float]:
        """极坐标转换

        像素坐标 -> (r, theta)
        校准点：
        - origin: 原点(极点)
        - x_end: 角度1点（像素坐标），对应实际角度 angle1
        - y_start: 角度2点（像素坐标），对应实际角度 angle2
        - y_end: 极径1点（像素坐标），对应实际极径 radius1

        算法：
        1. 计算P相对于原点的像素半径和像素角度方向
        2. 计算像素角度方向相对于角度1点的方向的比例位置
        3. 映射到实际角度 angle1 -> angle2
        4. 半径 = (像素半径 / 极径1点的像素距离) * radius1
        """
        import math

        origin_x, origin_y = calib.x_start
        angle1_x, angle1_y = calib.x_end      # 角度1点
        angle2_x, angle2_y = calib.y_start    # 角度2点
        radius1_x, radius1_y = calib.y_end     # 极径1点

        # 用户输入的实际角度值
        theta1_actual = calib.angle1  # 角度1的实际值
        theta2_actual = calib.angle2  # 角度2的实际值
        r1_actual = calib.radius1     # 极径1的实际值

        # 计算向量
        vx = px - origin_x
        vy = py - origin_y

        # 计算P的像素半径
        pixel_r = math.sqrt(vx * vx + vy * vy)

        # 计算P的像素角度（标准数学角度，逆时针为正，从正x轴开始）
        theta_p = math.atan2(vy, vx) * 180 / math.pi

        # 计算角度1点的像素方向角
        theta1_pix = math.atan2(angle1_y - origin_y, angle1_x - origin_x) * 180 / math.pi

        # 计算角度2点的像素方向角
        theta2_pix = math.atan2(angle2_y - origin_y, angle2_x - origin_x) * 180 / math.pi

        # 计算像素角度的顺时针跨度（从角度1到角度2）
        clockwise_span = (theta2_pix - theta1_pix + 360) % 360

        # 计算P相对于角度1的顺时针像素角度距离
        clockwise_dist = (theta_p - theta1_pix + 360) % 360

        # 计算比例（0到1之间）
        if clockwise_span < 1e-6:
            proportion = 0
        elif clockwise_dist <= clockwise_span:
            proportion = clockwise_dist / clockwise_span
        else:
            # 超出范围，clamped到边界
            proportion = 1.0 if clockwise_dist > clockwise_span + 180 else 0.0

        # 映射到实际角度
        # 注意：实际角度可能跨越0度（如330到30），需要特殊处理
        angle_diff = theta2_actual - theta1_actual
        # 如果角度差为负，说明跨越了0度，需要调整
        if angle_diff < 0:
            angle_diff += 360

        theta_actual = theta1_actual + proportion * angle_diff
        # 归一化到[0, 360)
        while theta_actual < 0:
            theta_actual += 360
        while theta_actual >= 360:
            theta_actual -= 360

        # 计算极径1点的像素距离
        r1_dx = radius1_x - origin_x
        r1_dy = radius1_y - origin_y
        r1_pixel_dist = math.sqrt(r1_dx * r1_dx + r1_dy * r1_dy)

        # 计算实际半径
        if r1_pixel_dist > 0:
            r_actual = (pixel_r / r1_pixel_dist) * r1_actual
        else:
            r_actual = 0

        return (r_actual, theta_actual)

    def get_curve(self, curve_id: str) -> Optional[Curve]:
        """根据ID获取曲线"""
        if self.current_project is None:
            return None
        for img in self.current_project.images:
            for curve in img.curves:
                if curve.id == curve_id:
                    return curve
        for curve in self.current_project.imported_curves:
            if curve.id == curve_id:
                return curve
        return None

    def update_curve_calibration(self, curve_id: str, calibration: CalibrationData):
        """更新曲线的校准数据"""
        if self.current_project is None:
            return

        curve = self.get_curve(curve_id)
        if curve is None:
            return

        curve.calibration = calibration
        self.current_project.is_modified = True

    def pixel_to_actual_coords(self, curve_id: str, px: float, py: float) -> Tuple[float, float]:
        """将像素坐标转换为实际坐标

        校准使用4点：
        - x_start, x_end 定义X轴
        - y_start, y_end 定义Y轴
        如果曲线没有校准数据，返回像素坐标
        """
        curve = self.get_curve(curve_id)
        if curve is None or curve.calibration is None:
            return (px, py)

        return self._compute_actual_coords(curve.calibration, px, py)


# 全局单例
project_manager = ProjectManager()
