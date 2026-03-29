"""
数据导出模块 - 支持 CSV、Excel、JSON、TXT、剪贴板
"""
from __future__ import annotations

import csv
import json
import os
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.schemas import Curve


class Exporter:
    """曲线数据导出器"""

    @staticmethod
    def _get_rows(curve: "Curve") -> List[List]:
        """获取数据行 [[x_actual, y_actual], ...]"""
        xs = curve.x_actual if curve.x_actual else curve.x_data
        ys = curve.y_actual if curve.y_actual else curve.y_data
        return list(zip(xs, ys))

    @staticmethod
    def _get_header(curve: "Curve") -> List[str]:
        """根据坐标类型生成表头"""
        if curve.calibration and getattr(curve.calibration, "coord_type", "linear") == "polar":
            return ["θ (角度)", "r (极径)"]
        return ["X", "Y"]

    # ==================== CSV ====================

    @staticmethod
    def export_csv(curve: "Curve", file_path: str, timestamp: Optional[str] = None) -> None:
        """导出为 CSV"""
        rows = Exporter._get_rows(curve)
        header = Exporter._get_header(curve)
        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if timestamp:
                writer.writerow([f"# exported: {timestamp}"])
            writer.writerow(["# " + curve.name])
            writer.writerow(header)
            for x, y in rows:
                writer.writerow([x, y])

    @staticmethod
    def export_csv_all(curves: List["Curve"], file_path: str, timestamp: Optional[str] = None) -> None:
        """导出所有曲线到同一 CSV（分组）"""
        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if timestamp:
                writer.writerow([f"# exported: {timestamp}"])
            for curve in curves:
                rows = Exporter._get_rows(curve)
                header = Exporter._get_header(curve)
                writer.writerow(["# " + curve.name])
                writer.writerow(header)
                for x, y in rows:
                    writer.writerow([x, y])
                writer.writerow([])

    # ==================== Excel ====================

    @staticmethod
    def export_excel(curve: "Curve", file_path: str, timestamp: Optional[str] = None) -> None:
        """导出为 Excel（单曲线单表）"""
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = curve.name[:31]  # Excel 表名限制 31 字符

        header = Exporter._get_header(curve)
        rows = Exporter._get_rows(curve)

        start_row = 1
        if timestamp:
            ws.cell(row=1, column=1, value=f"# exported: {timestamp}")
            start_row = 2

        # 表头样式
        header_fill = PatternFill(start_color="0078D4", end_color="0078D4", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        for col, h in enumerate(header, 1):
            cell = ws.cell(row=start_row, column=col, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
            ws.column_dimensions[cell.column_letter].width = 16

        # 数据行
        for row_idx, (x, y) in enumerate(rows, start_row + 1):
            ws.cell(row=row_idx, column=1, value=round(x, 8))
            ws.cell(row=row_idx, column=2, value=round(y, 8))

        wb.save(file_path)

    @staticmethod
    def export_excel_all(curves: List["Curve"], file_path: str, timestamp: Optional[str] = None) -> None:
        """导出所有曲线到同一 Excel（每条曲线一个表）"""
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment

        wb = openpyxl.Workbook()
        # 删除默认 sheet
        default_ws = wb.active
        wb.remove(default_ws)

        for curve in curves:
            ws = wb.create_sheet(title=curve.name[:31])
            header = Exporter._get_header(curve)
            rows = Exporter._get_rows(curve)

            start_row = 1
            if timestamp:
                ws.cell(row=1, column=1, value=f"# exported: {timestamp}")
                start_row = 2

            header_fill = PatternFill(start_color="0078D4", end_color="0078D4", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            for col, h in enumerate(header, 1):
                cell = ws.cell(row=start_row, column=col, value=h)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")
                ws.column_dimensions[cell.column_letter].width = 16

            for row_idx, (x, y) in enumerate(rows, start_row + 1):
                ws.cell(row=row_idx, column=1, value=round(x, 8))
                ws.cell(row=row_idx, column=2, value=round(y, 8))

        if not wb.worksheets:
            wb.create_sheet("空")
        wb.save(file_path)

    # ==================== JSON ====================

    @staticmethod
    def export_json(curve: "Curve", file_path: str, timestamp: Optional[str] = None) -> None:
        """导出为 JSON"""
        rows = Exporter._get_rows(curve)
        header = Exporter._get_header(curve)
        calib = None
        if curve.calibration:
            calib = curve.calibration.model_dump() if hasattr(curve.calibration, "model_dump") else str(curve.calibration)
        data = {
            "name": curve.name,
            "calibration": calib,
            "columns": header,
            "points": [{"x": x, "y": y} for x, y in rows],
        }
        if timestamp:
            data["exported_at"] = timestamp
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def export_json_all(curves: List["Curve"], file_path: str, timestamp: Optional[str] = None) -> None:
        """导出所有曲线到同一 JSON"""
        all_data = []
        for curve in curves:
            rows = Exporter._get_rows(curve)
            header = Exporter._get_header(curve)
            calib = None
            if curve.calibration:
                calib = curve.calibration.model_dump() if hasattr(curve.calibration, "model_dump") else str(curve.calibration)
            all_data.append({
                "name": curve.name,
                "calibration": calib,
                "columns": header,
                "points": [{"x": x, "y": y} for x, y in rows],
            })
        result = {"curves": all_data}
        if timestamp:
            result["exported_at"] = timestamp
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    # ==================== TXT ====================

    @staticmethod
    def export_txt(curve: "Curve", file_path: str, timestamp: Optional[str] = None) -> None:
        """导出为纯文本（空格分隔）"""
        rows = Exporter._get_rows(curve)
        header = Exporter._get_header(curve)
        with open(file_path, "w", encoding="utf-8") as f:
            if timestamp:
                f.write(f"# exported: {timestamp}\n")
            f.write(f"# {curve.name}\n")
            f.write(f"{header[0]}\t{header[1]}\n")
            for x, y in rows:
                f.write(f"{x}\t{y}\n")

    @staticmethod
    def export_txt_all(curves: List["Curve"], file_path: str, timestamp: Optional[str] = None) -> None:
        """导出所有曲线到同一 TXT"""
        with open(file_path, "w", encoding="utf-8") as f:
            if timestamp:
                f.write(f"# exported: {timestamp}\n")
            for curve in curves:
                rows = Exporter._get_rows(curve)
                header = Exporter._get_header(curve)
                f.write(f"# {curve.name}\n")
                f.write(f"{header[0]}\t{header[1]}\n")
                for x, y in rows:
                    f.write(f"{x}\t{y}\n")
                f.write("\n")

    # ==================== 剪贴板 ====================

    @staticmethod
    def get_clipboard_text(curve: "Curve", timestamp: Optional[str] = None) -> str:
        """生成剪贴板文本（制表符分隔，包含表头）"""
        rows = Exporter._get_rows(curve)
        header = Exporter._get_header(curve)
        lines = []
        if timestamp:
            lines.append(f"# exported: {timestamp}")
        lines.append("\t".join(header))
        for x, y in rows:
            lines.append(f"{x}\t{y}")
        return "\n".join(lines)

    @staticmethod
    def export_to_clipboard(curve: "Curve", timestamp: Optional[str] = None) -> None:
        """将曲线数据复制到系统剪贴板"""
        from PySide6.QtWidgets import QApplication
        text = Exporter.get_clipboard_text(curve, timestamp=timestamp)
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
