"""图形识别提取器（V1.2.1 — 轮廓形状描述子方案）

核心思路：
  1. 从截图模板中提取最大轮廓 → 计算 Hu 矩作为形状描述子
  2. 全图颜色过滤 → 多级形态学开运算剥离曲线 → 连通域分析 → 面积/形状过滤
  3. 对每个候选连通域 → cv2.matchShapes() + 实心度 + 宽高比 综合评判
  4. 匹配连通域的质心作为结果点

优势：
  - 多级开运算：先用递增核剥离曲线细线，保留标记块体
  - 多指标融合：Hu 矩 + 实心度 + 宽高比三重过滤
  - 尺度/旋转不敏感，抗背景干扰
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from core.image_io import cv2_imread_unicode


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
              'solidity'         : float          — 模板实心度 (area / convexHullArea)
              'aspect_ratio'     : float          — 模板宽高比 (w/h of bounding rect)
              'dominant_hsv'     : (H, S, V) int  — 前景主色（HSV）
              'color_tol_hsv'    : (dH, dS, dV)   — 建议容差
              'has_color'        : bool            — 主色是否有足够饱和度可用
              'size'             : (w, h)          — 模板尺寸（像素）
        """
        import cv2

        img = cv2_imread_unicode(image_path)
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

        # 计算实心度和宽高比
        hull = cv2.convexHull(largest)
        hull_area = cv2.contourArea(hull)
        solidity = contour_area / hull_area if hull_area > 0 else 0.0

        _, _, bw, bh = cv2.boundingRect(largest)
        aspect_ratio = bw / bh if bh > 0 else 1.0

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
            "solidity": float(solidity),
            "aspect_ratio": float(aspect_ratio),
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
          2. 多级形态学开运算 → 逐级连通域分析 → 面积/形状过滤
          3. 多指标评判：Hu 矩 + 实心度 + 宽高比
          4. NMS 去重 → 质心作为结果点

        Args:
            image_path:        图片路径
            template_info:     preprocess_region() 返回的字典
            mask_polygons:     蒙版多边形列表
            mask_include_mode: True = 蒙版内才识别；False = 蒙版内不识别
            step:              未使用（保留接口兼容）
            threshold:         形状相似度阈值 [0, 1]；越大越宽松
            color_weight:      颜色过滤的严格程度 (0.0~1.0)
        Returns:
            list of (x, y) 图片像素坐标
        """
        import cv2

        img = cv2_imread_unicode(image_path)
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")

        img_h, img_w = img.shape[:2]
        template_contour = template_info["contour"]
        template_area = template_info["contour_area"]
        template_solidity = template_info.get("solidity", 0.8)
        template_ar = template_info.get("aspect_ratio", 1.0)

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
                fg_mask = cv2.bitwise_and(fg_mask, search_mask)
            else:
                fg_mask = cv2.bitwise_and(fg_mask, cv2.bitwise_not(search_mask))

        # ---- 面积过滤范围 ----
        area_lo = template_area * 0.1
        area_hi = template_area * 8.0

        # ---- 形状相似度阈值映射 ----
        # threshold=1.0 → 非常宽松(dist_thr=1.5)  threshold=0.0 → 极严格(dist_thr=0.05)
        dist_thr = 0.05 + threshold * 1.45

        # ---- 多级开运算 + 原始掩膜，收集所有候选 ----
        # 开运算可剥离细曲线（1-2px 宽），保留较粗的标记形状
        raw_candidates: list[Tuple[float, float, float]] = []  # (cx, cy, score)

        # 确定开运算核大小范围：基于模板尺寸
        tw, th = template_info["size"]
        min_dim = min(tw, th)
        # 核大小从 0（原始）到 min_dim//3，最少 2 级
        max_ksize = max(3, min(min_dim // 3, 7))
        open_ksizes = [0] + list(range(2, max_ksize + 1))

        seen_centers: set = set()  # 粗去重（网格化）
        dedup_radius = max(3, min(tw, th) // 2)

        for ksize in open_ksizes:
            if ksize == 0:
                working_mask = fg_mask.copy()
            else:
                k_open = cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE, (ksize, ksize)
                )
                working_mask = cv2.morphologyEx(
                    fg_mask, cv2.MORPH_OPEN, k_open, iterations=1
                )

            # 闭运算填补小孔
            k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            working_mask = cv2.morphologyEx(
                working_mask, cv2.MORPH_CLOSE, k_close, iterations=1
            )

            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
                working_mask, connectivity=8
            )

            for i in range(1, num_labels):
                area = stats[i, cv2.CC_STAT_AREA]
                if area < area_lo or area > area_hi:
                    continue

                cx, cy = centroids[i]

                # 粗网格去重：避免同一标记在不同开运算级别被重复评估
                grid_key = (int(cx) // dedup_radius, int(cy) // dedup_radius)
                if grid_key in seen_centers:
                    continue

                # 提取该连通域的轮廓
                blob_mask = (labels == i).astype(np.uint8) * 255
                blob_contours, _ = cv2.findContours(
                    blob_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                if not blob_contours:
                    continue

                blob_contour = max(blob_contours, key=cv2.contourArea)
                blob_area = cv2.contourArea(blob_contour)
                if blob_area < 4:
                    continue

                # ---- 多指标评判 ----
                score = ShapeExtractor._evaluate_candidate(
                    template_contour, template_solidity, template_ar,
                    blob_contour, blob_area, dist_thr,
                )

                if score >= 0:
                    seen_centers.add(grid_key)
                    raw_candidates.append((float(cx), float(cy), score))

        # ---- NMS 去重 ----
        results = ShapeExtractor._nms_points(raw_candidates, dedup_radius)

        return results

    # ------------------------------------------------------------------ #
    #  多指标候选评判                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _evaluate_candidate(
        template_contour: np.ndarray,
        template_solidity: float,
        template_ar: float,
        blob_contour: np.ndarray,
        blob_area: float,
        dist_thr: float,
    ) -> float:
        """评判单个候选连通域与模板的相似度。

        返回 >= 0 的评分（越小越像）表示通过，返回 -1 表示不通过。
        """
        import cv2

        # 1. Hu 矩形状比对（主要指标，使用三种方法取最小）
        d1 = cv2.matchShapes(
            template_contour, blob_contour, cv2.CONTOURS_MATCH_I1, 0.0
        )
        d2 = cv2.matchShapes(
            template_contour, blob_contour, cv2.CONTOURS_MATCH_I2, 0.0
        )
        d3 = cv2.matchShapes(
            template_contour, blob_contour, cv2.CONTOURS_MATCH_I3, 0.0
        )
        # 取最小距离（最宽松的方法通过即可）
        hu_dist = min(d1, d2, d3)

        if hu_dist > dist_thr:
            return -1.0

        # 2. 实心度检查（面积/凸包面积）
        hull = cv2.convexHull(blob_contour)
        hull_area = cv2.contourArea(hull)
        blob_solidity = blob_area / hull_area if hull_area > 0 else 0.0

        # 允许实心度偏差 0.35
        if abs(blob_solidity - template_solidity) > 0.35:
            return -1.0

        # 3. 宽高比检查
        _, _, bw, bh = cv2.boundingRect(blob_contour)
        blob_ar = bw / bh if bh > 0 else 1.0

        # 允许宽高比偏差因子 2.5x
        ar_ratio = max(blob_ar, template_ar) / max(min(blob_ar, template_ar), 0.01)
        if ar_ratio > 2.5:
            return -1.0

        return hu_dist

    # ------------------------------------------------------------------ #
    #  NMS 点去重                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _nms_points(
        candidates: list[Tuple[float, float, float]],
        radius: int,
    ) -> List[Tuple[float, float]]:
        """对候选点按评分排序后做距离 NMS 去重。"""
        if not candidates:
            return []

        # 按评分升序排（越小越好）
        candidates.sort(key=lambda c: c[2])

        results: List[Tuple[float, float]] = []
        r2 = radius * radius

        for cx, cy, _ in candidates:
            too_close = False
            for rx, ry in results:
                if (cx - rx) ** 2 + (cy - ry) ** 2 < r2:
                    too_close = True
                    break
            if not too_close:
                results.append((cx, cy))

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
