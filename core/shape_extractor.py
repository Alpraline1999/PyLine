"""图形识别提取器（V1.2.1 — 轮廓形状描述子方案）

核心思路：
  1. 从截图模板中提取最大轮廓 → 计算 Hu 矩作为形状描述子
  2. 全图颜色过滤 → 连通域分析 → 面积过滤
  3. 对每个候选连通域提取轮廓 → cv2.matchShapes() 与模板比对
  4. 匹配连通域的质心作为结果点

优势：尺度不敏感、旋转不敏感、抗背景干扰
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np


class ShapeExtractor:
    """基于轮廓形状描述子的图形识别曲线点提取器"""

    # ------------------------------------------------------------------ #
    #  预处理：从图片截取区域并提取形状描述子                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def preprocess_region(
        image_path: str,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> dict:
        """从图片中截取矩形区域，提取轮廓形状描述子。

        Returns:
            dict 包含:
              'raw'              : ndarray (BGR)  — 原始截图
              'binary'           : ndarray uint8  — 实心二值形状（前景=255）
              'contour'          : ndarray        — 模板最大轮廓 (用于 matchShapes)
              'contour_area'     : float          — 模板轮廓面积（像素）
              'dominant_hsv'     : (H, S, V) int  — 前景主色（HSV）
              'color_tol_hsv'    : (dH, dS, dV)   — 建议容差
              'has_color'        : bool            — 主色是否有足够饱和度可用
              'size'             : (w, h)          — 模板尺寸（像素）
        """
        import cv2

        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")

        img_h, img_w = img.shape[:2]
        x1i = max(0, int(round(x1)))
        y1i = max(0, int(round(y1)))
        x2i = min(img_w, int(round(x2)))
        y2i = min(img_h, int(round(y2)))

        if x2i - x1i < 4 or y2i - y1i < 4:
            raise ValueError("截图区域过小（至少需要 4×4 像素）")

        raw = img[y1i:y2i, x1i:x2i].copy()
        gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)

        # ---- 生成实心二值形状 ----
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(blurred, 30, 120)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        binary = np.zeros_like(gray, dtype=np.uint8)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            cv2.drawContours(binary, [largest], -1, 255, cv2.FILLED)
        else:
            _, binary = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            # 从二值图重新提取轮廓
            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            if contours:
                largest = max(contours, key=cv2.contourArea)
            else:
                raise ValueError("无法从截图区域提取有效轮廓")

        contour_area = cv2.contourArea(largest)
        if contour_area < 4:
            raise ValueError("截图区域中的形状面积过小")

        # ---- 提取前景主色 ----
        hsv_raw = cv2.cvtColor(raw, cv2.COLOR_BGR2HSV)
        fg_mask = binary > 0
        dominant_hsv, color_tol_hsv, has_color = ShapeExtractor._extract_dominant_color(
            hsv_raw, fg_mask
        )

        return {
            "raw": raw,
            "binary": binary,
            "contour": largest,
            "contour_area": float(contour_area),
            "dominant_hsv": dominant_hsv,
            "color_tol_hsv": color_tol_hsv,
            "has_color": has_color,
            "size": (x2i - x1i, y2i - y1i),
        }

    # ------------------------------------------------------------------ #
    #  提取：轮廓描述子管线                                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def extract(
        image_path: str,
        template_info: dict,
        mask_polygons: Optional[list] = None,
        mask_include_mode: bool = True,
        step: int = 1,
        threshold: float = 0.55,
        color_weight: float = 0.7,
    ) -> List[Tuple[float, float]]:
        """在图片中搜索与模板形状相似的连通域，返回各匹配中心点坐标。

        管线：
          1. 颜色过滤（或自适应二值化）→ 前景掩膜
          2. 连通域分析 → 面积过滤
          3. 逐候选连通域 → matchShapes 与模板轮廓比对
          4. 相似度 ≤ 阈值 → 质心作为结果点

        Args:
            image_path:        图片路径
            template_info:     preprocess_region() 返回的字典
            mask_polygons:     蒙版多边形列表
            mask_include_mode: True = 蒙版内才识别；False = 蒙版内不识别
            step:              未使用（保留接口兼容）
            threshold:         形状相似度阈值 [0, 1]；越大越宽松
                               (内部映射到 matchShapes 距离阈值)
            color_weight:      颜色过滤的严格程度 (0.0~1.0)；
                               越高 → 颜色容差越小，过滤越严格
        Returns:
            list of (x, y) 图片像素坐标
        """
        import cv2

        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")

        img_h, img_w = img.shape[:2]
        template_contour = template_info["contour"]
        template_area = template_info["contour_area"]

        # ---- 构建前景掩膜 ----
        fg_mask = ShapeExtractor._build_foreground_mask(
            img, template_info, color_weight
        )

        # ---- 应用搜索蒙版 ----
        if mask_polygons:
            search_mask = np.zeros((img_h, img_w), dtype=np.uint8)
            pts_list = [
                np.array([(int(x), int(y)) for x, y in poly], dtype=np.int32)
                for poly in mask_polygons
            ]
            cv2.fillPoly(search_mask, pts_list, 255)

            if mask_include_mode:
                # 仅保留蒙版内
                fg_mask = cv2.bitwise_and(fg_mask, search_mask)
            else:
                # 排除蒙版内
                fg_mask = cv2.bitwise_and(fg_mask, cv2.bitwise_not(search_mask))

        # ---- 形态学清理 ----
        k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, k_close, iterations=1)

        # ---- 连通域分析 ----
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            fg_mask, connectivity=8
        )

        # 面积过滤范围：模板面积的 0.15x ~ 6x
        area_lo = template_area * 0.15
        area_hi = template_area * 6.0

        # 形状相似度阈值：threshold 映射到 matchShapes 距离
        # threshold=1.0 → 非常宽松(dist_thr=1.0)  threshold=0.0 → 极严格(dist_thr=0.02)
        dist_thr = 0.02 + threshold * 0.98

        results: List[Tuple[float, float]] = []

        for i in range(1, num_labels):  # 跳过背景 label=0
            area = stats[i, cv2.CC_STAT_AREA]
            if area < area_lo or area > area_hi:
                continue

            # 提取该连通域的轮廓
            blob_mask = (labels == i).astype(np.uint8) * 255
            blob_contours, _ = cv2.findContours(
                blob_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            if not blob_contours:
                continue

            blob_contour = max(blob_contours, key=cv2.contourArea)
            if cv2.contourArea(blob_contour) < 4:
                continue

            # Hu 矩形状比对
            dist = cv2.matchShapes(
                template_contour, blob_contour, cv2.CONTOURS_MATCH_I1, 0.0
            )

            if dist <= dist_thr:
                cx, cy = centroids[i]
                results.append((float(cx), float(cy)))

        return results

    # ------------------------------------------------------------------ #
    #  颜色前景掩膜构建                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_foreground_mask(
        img: np.ndarray,
        template_info: dict,
        color_weight: float,
    ) -> np.ndarray:
        """根据模板颜色信息构建前景二值掩膜。

        - 颜色可靠时：HSV inRange 颜色过滤
        - 颜色不可靠时：自适应阈值二值化
        - color_weight 控制颜色容差的缩放（越高越严格）
        """
        import cv2

        has_color = template_info.get("has_color", False)
        dominant_hsv = template_info.get("dominant_hsv")
        color_tol_hsv = template_info.get("color_tol_hsv")

        if has_color and dominant_hsv is not None and color_tol_hsv is not None:
            hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            h, s, v = dominant_hsv
            dh, ds, dv = color_tol_hsv

            # color_weight 调节容差：weight=1.0 → 容差×0.5（严格），weight=0.0 → 容差×2.0（宽松）
            tol_scale = 2.0 - 1.5 * color_weight
            dh = max(5, int(dh * tol_scale))
            ds = max(20, int(ds * tol_scale))
            dv = max(30, int(dv * tol_scale))

            color_mask = ShapeExtractor._hsv_in_range(hsv_img, h, s, v, dh, ds, dv)
            return color_mask
        else:
            # 颜色不可靠 → 灰度自适应二值化
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            binary = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 4
            )
            return binary

    # ------------------------------------------------------------------ #
    #  HSV 范围过滤（处理 H 通道环绕）                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _hsv_in_range(
        hsv_img: np.ndarray,
        h: int, s: int, v: int,
        dh: int, ds: int, dv: int,
    ) -> np.ndarray:
        """HSV inRange，自动处理 H 通道在 0/180 边界的环绕。"""
        import cv2

        s_lo, s_hi = max(0, s - ds), min(255, s + ds)
        v_lo, v_hi = max(0, v - dv), min(255, v + dv)

        if h - dh < 0:
            m1 = cv2.inRange(
                hsv_img,
                np.array([0, s_lo, v_lo], np.uint8),
                np.array([h + dh, s_hi, v_hi], np.uint8),
            )
            m2 = cv2.inRange(
                hsv_img,
                np.array([180 + (h - dh), s_lo, v_lo], np.uint8),
                np.array([180, s_hi, v_hi], np.uint8),
            )
            return cv2.bitwise_or(m1, m2)
        elif h + dh > 180:
            m1 = cv2.inRange(
                hsv_img,
                np.array([h - dh, s_lo, v_lo], np.uint8),
                np.array([180, s_hi, v_hi], np.uint8),
            )
            m2 = cv2.inRange(
                hsv_img,
                np.array([0, s_lo, v_lo], np.uint8),
                np.array([(h + dh) - 180, s_hi, v_hi], np.uint8),
            )
            return cv2.bitwise_or(m1, m2)
        else:
            return cv2.inRange(
                hsv_img,
                np.array([h - dh, s_lo, v_lo], np.uint8),
                np.array([h + dh, s_hi, v_hi], np.uint8),
            )

    # ------------------------------------------------------------------ #
    #  辅助：提取主色                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_dominant_color(
        hsv_crop: np.ndarray,
        fg_mask: np.ndarray,
    ) -> Tuple[Tuple[int, int, int], Tuple[int, int, int], bool]:
        """
        从 HSV 截图的前景像素中提取主色。

        Returns:
            dominant_hsv : (H, S, V) 中位数
            color_tol    : (dH, dS, dV) 建议容差（基于像素值分布的 MAD）
            has_color    : 若 S > 40 则认为颜色可靠
        """
        pixels = hsv_crop[fg_mask]
        if len(pixels) == 0:
            return (0, 0, 128), (15, 60, 60), False

        h_vals = pixels[:, 0].astype(np.float32)
        s_vals = pixels[:, 1].astype(np.float32)
        v_vals = pixels[:, 2].astype(np.float32)

        # H 通道是循环的，用圆形统计中位数
        h_rad = h_vals * (np.pi / 90.0)
        h_median = int(np.round(
            np.arctan2(np.median(np.sin(h_rad)), np.median(np.cos(h_rad)))
            * (90.0 / np.pi)
        ) % 180)

        s_median = int(np.median(s_vals))
        v_median = int(np.median(v_vals))

        # MAD（绝对中位差）作为容差基准，至少给最小值
        h_mad = max(10, int(np.median(np.abs(h_vals - h_median))) * 2)
        s_mad = max(40, int(np.median(np.abs(s_vals - s_median))) * 2)
        v_mad = max(50, int(np.median(np.abs(v_vals - v_median))) * 2)

        # 饱和度 < 40 → 近似灰/白/黑，颜色信息不可靠
        has_color = s_median > 40

        return (h_median, s_median, v_median), (h_mad, s_mad, v_mad), has_color
