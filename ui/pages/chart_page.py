"""图表页面 — 数据预览、绘图与对比"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List, Optional

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    FluentIcon as FIF,
    PushButton,
    SubtitleLabel,
    ToolButton,
    isDarkTheme,
)

try:
    import matplotlib
    matplotlib.use("QtAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from core.project_manager import project_manager


class ChartPage(QWidget):
    """数据预览/绘图/对比页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._import_curves: List[dict] = []  # [{name, x, y}]
        self._setup_ui()
        self._refresh()

    # ──────────────────────────────── UI ────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # 顶部标题 + 工具栏
        header = QHBoxLayout()
        title = SubtitleLabel("图表", self)
        header.addWidget(title)
        header.addStretch()

        self._import_btn = PushButton(FIF.DOWNLOAD, "导入对比数据", self)
        self._import_btn.clicked.connect(self._on_import)
        header.addWidget(self._import_btn)

        self._clear_import_btn = PushButton(FIF.DELETE, "清除对比", self)
        self._clear_import_btn.clicked.connect(self._on_clear_import)
        header.addWidget(self._clear_import_btn)

        self._export_img_btn = PushButton(FIF.SAVE, "导出图片", self)
        self._export_img_btn.clicked.connect(self._on_export_image)
        header.addWidget(self._export_img_btn)

        self._refresh_btn = ToolButton(FIF.SYNC, self)
        self._refresh_btn.setToolTip("刷新")
        self._refresh_btn.clicked.connect(self._refresh)
        header.addWidget(self._refresh_btn)

        root.addLayout(header)

        # 主体：左边曲线列表 + 右边图表
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setHandleWidth(6)

        # 左侧面板
        left_card = CardWidget(self)
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        left_layout.addWidget(BodyLabel("曲线选择", left_card))

        self._curve_list = QListWidget(left_card)
        self._curve_list.setSelectionMode(QListWidget.MultiSelection)
        self._curve_list.itemSelectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self._curve_list)

        # 图表样式选项
        style_row = QHBoxLayout()
        style_row.addWidget(BodyLabel("线型:", left_card))
        self._line_style_combo = ComboBox(left_card)
        self._line_style_combo.addItems(["折线", "散点", "折线+散点"])
        self._line_style_combo.currentIndexChanged.connect(self._redraw)
        style_row.addWidget(self._line_style_combo)
        left_layout.addLayout(style_row)

        self._select_all_btn = PushButton(FIF.CHECKBOX, "全选", left_card)
        self._select_all_btn.clicked.connect(self._select_all)
        left_layout.addWidget(self._select_all_btn)

        left_card.setMinimumWidth(200)
        left_card.setMaximumWidth(280)
        splitter.addWidget(left_card)

        # 右侧图表
        right_card = CardWidget(self)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(8, 8, 8, 8)

        if HAS_MATPLOTLIB:
            self._figure = Figure(tight_layout=True)
            self._canvas = FigureCanvas(self._figure)
            self._canvas.setMinimumHeight(300)
            right_layout.addWidget(self._canvas)
        else:
            no_mpl = QLabel("matplotlib 未安装，请运行：uv add matplotlib", self)
            no_mpl.setAlignment(Qt.AlignCenter)
            right_layout.addWidget(no_mpl)
            self._figure = None
            self._canvas = None

        splitter.addWidget(right_card)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter, 1)

    # ──────────────────────────────── 数据 ───────────────────────────────

    def _get_project_curves(self) -> List[dict]:
        """获取当前项目中所有已有实际坐标的曲线"""
        proj = project_manager.current_project
        if proj is None:
            return []
        result = []
        for image in (proj.images or []):
            for curve in (image.curves or []):
                if curve.x_actual and curve.y_actual:
                    result.append({
                        "name": f"{image.name} / {curve.name}",
                        "x": list(curve.x_actual),
                        "y": list(curve.y_actual),
                        "source": "project",
                        "color": curve.color,
                    })
        return result

    def _refresh(self):
        """刷新曲线列表"""
        self._curve_list.clear()
        curves = self._get_project_curves()
        for c in curves:
            item = QListWidgetItem(c["name"])
            item.setData(Qt.UserRole, c)
            self._curve_list.addItem(item)

        # 添加导入的对比曲线
        for c in self._import_curves:
            item = QListWidgetItem(f"[导入] {c['name']}")
            item.setData(Qt.UserRole, c)
            item.setForeground(Qt.yellow if isDarkTheme() else Qt.darkGreen)
            self._curve_list.addItem(item)

        self._redraw()

    def _selected_curves(self) -> List[dict]:
        return [item.data(Qt.UserRole) for item in self._curve_list.selectedItems()]

    # ──────────────────────────────── 绘图 ───────────────────────────────

    def _redraw(self):
        if not HAS_MATPLOTLIB or self._figure is None:
            return

        self._figure.clear()
        ax = self._figure.add_subplot(111)

        # 主题适配
        dark = isDarkTheme()
        bg_color = "#1e1e1e" if dark else "#ffffff"
        fg_color = "#cccccc" if dark else "#222222"
        grid_color = "#444444" if dark else "#dddddd"

        self._figure.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        ax.tick_params(colors=fg_color)
        ax.xaxis.label.set_color(fg_color)
        ax.yaxis.label.set_color(fg_color)
        ax.title.set_color(fg_color)
        for spine in ax.spines.values():
            spine.set_edgecolor(fg_color)
        ax.grid(True, color=grid_color, linestyle="--", linewidth=0.5, alpha=0.7)

        selected = self._selected_curves()
        style_idx = self._line_style_combo.currentIndex()  # 0=line,1=scatter,2=both

        for c in selected:
            x, y = c["x"], c["y"]
            label = c["name"]
            color = c.get("color", None)
            kwargs = {"label": label}
            if color:
                kwargs["color"] = color

            if style_idx == 0:
                ax.plot(x, y, linewidth=1.4, **kwargs)
            elif style_idx == 1:
                ax.scatter(x, y, s=12, **kwargs)
            else:
                ax.plot(x, y, linewidth=1.2, **kwargs)
                ax.scatter(x, y, s=8, color=kwargs.get("color", None))

        if selected:
            legend = ax.legend(
                facecolor=bg_color,
                edgecolor=fg_color,
                labelcolor=fg_color,
                fontsize=8,
            )

        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title("曲线图表")

        self._canvas.draw()

    # ──────────────────────────────── 动作 ───────────────────────────────

    def _select_all(self):
        self._curve_list.selectAll()

    def _on_selection_changed(self):
        self._redraw()

    def _on_import(self):
        """导入 CSV/JSON 格式的对比数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入对比数据",
            "",
            "数据文件 (*.csv *.json);;CSV (*.csv);;JSON (*.json)",
        )
        if not file_path:
            return

        try:
            curves = _load_data_file(file_path)
            self._import_curves.extend(curves)
            self._refresh()
        except Exception as e:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.error(
                title="导入失败",
                content=str(e),
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self,
            )

    def _on_clear_import(self):
        self._import_curves.clear()
        self._refresh()

    def _on_export_image(self):
        if not HAS_MATPLOTLIB or self._figure is None:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出图片",
            "chart.png",
            "PNG (*.png);;SVG (*.svg);;PDF (*.pdf)",
        )
        if file_path:
            self._figure.savefig(file_path, dpi=150, bbox_inches="tight")
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.success(
                title="导出成功",
                content=file_path,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )


# ─────────────────────── 数据加载工具函数 ────────────────────────

def _load_data_file(file_path: str) -> List[dict]:
    """解析 CSV 或 JSON 文件，返回曲线列表"""
    p = Path(file_path)
    name = p.stem

    if p.suffix.lower() == ".json":
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            # [{x: [...], y: [...]}, ...]  或  [[x, y], ...]
            if data and isinstance(data[0], (list, tuple)):
                xs = [float(row[0]) for row in data]
                ys = [float(row[1]) for row in data]
                return [{"name": name, "x": xs, "y": ys, "source": "import"}]
            elif data and isinstance(data[0], dict):
                curves = []
                for i, item in enumerate(data):
                    x = item.get("x", item.get("X", []))
                    y = item.get("y", item.get("Y", []))
                    n = item.get("name", f"{name}_{i+1}")
                    curves.append({"name": n, "x": list(x), "y": list(y), "source": "import"})
                return curves
        elif isinstance(data, dict):
            x = data.get("x", data.get("X", []))
            y = data.get("y", data.get("Y", []))
            n = data.get("name", name)
            return [{"name": n, "x": list(x), "y": list(y), "source": "import"}]
        return []

    else:  # CSV
        with open(p, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            return []

        # 尝试检测标头
        header = rows[0]
        try:
            float(header[0])
            data_rows = rows
            col_x, col_y = 0, 1
        except ValueError:
            data_rows = rows[1:]
            col_x, col_y = 0, 1

        xs, ys = [], []
        for row in data_rows:
            if len(row) >= 2:
                try:
                    xs.append(float(row[col_x]))
                    ys.append(float(row[col_y]))
                except ValueError:
                    continue

        return [{"name": name, "x": xs, "y": ys, "source": "import"}]
