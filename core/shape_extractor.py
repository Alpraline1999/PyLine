"""图形识别提取器（测试功能）

改进管线（V1.2.0）：
  Phase 1 — 颜色引导：从模板提取主色，在颜色相似度图上匹配，消除不同色曲线干扰
  Phase 2 — 形状遮罩：用 matchTemplate mask 参数屏蔽背景像素，评分仅计形状前景
  Phase 3 — 边缘辅助：在 Canny 边缘图上做轮廓匹配，加权融合（适合黑白标记）

三个阶段可通过 color_weight 参数调节：
  color_weight = 1.0  → 仅颜色+形状遮罩（Phase 1+2）
  color_weight = 0.0  → 仅边缘轮廓（Phase 3）
  color_weight = 0.7  → 默认，加权融合
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np


class ShapeExtractor:
    """基于多阶段模板匹配的图形识别曲线点提取器（测试功能）"""

    # ------------------------------------------------------------------ #
    #  预处理：从图片截取区域并提取有效形状作为模板                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def preprocess_region(
        image_path: str,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> dict:
        """从图片中截取矩形区域，提取多阶段匹配所需的模板信息。

        Returns:
            dict 包含:
              'raw'              : ndarray (BGR)  — 原始截图
              'template'         : ndarray uint8  — 灰度图（兼容旧接口）
              'binary'           : ndarray uint8  — 实心二值形状（前景=255）
              'binary_float'     : ndarray float32 [0,1] — 与 mask 配合使用
              'edges'            : ndarray uint8  — Canny 边缘图（轮廓匹配用）
              'edges_float'      : ndarray float32 [0,1]
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

        # ---- 提取前景主色（Phase 1）----
        hsv_raw = cv2.cvtColor(raw, cv2.COLOR_BGR2HSV)
        fg_mask = binary > 0
        dominant_hsv, color_tol_hsv, has_color = ShapeExtractor._extract_dominant_color(
            hsv_raw, fg_mask
        )

        # ---- 边缘图（Phase 3）----
        # 用更激进的参数提取轮廓（线宽 1px，不填充）
        edges_outline = cv2.Canny(blurred, 20, 80)
        # 膨胀 1px，使轮廓对微小偏移更宽容
        k1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        edges_outline = cv2.dilate(edges_outline, k1, iterations=1)

        binary_float = binary.astype(np.float32) / 255.0
        edges_float = edges_outline.astype(np.float32) / 255.0

        return {
            "raw": raw,
            "template": gray,
            "binary": binary,
            "binary_float": binary_float,
            "edges": edges_outline,
            "edges_float": edges_float,
            "dominant_hsv": dominant_hsv,
            "color_tol_hsv": color_tol_hsv,
            "has_color": has_color,
            "size": (x2i - x1i, y2i - y1i),
        }

    # ------------------------------------------------------------------ #
    #  提取：多阶段管线                                                     #
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
        """在图片中搜索与模板相似的形状，返回各匹配中心点的像素坐标列表。

        三阶段管线：
          Phase 1+2: 颜色相似度图 × 形状遮罩匹配
          Phase 3:   边缘轮廓匹配
          融合: final = color_weight * score_12 + (1 - color_weight) * score_3

        Args:
            image_path:        图片路径
            template_info:     preprocess_region() 返回的字典
            mask_polygons:     蒙版多边形列表
            mask_include_mode: True = 蒙版内才识别；False = 蒙版内不识别
            step:              NMS 抑制半径倍率，越大点越稀疏
            threshold:         融合评分阈值 [0, 1]
            color_weight:      颜色+形状评分的权重（0.0~1.0）；
                               若标记颜色饱和度不足则自动降权
        Returns:
            list of (x, y) 图片像素坐标
        """
        import cv2

        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")

        img_h, img_w = img.shape[:2]
        tw, th = template_info["size"]

        if tw >= img_w or th >= img_h:
            raise ValueError("模板尺寸超过图片尺寸，请缩小截图区域")

        # ---- 若主色不可靠，自动降低颜色权重 ----
        effective_cw = color_weight
        if not template_info.get("has_color", True):
            effective_cw = min(color_weight, 0.3)

        # ---- Phase 1+2: 颜色相似度图 + 形状遮罩匹配 ----
        score_12 = ShapeExtractor._phase12_score(img, template_info, img_h, img_w)

        # ---- Phase 3: 边缘轮廓匹配 ----
        score_3 = ShapeExtractor._phase3_score(img, template_info, img_h, img_w)

        # ---- 对齐尺寸（matchTemplate 输出比输入小 tw-1 × th-1）----
        rh = img_h - th + 1
        rw = img_w - tw + 1
        if score_12 is not None:
            score_12 = score_12[:rh, :rw]
        if score_3 is not None:
            score_3 = score_3[:rh, :rw]

        # ---- 加权融合 ----
        if score_12 is not None and score_3 is not None:
            result = effective_cw * score_12 + (1 - effective_cw) * score_3
        elif score_12 is not None:
            result = score_12
        elif score_3 is not None:
            result = score_3
        else:
            return []

        # ---- 应用搜索蒙版 ----
        if mask_polygons:
            mask_img = np.zeros((img_h, img_w), dtype=np.uint8)
            pts_list = [
                np.array([(int(x), int(y)) for x, y in poly], dtype=np.int32)
                for poly in mask_polygons
            ]
            import cv2 as _cv2
            _cv2.fillPoly(mask_img, pts_list, 255)

            half_tw, half_th = tw // 2, th // 2
            m_crop = mask_img[half_th: half_th + rh, half_tw: half_tw + rw]
            if m_crop.shape == result.shape:
                if mask_include_mode:
                    result[m_crop == 0] = -1.0
                else:
                    result[m_crop > 0] = -1.0

        # ---- NMS ----
        nms_radius = max(2, max(tw, th) // 2 * step)
        raw_points = ShapeExtractor._nms(result, threshold, nms_radius)

        cx_off = tw / 2.0
        cy_off = th / 2.0
        return [(x + cx_off, y + cy_off) for x, y in raw_points]

    # ------------------------------------------------------------------ #
    #  Phase 1+2：颜色相似度图 + 形状遮罩匹配                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _phase12_score(
        img: np.ndarray,
        template_info: dict,
        img_h: int,
        img_w: int,
    ) -> Optional[np.ndarray]:
        """
        在颜色相似度图（0~1 float）上用实心形状模板做 TM_CCORR_NORMED 匹配。
        mask 参数只评分形状前景像素，排除背景干扰。
        """
        import cv2

        binary_float = template_info.get("binary_float")
        if binary_float is None:
            return None

        dominant_hsv = template_info.get("dominant_hsv")
        color_tol_hsv = template_info.get("color_tol_hsv")
        has_color = template_info.get("has_color", False)

        if has_color and dominant_hsv is not None and color_tol_hsv is not None:
            # 构建颜色相似度图（前景颜色范围内=1，否则=0）
            hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            h, s, v = dominant_hsv
            dh, ds, dv = color_tol_hsv
            lower = np.array([max(0, h - dh), max(0, s - ds), max(0, v - dv)], dtype=np.uint8)
            upper = np.array([min(180, h + dh), min(255, s + ds), min(255, v + dv)], dtype=np.uint8)

            if h - dh < 0:
                # 跨越 H=0 的红色区域，分两段
                m1 = cv2.inRange(hsv_img, np.array([0, max(0, s - ds), max(0, v - dv)], np.uint8),
                                 np.array([h + dh, min(255, s + ds), min(255, v + dv)], np.uint8))
                m2 = cv2.inRange(hsv_img, np.array([180 + (h - dh), max(0, s - ds), max(0, v - dv)], np.uint8),
                                 np.array([180, min(255, s + ds), min(255, v + dv)], np.uint8))
                color_mask = cv2.bitwise_or(m1, m2)
            elif h + dh > 180:
                m1 = cv2.inRange(hsv_img, lower, np.array([180, min(255, s + ds), min(255, v + dv)], np.uint8))
                m2 = cv2.inRange(hsv_img, np.array([0, max(0, s - ds), max(0, v - dv)], np.uint8),
                                 np.array([(h + dh) - 180, min(255, s + ds), min(255, v + dv)], np.uint8))
                color_mask = cv2.bitwise_or(m1, m2)
            else:
                color_mask = cv2.inRange(hsv_img, lower, upper)

            search_map = color_mask.astype(np.float32) / 255.0
        else:
            # 颜色不可靠 → 退化为灰度图归一化
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            search_map = gray_img.astype(np.float32) / 255.0

        # 形状遮罩：只评分 binary 前景位置
        tmpl_uint8 = (binary_float * 255).astype(np.uint8)
        mask_uint8 = tmpl_uint8  # mask 与 template 相同（前景=255）

        try:
            score = cv2.matchTemplate(
                search_map, binary_float, cv2.TM_CCORR_NORMED, mask=mask_uint8
            )
        except cv2.error:
            # opencv 版本不支持 float32 mask fallback
            score = cv2.matchTemplate(search_map, binary_float, cv2.TM_CCORR_NORMED)

        return score

    # ------------------------------------------------------------------ #
    #  Phase 3：边缘轮廓匹配                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _phase3_score(
        img: np.ndarray,
        template_info: dict,
        img_h: int,
        img_w: int,
    ) -> Optional[np.ndarray]:
        """
        在搜索图的 Canny 边缘图上用模板边缘做 TM_CCORR_NORMED 匹配。
        """
        import cv2

        edges_float = template_info.get("edges_float")
        if edges_float is None:
            return None

        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray_img, (3, 3), 0)
        # 使用与 preprocess_region 相同的参数，保证边缘风格一致
        edges_search = cv2.Canny(blurred, 20, 80)
        k1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        edges_search = cv2.dilate(edges_search, k1, iterations=1)

        search_map = edges_search.astype(np.float32) / 255.0

        # 模板边缘的膨胀图也作为 mask（只评分有轮廓的位置）
        edges_uint8 = (edges_float * 255).astype(np.uint8)
        try:
            score = cv2.matchTemplate(
                search_map, edges_float, cv2.TM_CCORR_NORMED, mask=edges_uint8
            )
        except cv2.error:
            score = cv2.matchTemplate(search_map, edges_float, cv2.TM_CCORR_NORMED)

        return score

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

    # ------------------------------------------------------------------ #
    #  辅助：非极大值抑制                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _nms(
        score_map: np.ndarray,
        threshold: float,
        radius: int,
    ) -> List[Tuple[int, int]]:
        """在 radius 邻域内抑制非极大值，返回 (x, y) 列表（按得分降序）。"""
        import cv2

        above = (score_map >= threshold).astype(np.uint8)

        kernel_size = max(3, radius * 2 + 1)
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (kernel_size, kernel_size)
        )
        dilated = cv2.dilate(score_map, kernel)
        local_max = (score_map == dilated) & (above > 0)

        ys, xs = np.where(local_max)
        if len(xs) == 0:
            return []

        scores = score_map[ys, xs]
        order = np.argsort(-scores)
        ys, xs = ys[order], xs[order]
        return [(int(x), int(y)) for x, y in zip(xs, ys)]
