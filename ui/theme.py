from qfluentwidgets import isDarkTheme


def text_color():
    """主文字颜色"""
    return "#ffffff" if isDarkTheme() else "#000000"


def secondary_color():
    """次要文字颜色"""
    return "#a0a0a0" if isDarkTheme() else "#808080"


def placeholder_color():
    """占位符颜色"""
    return "#808080" if isDarkTheme() else "#a0a0a0"


def background_color():
    """背景颜色"""
    return "#202020" if isDarkTheme() else "#f5f5f5"


def card_background_color():
    """卡片背景颜色"""
    return "#2d2d2d" if isDarkTheme() else "#ffffff"


def border_color():
    """边框颜色"""
    return "#404040" if isDarkTheme() else "#e0e0e0"


def accent_color():
    """强调色（Fluent 蓝）"""
    return "#0078D4"


def surface_color():
    """浅层面板背景"""
    return "#2a2a2a" if isDarkTheme() else "#fafafa"


def hover_color():
    """悬停高亮颜色"""
    return "#383838" if isDarkTheme() else "#e8f0fe"


# ── 通用 UI 工厂函数（避免各页面重复定义）──────────────────────────────

def make_section_label(text: str, parent=None):
    """创建节标题标签（粗体，11px）"""
    from qfluentwidgets import BodyLabel
    lbl = BodyLabel(text, parent)
    lbl.setStyleSheet(f"color: {text_color()}; font-weight: bold; font-size: 11px;")
    return lbl


def make_hsep(parent=None):
    """创建水平分隔线"""
    from PySide6.QtWidgets import QFrame
    line = QFrame(parent)
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"color: {border_color()};")
    return line


def make_vsep(parent=None):
    """创建垂直分隔线（1px 宽）"""
    from PySide6.QtWidgets import QFrame
    line = QFrame(parent)
    line.setFrameShape(QFrame.Shape.VLine)
    line.setFixedWidth(1)
    line.setStyleSheet(f"color: {border_color()};")
    return line
