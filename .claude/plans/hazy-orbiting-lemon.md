# PyLine 实现计划

## Context

将 PyLine 实现为带有 **Fluent 风格界面** 的桌面应用。

**技术栈**：
- Python + **PySide6** (Qt for Python)
- **qfluentwidgets** 库实现 Fluent 风格界面
- OpenCV 用于图片处理
- Matplotlib/Plotly 用于曲线绘制

**第一优先级**：先制作 Fluent 风格的主窗口框架

## 技术选型

### GUI框架
- **PySide6**: Qt for Python，跨平台
- **qfluentwidgets**: 专门为PySide6设计的Fluent风格组件库

### 核心依赖
```
PySide6
qfluentwidgets
opencv-python
numpy
matplotlib
pydantic
```

## 项目结构

```
PyLine/
├── main.py                    # 入口文件
├── requirements.txt           # 依赖
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # 主窗口（Fluent风格）
│   ├── widgets/                # 自定义组件
│   │   ├── image_viewer.py    # 图片查看器
│   │   ├── curve_panel.py     # 曲线面板
│   │   └── toolbar.py          # 工具栏
│   └── styles/                 # 样式资源
├── core/
│   ├── __init__.py
│   ├── curve_extractor.py      # 曲线提取
│   ├── image_processor.py      # 图片处理
│   └── data_handler.py        # 数据管理
├── models/
│   ├── __init__.py
│   └── schemas.py              # Pydantic 数据模型
└── resources/                  # 图片等资源
```

## 数据模型

```python
class CalibrationData(BaseModel):
    origin: Tuple[float, float]
    x_axis_end: Tuple[float, float]
    y_axis_end: Tuple[float, float]
    x_range: Tuple[float, float]
    y_range: Tuple[float, float]
    coord_type: str = "linear"

class Curve(BaseModel):
    id: str
    name: str
    x_data: List[float]
    y_data: List[float]
    color: str
    source_image_id: Optional[str]

class MaskData(BaseModel):
    include_mode: bool
    polygons: List[List[Tuple[int, int]]]

class ImageWork(BaseModel):
    id: str
    name: str
    image_path: str
    curves: List[Curve]
    mask: Optional[MaskData]
    calibration: Optional[CalibrationData]

class Project(BaseModel):
    id: str
    name: str
    images: List[ImageWork]
    imported_curves: List[Curve]
    created_at: str
    updated_at: str
```

## 实施顺序

### Phase 1: Fluent 界面框架（第一优先）
1. 环境搭建（PySide6 + qfluentwidgets）
2. 主窗口框架（Fluent 风格）
   - 导航侧边栏
   - 标题栏
   - 主题支持（亮/暗）
3. 基础布局（左侧/中间/底部面板）

### Phase 2: 核心功能
4. 项目管理（新建/打开/保存 .pyline JSON）
5. 图片查看器（缩放/平移/放大镜）
6. 蒙版工具（矩形框选/自由涂刷/橡皮擦）
7. 曲线提取（颜色采样 + 蒙版）
8. 坐标轴校准

### Phase 3: 完善功能
9. 曲线对比视图
10. 数据导入/导出
11. 曲线编辑
12. 拖拽/右键菜单/Undo-Redo

## 工具栏设计

| 按钮 | 功能 |
|------|------|
| 🖱️ 选取颜色 | 颜色采样模式 |
| 📦 框选蒙版 | 矩形蒙版工具 |
| 🖌️ 涂刷蒙版 | 自由绘制蒙版 |
| 🧹 橡皮擦 | 擦除蒙版 |
| ↩️ 撤销 / ↪️ 重做 | Undo/Redo |
| 🔍 放大镜 | 局部放大开关 |
| 📐 校准 | 坐标轴校准 |
| 📊 对比视图 | 切换到曲线对比 |

## 验证方案

1. 运行 `python main.py` 启动应用
2. 验证 Fluent 风格主窗口正常显示
3. 测试主题切换（亮/暗）
4. 测试完整曲线提取流程
