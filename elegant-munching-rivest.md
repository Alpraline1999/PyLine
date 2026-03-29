# PyLine 项目现状分析

## 一、项目概述

PyLine 是一个用于从图片中提取曲线数据的 Python 桌面应用，基于 PySide6 和 qfluentwidgets 开发。

## 二、已完成的功能

### 核心功能
1. **项目管理** - 创建/打开/保存项目（JSON格式）
2. **图片管理** - 添加图片到项目，支持拖放
3. **曲线提取** - 在图片上点击选取曲线点
4. **校准功能** - 4点校准（X轴起点/终点，Y轴起点/终点）
5. **坐标转换** - 像素坐标转实际坐标（线性/对数）
6. **橡皮擦** - 擦除提取错误的点
7. **蒙版** - 框选/画笔蒙版
8. **点形状** - 支持圆形、方形、三角形、菱形、倒三角、叉号、星号、五角星

### UI功能
1. **三面板布局** - 左侧项目树、中间图片查看器、右侧工具面板
2. **工具标签页** - 手动选点、自动选点
3. **公共工具** - 颜色选择器、形状选择器、排序按钮
4. **主题支持** - 浅色/深色/跟随系统（目前隐藏）
5. **右键菜单** - 曲线操作（重命名、删除、隐藏/显示）

## 三、当前存在的问题

### 问题1：校准后对话框未出现
**现象**: 用户期望校准设置完4个点后，再按一次校准按钮弹出对话框输入X/Y范围
**代码位置**: `workspace_page.py` 第562-585行

当前校准流程（按代码）:
1. 按下校准按钮 → 如有现有校准则提示确认清除
2. 调用 `set_calibrate_mode()` 进入校准模式
3. 用户点击4个校准点
4. **问题**: 没有"再次按下校准按钮完成校准"的逻辑

**修复**: 在 `_on_tool_clicked` 中，当 `_active_tool == "calibrate"` 时：
- 如果4个校准点已设置完成，调用 `finish_calibration()` 弹出对话框
- 如果未完成，提示用户继续

### 问题2：排序后曲线点和校准消失
**现象**: 按下X/Y排序按钮后，曲线点和校准线消失
**代码位置**: `workspace_page.py` 第1283-1302行

当前 `_on_sort_by_x` 和 `_on_sort_by_y` 的逻辑:
```python
def _on_sort_by_x(self):
    # 获取排序后的索引并排序
    indices = sorted(...)
    curve.x_data = [curve.x_data[i] for i in indices]
    curve.y_data = [curve.y_data[i] for i in indices]
    # 问题1: 没有保存当前提取的点
    # 问题2: 没有重新应用校准
    self._display_current_curve_on_image()
```

**问题分析**:
1. 提取模式下的点存在 `_current_curve_points`（workspace_page）和 `_current_curve`（image_viewer），未保存到 project_manager
2. `_display_current_curve_on_image()` 中如果有校准数据会调用 `_apply_calibration_to_viewer()`，但排序后 curve.calibration 可能为 None

**修复**:
1. 排序前先调用 `_save_extracted_curve()` 保存当前提取的点
2. 排序后调用 `_apply_calibration_to_viewer(curve.calibration)` 确保校准显示

### 问题3：校准微调逻辑错误
**现象**: 键盘微调校准点时，调整了错误的点
**代码位置**: `image_viewer.py` 第141-152行

```python
def nudge_current_point(self, dx, dy):
    if self.x_start is None:
        pass  # 正确：无操作
    elif self.x_end is None:
        self.x_start = QPointF(...)  # 错误：这里应该调整 x_end！
    elif self.y_start is None:
        self.x_end = QPointF(...)  # 错误：这里应该调整 y_start！
    # ...
```

**修复**: 修正判断逻辑，正确识别当前应该调整哪个点

## 四、待实现功能

1. **极坐标支持** - 扩展坐标类型
2. **数据导出** - 导出为CSV/Excel
3. **多曲线对比** - 在同一坐标系显示多条曲线
4. **图片预处理** - 亮度/对比度调整

## 五、关键文件

| 文件 | 功能 |
|-----|------|
| `ui/pages/workspace_page.py` | 主工作区，1300+行，所有工具逻辑 |
| `ui/widgets/image_viewer.py` | 图片显示和交互，约880行 |
| `ui/dialogs/calibration_dialog.py` | 校准范围对话框 |
| `core/project_manager.py` | 项目管理和坐标转换 |
| `models/schemas.py` | 数据模型（Project, ImageWork, Curve, CalibrationData） |

## 六、修复计划

### 修复1：校准完成逻辑
**文件**: `ui/pages/workspace_page.py`
**位置**: `_on_tool_clicked()` 方法（约第562行）

添加逻辑:
```python
if tool_name == "calibrate":
    # 如果已经在校准模式
    if self._active_tool == "calibrate":
        calib = self._image_viewer.get_calibration()
        if calib.is_complete():
            # 完成校准，弹出对话框
            self._image_viewer.finish_calibration()
        else:
            self._status_label.setText("请先完成所有校准点的设置")
        return
    # ... 现有逻辑继续 ...
```

### 修复2：排序时保留校准和点
**文件**: `ui/pages/workspace_page.py`
**位置**: `_on_sort_by_x()` 和 `_on_sort_by_y()` 方法

修改为:
```python
def _on_sort_by_x(self):
    if self._current_curve_id is None:
        return
    curve = project_manager.get_curve(self._current_curve_id)
    if curve is None:
        return

    # 先保存当前提取的曲线点
    if self._current_curve_points:
        self._save_extracted_curve()

    if not curve.x_data:
        return

    # 保存校准数据
    saved_calibration = curve.calibration

    # 排序
    indices = sorted(range(len(curve.x_data)), key=lambda i: curve.x_data[i])
    curve.x_data = [curve.x_data[i] for i in indices]
    curve.y_data = [curve.y_data[i] for i in indices]
    if curve.x_actual and curve.y_actual:
        curve.x_actual = [curve.x_actual[i] for i in indices]
        curve.y_actual = [curve.y_actual[i] for i in indices]

    # 先应用校准，再显示曲线
    if saved_calibration:
        self._apply_calibration_to_viewer(saved_calibration)
    self._display_current_curve_on_image()
    self._update_curve_table()
    self.project_modified.emit()
```

### 修复3：校准微调修正
**文件**: `ui/widgets/image_viewer.py`
**位置**: `CalibrationOverlay.nudge_current_point()` 方法

修正逻辑，正确判断当前应该调整哪个点。

## 七、验证步骤

1. 运行 `python main.py`
2. 创建项目，添加图片，创建曲线
3. **校准测试**: 选曲线 → 校准按钮 → 选择坐标类型 → 依次点击4个点 → 再次按校准按钮 → 应弹出对话框输入X/Y范围
4. **提取测试**: 选图片/曲线 → 提取按钮 → 点击添加几个点 → 按排序 → 点应保留
5. **校准后排序测试**: 校准完成 → 按排序 → 校准线应保留
6. **微调测试**: 校准过程中按方向键 → 应微调正确的校准点
