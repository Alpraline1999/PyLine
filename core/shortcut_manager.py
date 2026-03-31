"""快捷键管理器 - 管理全局键盘快捷键的默认值和用户自定义"""
import json
from pathlib import Path
from PySide6.QtCore import QObject, Signal


class ShortcutManager(QObject):
    """单例快捷键管理器，支持加载/保存用户自定义快捷键"""

    shortcuts_changed = Signal()  # 快捷键修改后发出

    DEFAULTS: dict[str, str] = {
        "undo":          "Ctrl+Z",
        "redo":          "Ctrl+Y",
        "save":          "Ctrl+S",
        "new_project":   "Ctrl+N",
        "open_project":  "Ctrl+O",
        "close_project": "Ctrl+W",
        "add_image":     "Ctrl+I",
        "add_curve":     "Ctrl+Shift+N",
        "extract":       "Q",
        "calibrate":     "C",
        "eraser":        "E",
        "auto_detect":   "A",
        "apply_auto":    "Ctrl+Return",
        "clear_points":  "Ctrl+Delete",
        "clear_masks":   "Ctrl+Shift+Delete",
        "escape_tool":   "Escape",
        "zoom_in":       "Ctrl+=",
        "zoom_out":      "Ctrl+-",
        "zoom_fit":      "Ctrl+0",
        "delete_rows":   "Delete",
    }

    LABELS: dict[str, str] = {
        "undo":          "撤销",
        "redo":          "重做",
        "save":          "保存项目",
        "new_project":   "新建项目",
        "open_project":  "打开项目",
        "close_project": "关闭项目",
        "add_image":     "添加图片",
        "add_curve":     "添加曲线",
        "extract":       "手动提取模式",
        "calibrate":     "校准模式",
        "eraser":        "橡皮擦模式",
        "auto_detect":   "自动检测",
        "apply_auto":    "应用检测结果",
        "clear_points":  "清除所有点",
        "clear_masks":   "清除蒙版",
        "escape_tool":   "取消当前工具",
        "zoom_in":       "放大",
        "zoom_out":      "缩小",
        "zoom_fit":      "适合窗口",
        "delete_rows":   "删除数据行",
    }

    _CONFIG_FILE = Path.home() / ".config" / "pyline" / "shortcuts.json"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shortcuts: dict[str, str] = dict(self.DEFAULTS)
        self._load()

    def _load(self):
        try:
            if self._CONFIG_FILE.exists():
                with open(self._CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for k, v in data.items():
                    if k in self._shortcuts:
                        self._shortcuts[k] = v
        except Exception:
            pass

    def save(self):
        try:
            self._CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self._CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._shortcuts, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get(self, action: str) -> str:
        return self._shortcuts.get(action, self.DEFAULTS.get(action, ""))

    def set(self, action: str, key_sequence: str):
        self._shortcuts[action] = key_sequence

    def reset_to_defaults(self):
        self._shortcuts = dict(self.DEFAULTS)
        self.save()
        self.shortcuts_changed.emit()

    def apply_all(self, mapping: dict[str, str]):
        """批量更新快捷键并保存"""
        for k, v in mapping.items():
            if k in self._shortcuts:
                self._shortcuts[k] = v
        self.save()
        self.shortcuts_changed.emit()


# 全局单例
shortcut_manager = ShortcutManager()
