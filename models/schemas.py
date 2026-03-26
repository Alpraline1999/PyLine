from pydantic import BaseModel
from typing import List, Optional, Tuple
from datetime import datetime
import uuid


class CalibrationData(BaseModel):
    """校准数据 - 使用4点校准

    线性/对数坐标系（coord_type="linear"或"log"）：
    - x_start, x_end: X轴起点和终点（像素坐标）
    - y_start, y_end: Y轴起点和终点（像素坐标）
    - x_range: X轴实际数值范围
    - y_range: Y轴实际数值范围

    极坐标系（coord_type="polar"）：
    - x_start: 原点/极点（像素坐标）
    - x_end: 角度1点（像素坐标）
    - y_start: 角度2点（像素坐标）
    - y_end: 极径1点（像素坐标）
    - angle1: 角度1的实际值（度）
    - angle2: 角度2的实际值（度）
    - radius1: 极径1的实际值
    - radius_max: 最大半径（由角度点位置比例确定）
    """
    x_start: Tuple[float, float] = (0.0, 0.0)  # X轴起点 或 原点(极坐标)
    x_end: Tuple[float, float] = (1.0, 0.0)      # X轴终点 或 角度1点(极坐标)
    y_start: Tuple[float, float] = (0.0, 0.0)  # Y轴起点 或 角度2点(极坐标)
    y_end: Tuple[float, float] = (0.0, 1.0)      # Y轴终点 或 极径1点(极坐标)
    x_range: Tuple[float, float] = (0.0, 1.0)  # X轴范围 或 半径范围(极坐标)
    y_range: Tuple[float, float] = (0.0, 1.0)  # Y轴范围 或 角度范围(极坐标)
    coord_type: str = "linear"
    # 极坐标专用参数
    angle1: float = 0.0  # 角度1的实际值（度）
    angle2: float = 90.0  # 角度2的实际值（度）
    radius1: float = 1.0  # 极径1的实际值


class Curve(BaseModel):
    id: str = ""
    name: str = ""
    x_data: List[float] = []  # 像素坐标X
    y_data: List[float] = []  # 像素坐标Y
    x_actual: List[float] = []  # 实际坐标X（校准后）
    y_actual: List[float] = []  # 实际坐标Y（校准后）
    color: str = "#0078D4"
    point_shape: str = "circle"  # 点形状: circle, square, triangle, diamond, inv_triangle, cross, star, pentagram
    source_image_id: Optional[str] = None
    calibration: Optional[CalibrationData] = None  # 曲线专属的校准数据


class MaskData(BaseModel):
    include_mode: bool = True
    polygons: List[List[Tuple[int, int]]] = []


class ImageWork(BaseModel):
    id: str = ""
    name: str = ""
    image_path: str = ""
    curves: List[Curve] = []
    mask: Optional[MaskData] = None


class Project(BaseModel):
    id: str = ""
    name: str = ""
    images: List[ImageWork] = []
    imported_curves: List[Curve] = []
    created_at: str = ""
    updated_at: str = ""
    file_path: Optional[str] = None
    is_modified: bool = False

    @classmethod
    def create_new(cls, name: str) -> "Project":
        """创建一个新的项目"""
        now = datetime.now().isoformat()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            images=[],
            imported_curves=[],
            created_at=now,
            updated_at=now,
            file_path=None,
            is_modified=False
        )
