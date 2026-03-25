import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from models.schemas import Project


class ProjectManager:
    """项目管理器 - 处理项目的创建、打开、保存"""

    def __init__(self):
        self._current_project: Optional[Project] = None
        self._file_path: Optional[str] = None

    @property
    def current_project(self) -> Optional[Project]:
        return self._current_project

    @property
    def file_path(self) -> Optional[str]:
        return self._file_path

    @property
    def is_modified(self) -> bool:
        """检查项目是否有未保存的更改"""
        return self._current_project is not None

    def create_new(self, name: str) -> Project:
        """创建新项目"""
        self._current_project = Project.create_new(name)
        self._file_path = None
        return self._current_project

    def save(self, file_path: Optional[str] = None) -> str:
        """保存项目到文件"""
        if self._current_project is None:
            raise ValueError("没有当前项目")

        if file_path is None:
            if self._file_path is None:
                raise ValueError("没有指定文件路径")
            file_path = self._file_path

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 更新时间戳
        self._current_project.updated_at = datetime.now().isoformat()

        # 保存为 JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self._current_project.model_dump(), f, indent=2, ensure_ascii=False)

        self._file_path = file_path
        return file_path

    def open(self, file_path: str) -> Project:
        """从文件打开项目"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"项目文件不存在: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._current_project = Project(**data)
        self._file_path = file_path
        return self._current_project

    def close(self):
        """关闭当前项目"""
        self._current_project = None
        self._file_path = None

    def add_image(self, image_path: str, name: Optional[str] = None) -> "ImageWork":
        """向项目添加图片"""
        if self._current_project is None:
            raise ValueError("没有当前项目")

        from models.schemas import ImageWork
        import uuid

        image_work = ImageWork(
            id=str(uuid.uuid4()),
            name=name or os.path.basename(image_path),
            image_path=image_path
        )
        self._current_project.images.append(image_work)
        return image_work


# 全局单例
project_manager = ProjectManager()
