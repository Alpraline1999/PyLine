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
