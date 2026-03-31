"""图形识别提取器（测试功能）

通过模板匹配在图片中寻找与截图图例形状相似的点，以各匹配中心作为曲线点位置。
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np


class ShapeExtractor:
    """基于模板匹配的图形识别曲线点提取器（测试功能）"""

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
        """从图片中截取矩形区域，提取有效形状模板。

        对截取区域做边缘检测，找到最大的闭合形状作为匹配模板。

        Returns:
            dict 包含:
              'raw'     : ndarray (BGR)  — 原始截图
              'template': ndarray        — 灰度匹配模板（用于 matchTemplate）
              'edges'   : ndarray        — Canny 边缘图（预览用）
              'binary'  : ndarray        — 二值化形状图（用于预览显示）
              'size'    : (w, h)         — 模板尺寸（像素）
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

        # 高斯模糊去噪，再 Canny 边缘检测
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(blurred, 30, 120)

        # 膨胀连接断线
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=1)

        # 找最大轮廓，填充得到实心形状作为二值模板
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        binary = np.zeros_like(gray, dtype=np.uint8)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            cv2.drawContours(binary, [largest], -1, 255, cv2.FILLED)
        else:
            # fallback：Otsu 二值化
            _, binary = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

        return {
            "raw": raw,
            "template": gray,     # 用于 matchTemplate 的灰度模板
            "edges": edges,        # Canny 边缘图
            "binary": binary,      # 实心二值化形状（预览/调试用）
            "size": (x2i - x1i, y2i - y1i),
        }

    # ------------------------------------------------------------------ #
    #  提取：在图片中搜索与模板匹配的形状，返回中心点列表                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def extract(
        image_path: str,
        template_info: dict,
        mask_polygons: Optional[list] = None,
        mask_include_mode: bool = True,
        step: int = 1,
        threshold: float = 0.65,
    ) -> List[Tuple[float, float]]:
        """在图片中搜索与模板相似的形状，返回各匹配中心点的像素坐标列表。

        Args:
            image_path:        图片路径
            template_info:     preprocess_region() 返回的字典
            mask_polygons:     蒙版多边形列表（格式与 AutoExtractor 相同）
            mask_include_mode: True = 蒙版内才识别；False = 蒙版内不识别
            step:              影响 NMS 抑制半径，越大重叠点合并越积极（点越稀疏）
            threshold:         匹配阈值 [0, 1]，越高越严格

        Returns:
            list of (x, y) 图片像素坐标
        """
        import cv2

        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")

        img_h, img_w = img.shape[:2]
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        template = template_info.get("template")
        tw, th = template_info["size"]

        if template is None:
            raise ValueError("模板信息不完整，请重新截图")
        if tw >= img_w or th >= img_h:
            raise ValueError("模板尺寸超过图片尺寸，请缩小截图区域")

        # ---- 模板归一化互相关 ----
        result = cv2.matchTemplate(gray_img, template, cv2.TM_CCOEFF_NORMED)

        # ---- 应用蒙版限制搜索区域 ----
        if mask_polygons:
            mask_img = np.zeros((img_h, img_w), dtype=np.uint8)
            pts_list = [
                np.array([(int(x), int(y)) for x, y in poly], dtype=np.int32)
                for poly in mask_polygons
            ]
            cv2.fillPoly(mask_img, pts_list, 255)

            result_h, result_w = result.shape[:2]
            half_tw = tw // 2
            half_th = th // 2
            # 将蒙版裁剪到 matchTemplate 结果坐标空间
            m_crop = mask_img[
                half_th : half_th + result_h, half_tw : half_tw + result_w
            ]
            if m_crop.shape == result.shape:
                if mask_include_mode:
                    result[m_crop == 0] = -1.0
                else:
                    result[m_crop > 0] = -1.0

        # ---- 非极大值抑制寻找多个极值 ----
        nms_radius = max(2, max(tw, th) // 2 * step)
        raw_points = ShapeExtractor._nms(result, threshold, nms_radius)

        # 将 matchTemplate 返回的左上角坐标转换为模板中心坐标
        cx_off = tw / 2.0
        cy_off = th / 2.0
        return [(x + cx_off, y + cy_off) for x, y in raw_points]

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

        # 超过阈值的区域掩码
        above = (score_map >= threshold).astype(np.uint8)

        # 局部极大值：膨胀后与原图相等的位置
        kernel_size = max(3, radius * 2 + 1)
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (kernel_size, kernel_size)
        )
        dilated = cv2.dilate(score_map, kernel)
        local_max = (score_map == dilated) & (above > 0)

        ys, xs = np.where(local_max)
        if len(xs) == 0:
            return []

        # 按得分降序排列
        scores = score_map[ys, xs]
        order = np.argsort(-scores)
        ys, xs = ys[order], xs[order]
        return [(int(x), int(y)) for x, y in zip(xs, ys)]
