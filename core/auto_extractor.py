"""
自动选点模块 - 基于 OpenCV + numpy 的颜色匹配曲线提取
"""
from __future__ import annotations

import cv2
import numpy as np
from typing import List, Tuple, Optional


class AutoExtractor:
    """
    基于颜色匹配的自动曲线提取器。

    流程：
    1. 读取图片（BGR）→ HSV 空间
    2. 构建颜色范围掩码（目标颜色 ±HSV 容差）
    3. 结合蒙版多边形进行区域筛选
    4. 按列（x 步长）扫描，对每列匹配像素求 y 质心
    5. 返回 (x, y) 像素坐标点列表
    """

    @staticmethod
    def extract(
        image_path: str,
        target_r: int,
        target_g: int,
        target_b: int,
        h_tol: int = 15,
        s_tol: int = 50,
        v_tol: int = 50,
        mask_polygons: Optional[List[List[Tuple[float, float]]]] = None,
        step: int = 2,
    ) -> List[Tuple[float, float]]:
        """
        提取颜色匹配的曲线点。

        参数:
            image_path: 图片文件路径
            target_r/g/b: 目标颜色 RGB 分量 (0-255)
            h_tol: 色调容差 (0-180)
            s_tol: 饱和度容差 (0-255)
            v_tol: 明度容差 (0-255)
            mask_polygons: 蒙版多边形列表，点为 (x, y) 元组；若提供，仅在蒙版内检测
            step: 列扫描步长（像素）
        返回:
            [(x, y), ...] 像素坐标列表，已按 x 排序
        """
        # 读取图片
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            return []

        h_img, w_img = img_bgr.shape[:2]

        # RGB → HSV 目标颜色
        target_bgr = np.array([[[target_b, target_g, target_r]]], dtype=np.uint8)
        target_hsv = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2HSV)[0, 0]
        th, ts, tv = int(target_hsv[0]), int(target_hsv[1]), int(target_hsv[2])

        # 构建 HSV 范围（注意色调环绕处理）
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        lower1 = np.array([max(0, th - h_tol), max(0, ts - s_tol), max(0, tv - v_tol)])
        upper1 = np.array([min(180, th + h_tol), min(255, ts + s_tol), min(255, tv + v_tol)])
        color_mask = cv2.inRange(img_hsv, lower1, upper1)

        # 色调环绕处理（跨越 0/180 边界）
        if th - h_tol < 0:
            lower2 = np.array([180 + th - h_tol, max(0, ts - s_tol), max(0, tv - v_tol)])
            upper2 = np.array([180, min(255, ts + s_tol), min(255, tv + v_tol)])
            color_mask = cv2.bitwise_or(color_mask, cv2.inRange(img_hsv, lower2, upper2))
        elif th + h_tol > 180:
            lower2 = np.array([0, max(0, ts - s_tol), max(0, tv - v_tol)])
            upper2 = np.array([th + h_tol - 180, min(255, ts + s_tol), min(255, tv + v_tol)])
            color_mask = cv2.bitwise_or(color_mask, cv2.inRange(img_hsv, lower2, upper2))

        # 构建蒙版区域图像掩码（若有蒙版多边形则只保留蒙版内的像素）
        if mask_polygons:
            region_mask = np.zeros((h_img, w_img), dtype=np.uint8)
            for polygon in mask_polygons:
                if len(polygon) >= 3:
                    pts = np.array([(int(p[0]), int(p[1])) for p in polygon], dtype=np.int32)
                    cv2.fillPoly(region_mask, [pts], 255)
            color_mask = cv2.bitwise_and(color_mask, region_mask)

        # 按列扫描，对每列匹配像素求 y 质心
        points: List[Tuple[float, float]] = []
        for x in range(0, w_img, step):
            col = color_mask[:, x]
            y_indices = np.where(col > 0)[0]
            if len(y_indices) > 0:
                y_center = float(np.mean(y_indices))
                points.append((float(x), y_center))

        return points

    @staticmethod
    def preview_mask(
        image_path: str,
        target_r: int,
        target_g: int,
        target_b: int,
        h_tol: int = 15,
        s_tol: int = 50,
        v_tol: int = 50,
    ) -> Optional[np.ndarray]:
        """
        返回颜色匹配的二值掩码图（用于调试/预览），形状 (H, W)，uint8。
        """
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            return None

        target_bgr = np.array([[[target_b, target_g, target_r]]], dtype=np.uint8)
        target_hsv = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2HSV)[0, 0]
        th, ts, tv = int(target_hsv[0]), int(target_hsv[1]), int(target_hsv[2])

        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        lower1 = np.array([max(0, th - h_tol), max(0, ts - s_tol), max(0, tv - v_tol)])
        upper1 = np.array([min(180, th + h_tol), min(255, ts + s_tol), min(255, tv + v_tol)])
        color_mask = cv2.inRange(img_hsv, lower1, upper1)

        if th - h_tol < 0:
            lower2 = np.array([180 + th - h_tol, max(0, ts - s_tol), max(0, tv - v_tol)])
            upper2 = np.array([180, min(255, ts + s_tol), min(255, tv + v_tol)])
            color_mask = cv2.bitwise_or(color_mask, cv2.inRange(img_hsv, lower2, upper2))
        elif th + h_tol > 180:
            lower2 = np.array([0, max(0, ts - s_tol), max(0, tv - v_tol)])
            upper2 = np.array([th + h_tol - 180, min(255, ts + s_tol), min(255, tv + v_tol)])
            color_mask = cv2.bitwise_or(color_mask, cv2.inRange(img_hsv, lower2, upper2))

        return color_mask
