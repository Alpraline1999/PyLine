from pydantic import BaseModel
from typing import List, Optional, Tuple
from datetime import datetime
import uuid


class CalibrationData(BaseModel):
    origin: Tuple[float, float] = (0.0, 0.0)
    x_axis_end: Tuple[float, float] = (1.0, 0.0)
    y_axis_end: Tuple[float, float] = (0.0, 1.0)
    x_range: Tuple[float, float] = (0.0, 1.0)
    y_range: Tuple[float, float] = (0.0, 1.0)
    coord_type: str = "linear"


class Curve(BaseModel):
    id: str = ""
    name: str = ""
    x_data: List[float] = []
    y_data: List[float] = []
    color: str = "#0078D4"
    source_image_id: Optional[str] = None


class MaskData(BaseModel):
    include_mode: bool = True
    polygons: List[List[Tuple[int, int]]] = []


class ImageWork(BaseModel):
    id: str = ""
    name: str = ""
    image_path: str = ""
    curves: List[Curve] = []
    mask: Optional[MaskData] = None
    calibration: Optional[CalibrationData] = None


class Project(BaseModel):
    id: str = ""
    name: str = ""
    images: List[ImageWork] = []
    imported_curves: List[Curve] = []
    created_at: str = ""
    updated_at: str = ""

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
            updated_at=now
        )
