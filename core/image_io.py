from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PySide6.QtGui import QPixmap


def load_pixmap_unicode(file_path: str) -> QPixmap:
    """通过字节流加载图片，规避 Windows 中文路径问题。"""
    pixmap = QPixmap()
    try:
        data = Path(file_path).read_bytes()
    except OSError:
        return pixmap

    pixmap.loadFromData(data)
    return pixmap


def cv2_imread_unicode(file_path: str, flags: int = cv2.IMREAD_COLOR):
    """通过 imdecode 读取图片，规避 Windows 下 cv2.imread 的 Unicode 路径问题。"""
    try:
        data = np.fromfile(file_path, dtype=np.uint8)
    except OSError:
        return None

    if data.size == 0:
        return None

    return cv2.imdecode(data, flags)