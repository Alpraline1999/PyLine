"""
曲线平滑/重采样模块
"""
from __future__ import annotations

from typing import Tuple, List
import math


def smooth_moving_average(
    x: List[float],
    y: List[float],
    window: int = 3,
) -> Tuple[List[float], List[float]]:
    """
    移动平均平滑。

    参数:
        x, y: 输入坐标列表（长度相同，已按 x 排序）
        window: 窗口大小（奇数，至少 3）
    返回:
        (x_smooth, y_smooth)
    """
    if len(x) < 2:
        return list(x), list(y)

    window = max(3, window | 1)  # 强制为奇数且 ≥3
    half = window // 2
    n = len(y)
    y_smooth = []
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        y_smooth.append(sum(y[lo:hi]) / (hi - lo))
    return list(x), y_smooth


def smooth_savgol(
    x: List[float],
    y: List[float],
    window: int = 5,
    poly: int = 2,
) -> Tuple[List[float], List[float]]:
    """
    Savitzky-Golay 平滑（纯 Python 实现，无 scipy 依赖）。

    参数:
        x, y: 输入列表
        window: 窗口大小（奇数，>= poly+1）
        poly: 多项式阶数
    返回:
        (x_smooth, y_smooth)
    """
    if len(x) < window:
        return smooth_moving_average(x, y, window=max(3, len(x) | 1))

    window = max(poly + 1, window | 1)  # 奇数
    half = window // 2

    # 计算 Savitzky-Golay 系数
    coeffs = _savgol_coeffs(window, poly)

    n = len(y)
    y_smooth = []
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        # 边缘使用镜像填充
        sub = []
        for j in range(i - half, i + half + 1):
            if 0 <= j < n:
                sub.append(y[j])
            elif j < 0:
                sub.append(y[0])
            else:
                sub.append(y[-1])
        val = sum(c * v for c, v in zip(coeffs, sub))
        y_smooth.append(val)
    return list(x), y_smooth


def _savgol_coeffs(window: int, poly: int) -> List[float]:
    """计算 Savitzky-Golay 平滑系数（最小二乘多项式拟合）"""
    half = window // 2
    # 构建 Vandermonde 矩阵
    J = [[float(i ** k) for k in range(poly + 1)] for i in range(-half, half + 1)]
    # 计算 (J^T J)^-1 J^T
    JT = _transpose(J)
    JTJ = _matmul(JT, J)
    JTJ_inv = _mat_inv(JTJ)
    pinv = _matmul(JTJ_inv, JT)
    # 取第 0 行（0 阶，即平滑值本身）
    return pinv[0]


def _transpose(m: List[List[float]]) -> List[List[float]]:
    return [[m[r][c] for r in range(len(m))] for c in range(len(m[0]))]


def _matmul(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    ra, ca = len(a), len(a[0])
    rb, cb = len(b), len(b[0])
    assert ca == rb
    result = [[0.0] * cb for _ in range(ra)]
    for i in range(ra):
        for j in range(cb):
            for k in range(ca):
                result[i][j] += a[i][k] * b[k][j]
    return result


def _mat_inv(m: List[List[float]]) -> List[List[float]]:
    """高斯消元法求逆矩阵"""
    n = len(m)
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[pivot] = aug[pivot], aug[col]
        div = aug[col][col]
        if abs(div) < 1e-12:
            raise ValueError("矩阵奇异，无法求逆")
        aug[col] = [v / div for v in aug[col]]
        for row in range(n):
            if row != col:
                factor = aug[row][col]
                aug[row] = [aug[row][j] - factor * aug[col][j] for j in range(2 * n)]
    return [row[n:] for row in aug]


def resample_uniform(
    x: List[float],
    y: List[float],
    n_points: int,
) -> Tuple[List[float], List[float]]:
    """
    均匀间隔重采样（线性插值）。

    参数:
        x, y: 输入列表（已按 x 排序）
        n_points: 重采样点数
    返回:
        (x_new, y_new)
    """
    if len(x) < 2 or n_points < 2:
        return list(x), list(y)

    x_min, x_max = x[0], x[-1]
    if x_min == x_max:
        return list(x), list(y)

    x_new = [x_min + i * (x_max - x_min) / (n_points - 1) for i in range(n_points)]
    y_new = [_interp(x_val, x, y) for x_val in x_new]
    return x_new, y_new


def _interp(x_val: float, x: List[float], y: List[float]) -> float:
    """简单线性插值"""
    if x_val <= x[0]:
        return y[0]
    if x_val >= x[-1]:
        return y[-1]
    # 二分查找
    lo, hi = 0, len(x) - 1
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if x[mid] <= x_val:
            lo = mid
        else:
            hi = mid
    t = (x_val - x[lo]) / (x[hi] - x[lo])
    return y[lo] + t * (y[hi] - y[lo])
