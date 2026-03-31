"""图表页面 — 数据预览、绘图与对比"""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from ui.theme import text_color, make_section_label, make_hsep

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QListWidgetItem,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    ListWidget,
    CardWidget,
    ComboBox,
    FluentIcon as FIF,
    LineEdit,
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
    from matplotlib import font_manager

    _CJK_FONT_FILES = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    _cjk_font_prop = None
    for _f in _CJK_FONT_FILES:
        if os.path.exists(_f):
            font_manager.fontManager.addfont(_f)
            _cjk_font_prop = font_manager.FontProperties(fname=_f)
            matplotlib.rcParams["font.family"] = _cjk_font_prop.get_name()
            break

    if _cjk_font_prop is None:
        _CJK_NAMES = ["Noto Sans CJK JP", "Noto Sans CJK SC", "WenQuanYi Micro Hei", "SimHei"]
        _found = next(
            (n for n in _CJK_NAMES if any(n == fm.name for fm in font_manager.fontManager.ttflist)),
            None,
        )
        if _found:
            matplotlib.rcParams["font.family"] = _found

    matplotlib.rcParams["axes.unicode_minus"] = False
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from core.project_manager import project_manager

_STYLES = [
    ("实线 —",         "-",   ""),
    ("虚线 - -",       "--",  ""),
    ("点线 ···",       ":",   ""),
    ("点划线 —·",      "-.",  ""),
    ("散点 ○",         "",    "o"),
    ("散点 □",         "",    "s"),
    ("散点 △",         "",    "^"),
    ("散点+线 ○—",     "-",   "o"),
    ("散点+线 □—",     "-",   "s"),
]
_STYLE_LABELS     = [s[0] for s in _STYLES]
_STYLE_LINESTYLES = [s[1] for s in _STYLES]
_STYLE_MARKERS    = [s[2] for s in _STYLES]


class ChartPage(QWidget):
    """数据预览/绘图/对比页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._import_curves: List[dict] = []
        self._curve_styles: Dict[str, dict] = {}   # name → {"color": str, "linestyle": str}
        self._style_target: Optional[str] = None   # 当前正在编辑样式的曲线名
        self._setup_ui()
        self._refresh()

    # ──────────────────────────── UI ────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setHandleWidth(6)

        # \u2500\u2500 \u5de6\u4fa7\u9762\u677f \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        left_card = CardWidget(self)
        lv = QVBoxLayout(left_card)
        lv.setContentsMargins(12, 12, 12, 12)
        lv.setSpacing(8)

        lv.addWidget(make_section_label("数据对比", left_card))

        btn_grid = QGridLayout()
        btn_grid.setSpacing(4)

        self._import_btn = PushButton(FIF.DOWNLOAD, "导入数据", left_card)
        self._import_btn.setFixedHeight(32)
        self._import_btn.clicked.connect(self._on_import)
        btn_grid.addWidget(self._import_btn, 0, 0)

        self._clear_import_btn = PushButton(FIF.DELETE, "清除绘图", left_card)
        self._clear_import_btn.setFixedHeight(32)
        self._clear_import_btn.clicked.connect(self._on_clear_import)
        btn_grid.addWidget(self._clear_import_btn, 0, 1)

        self._export_img_btn = PushButton(FIF.SAVE, "导出图片", left_card)
        self._export_img_btn.setFixedHeight(32)
        self._export_img_btn.clicked.connect(self._on_export_image)
        btn_grid.addWidget(self._export_img_btn, 1, 0)

        self._refresh_btn = PushButton(FIF.SYNC, "刷新", left_card)
        self._refresh_btn.setFixedHeight(32)
        self._refresh_btn.clicked.connect(self._refresh)
        btn_grid.addWidget(self._refresh_btn, 1, 1)

        btn_grid.setColumnStretch(0, 1)
        btn_grid.setColumnStretch(1, 1)
        lv.addLayout(btn_grid)

        lv.addWidget(make_hsep(left_card))

        lv.addWidget(make_section_label("曲线选择", left_card))

        self._curve_list = ListWidget(left_card)
        self._curve_list.setSelectionMode(ListWidget.MultiSelection)
        self._curve_list.itemSelectionChanged.connect(self._on_selection_changed)
        self._curve_list.currentItemChanged.connect(self._on_current_item_changed)
        lv.addWidget(self._curve_list)

        # \u5168\u9009 + \u5220\u9664\u5bfc\u5165\u66f2\u7ebf\uff08\u5e76\u6392\uff09
        sel_row = QHBoxLayout()
        self._select_all_btn = PushButton(FIF.CHECKBOX, "全选", left_card)
        self._select_all_btn.setFixedHeight(30)
        self._select_all_btn.clicked.connect(self._select_all)
        sel_row.addWidget(self._select_all_btn)

        self._delete_import_btn = PushButton(FIF.DELETE, "删除导入", left_card)
        self._delete_import_btn.setFixedHeight(30)
        self._delete_import_btn.setEnabled(False)
        self._delete_import_btn.clicked.connect(self._on_delete_import_curve)
        sel_row.addWidget(self._delete_import_btn)
        lv.addLayout(sel_row)


        lv.addWidget(make_hsep(left_card))

        # \u66f2\u7ebf\u6837\u5f0f\u533a\u57df
        lv.addWidget(make_section_label("曲线样式(选择曲线进行设置)", left_card))

        self._style_target_label = BodyLabel("- 未选择 -", left_card)
        self._style_target_label.setStyleSheet("color: gray; font-size: 11px;")
        self._style_target_label.setWordWrap(True)
        lv.addWidget(self._style_target_label)

        style_row = QHBoxLayout()
        style_row.setSpacing(6)
        style_row.addWidget(BodyLabel("颜色:", left_card))
        self._style_color_btn = PushButton(left_card)
        self._style_color_btn.setFixedSize(28, 28)
        self._style_color_btn.setToolTip("点击选择颜色")
        self._style_color_btn.setEnabled(False)
        self._style_color_btn.clicked.connect(self._on_style_color_click)
        style_row.addWidget(self._style_color_btn)
        self._style_reset_color_btn = ToolButton(FIF.CANCEL, left_card)
        self._style_reset_color_btn.setToolTip("重置为默认颜色")
        self._style_reset_color_btn.setFixedSize(24, 24)
        self._style_reset_color_btn.setEnabled(False)
        self._style_reset_color_btn.clicked.connect(self._on_style_reset_color)
        style_row.addWidget(self._style_reset_color_btn)
        style_row.addWidget(BodyLabel("线型:", left_card))
        self._style_line_combo = ComboBox(left_card)
        self._style_line_combo.addItems(_STYLE_LABELS)
        self._style_line_combo.setEnabled(False)
        self._style_line_combo.currentIndexChanged.connect(self._on_style_line_changed)
        style_row.addWidget(self._style_line_combo, 1)
        lv.addLayout(style_row)

        lv.addWidget(make_hsep(left_card))

        # \u5750\u6807\u8f74\u8bbe\u7f6e
        lv.addWidget(make_section_label("坐标轴", left_card))

        ax_form = QHBoxLayout()
        ax_form.addWidget(BodyLabel("X 范围:", left_card))
        self._x_min_edit = LineEdit(left_card)
        self._x_min_edit.setPlaceholderText("\u81ea\u52a8")
        self._x_min_edit.setFixedWidth(72)
        self._x_min_edit.textChanged.connect(self._redraw)
        ax_form.addWidget(self._x_min_edit)

        self._x_max_edit = LineEdit(left_card)
        self._x_max_edit.setPlaceholderText("\u81ea\u52a8")
        self._x_max_edit.setFixedWidth(72)
        self._x_max_edit.textChanged.connect(self._redraw)
        ax_form.addWidget(self._x_max_edit)
        lv.addLayout(ax_form)

        ay_form = QHBoxLayout()
        ay_form.addWidget(BodyLabel("Y 范围:", left_card))
        self._y_min_edit = LineEdit(left_card)
        self._y_min_edit.setPlaceholderText("\u81ea\u52a8")
        self._y_min_edit.setFixedWidth(72)
        self._y_min_edit.textChanged.connect(self._redraw)
        ay_form.addWidget(self._y_min_edit)

        self._y_max_edit = LineEdit(left_card)
        self._y_max_edit.setPlaceholderText("\u81ea\u52a8")
        self._y_max_edit.setFixedWidth(72)
        self._y_max_edit.textChanged.connect(self._redraw)
        ay_form.addWidget(self._y_max_edit)
        lv.addLayout(ay_form)

        xlabel_row = QHBoxLayout()
        xlabel_row.addWidget(BodyLabel("X 轴标签:", left_card))
        self._x_label_edit = LineEdit(left_card)
        self._x_label_edit.setPlaceholderText("X")
        self._x_label_edit.textChanged.connect(self._redraw)
        xlabel_row.addWidget(self._x_label_edit)
        lv.addLayout(xlabel_row)

        ylabel_row = QHBoxLayout()
        ylabel_row.addWidget(BodyLabel("Y 轴标签:", left_card))
        self._y_label_edit = LineEdit(left_card)
        self._y_label_edit.setPlaceholderText("Y")
        self._y_label_edit.textChanged.connect(self._redraw)
        ylabel_row.addWidget(self._y_label_edit)
        lv.addLayout(ylabel_row)

        lv.addStretch()
        left_card.setMinimumWidth(220)
        left_card.setMaximumWidth(320)
        splitter.addWidget(left_card)

        # \u2500\u2500 \u53f3\u4fa7\u56fe\u8868 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        right_card = CardWidget(self)
        rv = QVBoxLayout(right_card)
        rv.setContentsMargins(8, 8, 8, 8)

        if HAS_MATPLOTLIB:
            self._figure = Figure()
            self._canvas = FigureCanvas(self._figure)
            self._canvas.setMinimumHeight(300)
            rv.addWidget(self._canvas)
        else:
            no_mpl = BodyLabel("\u6ca1\u6709\u5b89\u88c5 matplotlib\uff0c\u8bf7\u8fd0\u884c\uff1auv pip install matplotlib", self)
            no_mpl.setAlignment(Qt.AlignCenter)
            rv.addWidget(no_mpl)
            self._figure = None
            self._canvas = None

        splitter.addWidget(right_card)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

    # ──────────────────────────── 数据 ──────────────────────────────────

    def _get_project_curves(self) -> List[dict]:
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
        prev_selected = {
            item.data(Qt.UserRole)["name"]
            for item in self._curve_list.selectedItems()
        }
        self._curve_list.clear()

        for c in self._get_project_curves():
            item = QListWidgetItem(c["name"])
            item.setData(Qt.UserRole, c)
            if c["name"] in prev_selected:
                item.setSelected(True)
            self._curve_list.addItem(item)

        for c in self._import_curves:
            item = QListWidgetItem(f"[导入] {c['name']}")
            item.setData(Qt.UserRole, c)
            item.setForeground(QColor("#F0A800") if isDarkTheme() else QColor("#1a7a00"))
            if c["name"] in prev_selected:
                item.setSelected(True)
            self._curve_list.addItem(item)

        self._redraw()

    def _selected_curves(self) -> List[dict]:
        return [item.data(Qt.UserRole) for item in self._curve_list.selectedItems()]

    def _get_curve_style(self, curve: dict) -> dict:
        name = curve["name"]
        override = self._curve_styles.get(name, {})
        color = override.get("color") or curve.get("color") or None
        ls = override.get("linestyle", "-")
        mk = override.get("marker", "")
        return {"color": color, "linestyle": ls, "marker": mk}

    # ──────────────────────────── 绘图 ──────────────────────────────────

    def _redraw(self):
        if not HAS_MATPLOTLIB or self._figure is None:
            return
        self._figure.clear()
        ax = self._figure.add_subplot(111)

        dark = isDarkTheme()
        bg = "#1e1e1e" if dark else "#ffffff"
        fg = "#cccccc" if dark else "#222222"
        grid_c = "#444444" if dark else "#dddddd"

        self._figure.patch.set_facecolor(bg)
        ax.set_facecolor(bg)
        ax.tick_params(colors=fg, labelcolor=fg)
        ax.xaxis.label.set_color(fg)
        ax.yaxis.label.set_color(fg)
        ax.title.set_color(fg)
        for spine in ax.spines.values():
            spine.set_edgecolor(fg)
        ax.grid(True, color=grid_c, linestyle="--", linewidth=0.5, alpha=0.7)

        show_scatter = False
        show_line    = True

        for c in self._selected_curves():
            style = self._get_curve_style(c)
            ls = style["linestyle"] or "none"
            marker = style["marker"] or ""
            kw = {"label": c["name"], "linestyle": ls}
            if marker:
                kw["marker"] = marker
                kw["markersize"] = 5
            if style["color"]:
                kw["color"] = style["color"]
            ax.plot(c["x"], c["y"], linewidth=1.4, **kw)

        if self._selected_curves():
            ax.legend(facecolor=bg, edgecolor=fg, labelcolor=fg, fontsize=8)

        x_label = self._x_label_edit.text().strip() if hasattr(self, '_x_label_edit') else ""
        y_label = self._y_label_edit.text().strip() if hasattr(self, '_y_label_edit') else ""
        ax.set_xlabel(x_label or "X")
        ax.set_ylabel(y_label or "Y")
        ax.set_title("")

        def _parse(edit):
            try:
                return float(edit.text().strip())
            except Exception:
                return None

        if hasattr(self, '_x_min_edit') and hasattr(self, '_x_max_edit'):
            x_min = _parse(self._x_min_edit)
            x_max = _parse(self._x_max_edit)
            if x_min is not None and x_max is not None and x_min < x_max:
                ax.set_xlim(x_min, x_max)
            elif x_min is not None and x_max is None:
                ax.set_xlim(left=x_min)
            elif x_min is None and x_max is not None:
                ax.set_xlim(right=x_max)

        if hasattr(self, '_y_min_edit') and hasattr(self, '_y_max_edit'):
            y_min = _parse(self._y_min_edit)
            y_max = _parse(self._y_max_edit)
            if y_min is not None and y_max is not None and y_min < y_max:
                ax.set_ylim(y_min, y_max)
            elif y_min is not None and y_max is None:
                ax.set_ylim(bottom=y_min)
            elif y_min is None and y_max is not None:
                ax.set_ylim(top=y_max)

        self._figure.subplots_adjust(left=0.12, right=0.96, top=0.96, bottom=0.10)
        self._canvas.draw()

    # ──────────────────────────── 样式面板 ──────────────────────────────

    def _set_style_panel_enabled(self, enabled: bool, curve: Optional[dict] = None):
        self._style_color_btn.setEnabled(enabled)
        self._style_reset_color_btn.setEnabled(enabled)
        self._style_line_combo.setEnabled(enabled)
        is_import = enabled and curve is not None and curve.get("source") == "import"
        self._delete_import_btn.setEnabled(is_import)
        if enabled and curve:
            name = curve["name"]
            self._style_target = name
            self._style_target_label.setText(name[:30] + ("…" if len(name) > 30 else ""))
            ov = self._curve_styles.get(name, {})
            eff_color = ov.get("color") or curve.get("color") or "#888888"
            self._update_color_btn(eff_color)
            ls = ov.get("linestyle", "-")
            mk = ov.get("marker", "")
            try:
                idx = next(i for i, (sl, sm) in enumerate(zip(_STYLE_LINESTYLES, _STYLE_MARKERS)) if sl == ls and sm == mk)
            except StopIteration:
                idx = 0
            self._style_line_combo.blockSignals(True)
            self._style_line_combo.setCurrentIndex(idx)
            self._style_line_combo.blockSignals(False)
        else:
            self._style_target = None
            self._style_target_label.setText("— 未选中 —")
            self._update_color_btn("#888888")

    def _update_color_btn(self, color_str: str):
        c = QColor(color_str)
        if not c.isValid():
            color_str = "#888888"
        self._style_color_btn.setStyleSheet(
            f"QPushButton{{background:{color_str};border:1px solid #888;border-radius:4px;}}"
            f"QPushButton:hover{{border:2px solid #aaa;}}"
        )

    def _on_current_item_changed(self, current, previous):
        if current is None:
            self._set_style_panel_enabled(False)
        else:
            self._set_style_panel_enabled(True, current.data(Qt.UserRole))

    def _on_style_color_click(self):
        if not self._style_target:
            return
        curve = self._find_curve_by_name(self._style_target)
        cur_hex = self._curve_styles.get(self._style_target, {}).get("color") \
                  or (curve.get("color") if curve else None) or "#0078D4"
        color = QColorDialog.getColor(QColor(cur_hex), self, "选择曲线颜色")
        if color.isValid():
            self._curve_styles.setdefault(self._style_target, {})["color"] = color.name()
            self._update_color_btn(color.name())
            self._redraw()

    def _on_style_reset_color(self):
        if not self._style_target:
            return
        self._curve_styles.get(self._style_target, {}).pop("color", None)
        curve = self._find_curve_by_name(self._style_target)
        self._update_color_btn((curve.get("color") if curve else None) or "#888888")
        self._redraw()

    def _on_style_line_changed(self, idx: int):
        if not self._style_target:
            return
        styles = self._curve_styles.setdefault(self._style_target, {})
        styles["linestyle"] = _STYLE_LINESTYLES[idx]
        styles["marker"] = _STYLE_MARKERS[idx]
        self._redraw()

    def _on_delete_import_curve(self):
        """删除当前选中的导入曲线"""
        if not self._style_target:
            return
        self._import_curves = [c for c in self._import_curves if c["name"] != self._style_target]
        self._curve_styles.pop(self._style_target, None)
        self._style_target = None
        self._refresh()

    def _find_curve_by_name(self, name: str) -> Optional[dict]:
        for i in range(self._curve_list.count()):
            c = self._curve_list.item(i).data(Qt.UserRole)
            if c and c["name"] == name:
                return c
        return None

    # ──────────────────────────── 列表事件 ──────────────────────────────

    def _select_all(self):
        self._curve_list.selectAll()

    def _on_selection_changed(self):
        self._redraw()

    # ──────────────────────────── 文件操作 ──────────────────────────────

    def _on_import(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入对比数据", "",
            "数据文件 (*.csv *.txt *.dat *.tsv *.json *.npy);;"
            "CSV (*.csv);;文本 (*.txt *.dat *.tsv);;JSON (*.json);;NumPy (*.npy)",
        )
        if not file_path:
            return
        try:
            curves = _load_data_file(file_path)
            if not curves:
                raise ValueError("文件中未找到有效数值数据")
            self._import_curves.extend(curves)
            self._refresh()
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.success(
                title="导入成功", content=f"共导入 {len(curves)} 条曲线",
                position=InfoBarPosition.TOP, duration=2500, parent=self,
            )
        except Exception as e:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.error(
                title="导入失败", content=str(e),
                position=InfoBarPosition.TOP, duration=4000, parent=self,
            )

    def _on_clear_import(self):
        removed = {c["name"] for c in self._import_curves}
        self._import_curves.clear()
        for k in list(self._curve_styles):
            if k in removed:
                del self._curve_styles[k]
        self._refresh()

    def _on_export_image(self):
        if not HAS_MATPLOTLIB or self._figure is None:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出图片", "chart.png", "PNG (*.png);;SVG (*.svg);;PDF (*.pdf)",
        )
        if file_path:
            self._figure.savefig(file_path, dpi=150, bbox_inches="tight")
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.success(
                title="导出成功", content=file_path,
                position=InfoBarPosition.TOP, duration=3000, parent=self,
            )


# ─────────────────────── 数据加载工具函数 ────────────────────────

def _load_data_file(file_path: str) -> List[dict]:
    """
    支持: CSV, TXT, DAT, TSV（多列自动分离）, JSON, NumPy .npy
    多列文件: 第1列为 X，其余每列为独立 Y 曲线，自动命名 name_Y2/Y3/...
    """
    p = Path(file_path)
    name = p.stem
    suffix = p.suffix.lower()
    if suffix == ".npy":
        return _load_npy(p, name)
    if suffix == ".json":
        return _load_json(p, name)
    return _load_tabular(p, name)


def _load_npy(p: Path, name: str) -> List[dict]:
    arr = np.load(str(p))
    if arr.ndim == 1:
        return [{"name": name, "x": list(range(len(arr))), "y": arr.tolist(), "source": "import"}]
    if arr.ndim == 2:
        return _cols_to_curves(arr, name)
    raise ValueError("NumPy 数组维度应为 1 或 2")


def _load_json(p: Path, name: str) -> List[dict]:
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        if data and isinstance(data[0], (list, tuple)):
            arr = np.array(data, dtype=float)
            return _cols_to_curves(arr, name)
        if data and isinstance(data[0], dict):
            curves = []
            for i, item in enumerate(data):
                y = item.get("y", item.get("Y", []))
                x = item.get("x", item.get("X", list(range(len(y)))))
                n = item.get("name", f"{name}_{i + 1}")
                curves.append({"name": n, "x": list(map(float, x)), "y": list(map(float, y)), "source": "import"})
            return curves
    if isinstance(data, dict):
        y = data.get("y", data.get("Y", []))
        x = data.get("x", data.get("X", list(range(len(y)))))
        n = data.get("name", name)
        return [{"name": n, "x": list(map(float, x)), "y": list(map(float, y)), "source": "import"}]
    raise ValueError("无法识别的 JSON 结构")


def _load_tabular(p: Path, name: str) -> List[dict]:
    """通用分隔符文本文件解析（自动检测分隔符、标题行、注释行）"""
    raw_lines: List[str] = []
    for enc in ("utf-8-sig", "utf-8", "gbk", "latin-1"):
        try:
            with open(p, encoding=enc, newline="") as f:
                raw_lines = f.readlines()
            break
        except UnicodeDecodeError:
            continue

    if not raw_lines:
        raise ValueError("文件读取失败或为空")

    data_lines = [l.rstrip("\r\n") for l in raw_lines
                  if l.strip() and not l.lstrip().startswith(("#", "%", "!", "/"))]
    if not data_lines:
        raise ValueError("文件中无有效数据行")

    delimiter = _detect_delimiter(data_lines)

    col_names: Optional[List[str]] = None
    start_row = 0
    first_parts = _split_line(data_lines[0], delimiter)
    if not _all_numeric(first_parts) and len(first_parts) >= 2:
        col_names = [pp.strip().strip('"\'') for pp in first_parts]
        start_row = 1

    rows: List[List[float]] = []
    for line in data_lines[start_row:]:
        parts = _split_line(line, delimiter)
        try:
            row = [float(v) for v in parts if v.strip()]
            if row:
                rows.append(row)
        except ValueError:
            continue

    if not rows:
        raise ValueError("文件中未找到数值数据")

    col_counts = [len(r) for r in rows]
    most_common_ncols = max(set(col_counts), key=col_counts.count)
    rows = [r for r in rows if len(r) == most_common_ncols]
    arr = np.array(rows, dtype=float)

    if col_names and len(col_names) != most_common_ncols:
        col_names = None

    return _cols_to_curves(arr, name, col_names=col_names)


def _cols_to_curves(arr: np.ndarray, name: str, col_names: Optional[List[str]] = None) -> List[dict]:
    if arr.ndim == 1:
        return [{"name": name, "x": list(range(len(arr))), "y": arr.tolist(), "source": "import"}]
    n_cols = arr.shape[1]
    if n_cols < 2:
        return [{"name": name, "x": list(range(len(arr))), "y": arr[:, 0].tolist(), "source": "import"}]
    x = arr[:, 0].tolist()
    curves = []
    for i in range(1, n_cols):
        if col_names and len(col_names) > i:
            y_label = col_names[i]
            c_name = f"{name} / {y_label}"
        else:
            c_name = name if n_cols == 2 else f"{name}_Y{i}"
        curves.append({"name": c_name, "x": x, "y": arr[:, i].tolist(), "source": "import"})
    return curves


def _detect_delimiter(lines: List[str]) -> Optional[str]:
    sample = "\n".join(lines[:10])
    if "\t" in sample:
        return "\t"
    comma_count = sample.count(",")
    semi_count = sample.count(";")
    if comma_count > 0 or semi_count > 0:
        return "," if comma_count >= semi_count else ";"
    return None


def _split_line(line: str, delimiter: Optional[str]) -> List[str]:
    if delimiter is None:
        return re.split(r"\s+", line.strip())
    return line.split(delimiter)


def _all_numeric(parts: List[str]) -> bool:
    for pp in parts:
        try:
            float(pp.strip())
        except (ValueError, AttributeError):
            return False
    return bool(parts)
