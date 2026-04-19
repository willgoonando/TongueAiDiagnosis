# 🔧 LabelImg 画框错误修复说明

## ❌ 问题描述

在 labelImg 中点击画框时出现错误并闪退：

```
TypeError: arguments did not match any overloaded call:
  drawLine(self, x1: int, y1: int, x2: int, y2: int): argument 1 has unexpected type 'float'
```

## 🔍 问题原因

这是 labelImg 1.8.6 与 PyQt5 5.15.x 的兼容性问题：

- `QPointF.x()` 和 `QPointF.y()` 返回 `float` 类型
- `drawLine()` 和 `drawRect()` 需要 `int` 类型参数
- PyQt5 5.15.x 对类型检查更严格

## ✅ 修复方案

已直接修复 labelImg 源代码：

**文件位置**: `D:\Anaconda\envs\AiDiagnosis-3.12\Lib\site-packages\libs\canvas.py`

### 修复内容

1. **第 530-531 行** - `drawLine` 调用：
   ```python
   # 修复前：
   p.drawLine(self.prev_point.x(), 0, self.prev_point.x(), self.pixmap.height())
   p.drawLine(0, self.prev_point.y(), self.pixmap.width(), self.prev_point.y())
   
   # 修复后：
   p.drawLine(int(self.prev_point.x()), 0, int(self.prev_point.x()), int(self.pixmap.height()))
   p.drawLine(0, int(self.prev_point.y()), int(self.pixmap.width()), int(self.pixmap.height()))
   ```

2. **第 526 行** - `drawRect` 调用：
   ```python
   # 修复前：
   p.drawRect(left_top.x(), left_top.y(), rect_width, rect_height)
   
   # 修复后：
   p.drawRect(int(left_top.x()), int(left_top.y()), int(rect_width), int(rect_height))
   ```

## 🧪 测试修复

修复后，重新启动 labelImg：

```bash
conda activate AiDiagnosis-3.12
labelimg
```

然后：
1. 打开 `images/train` 目录
2. 设置保存目录为 `images/Labels/train`
3. 选择 YOLO 格式
4. 按 `W` 键画框

应该不会再出现错误。

## 📝 注意事项

- 此修复直接修改了 labelImg 的源代码
- 如果重新安装 labelImg，可能需要重新应用此修复
- 建议备份修复后的文件

## ✅ 最新修复（2024-12-28）

### 修复 2：滚动条 setValue 错误

**错误信息**:
```
TypeError: setValue(self, a0: int): argument 1 has unexpected type 'float'
```

**修复位置**: `labelImg.py` 第 965 行和第 1025-1026 行

**修复内容**:
```python
# 修复前（第 965 行）：
bar.setValue(bar.value() + bar.singleStep() * units)

# 修复后：
bar.setValue(int(bar.value() + bar.singleStep() * units))

# 修复前（第 1025-1026 行）：
h_bar.setValue(new_h_bar_value)
v_bar.setValue(new_v_bar_value)

# 修复后：
h_bar.setValue(int(new_h_bar_value))
v_bar.setValue(int(new_v_bar_value))
```

### 修复 3：标签文本绘制 drawText 错误

**错误信息**:
```
TypeError: arguments did not match any overloaded call:
  drawText(self, x: int, y: int, s: Optional[str]): argument 1 has unexpected type 'float'
```

**修复位置**: `shape.py` 第 131 行

**修复内容**:
```python
# 修复前：
painter.drawText(min_x, min_y, self.label)

# 修复后：
painter.drawText(int(min_x), int(min_y), self.label)
```

**说明**: 标注后绘制标签文本时，`min_x` 和 `min_y` 是 float 类型（来自 `point.x()` 和 `point.y()`），但 `drawText` 需要 int 类型。

## 🔄 如果重新安装 labelImg

如果将来需要重新安装 labelImg，可以运行以下脚本自动修复：

```python
# 修复脚本（保存为 fix_labelimg.py）
import os
import re

canvas_path = r"D:\Anaconda\envs\AiDiagnosis-3.12\Lib\site-packages\libs\canvas.py"

with open(canvas_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复 drawLine
content = re.sub(
    r'p\.drawLine\(self\.prev_point\.x\(\), 0, self\.prev_point\.x\(\), self\.pixmap\.height\(\)\)',
    r'p.drawLine(int(self.prev_point.x()), 0, int(self.prev_point.x()), int(self.pixmap.height()))',
    content
)
content = re.sub(
    r'p\.drawLine\(0, self\.prev_point\.y\(\), self\.pixmap\.width\(\), self\.prev_point\.y\(\)\)',
    r'p.drawLine(0, int(self.prev_point.y()), int(self.pixmap.width()), int(self.prev_point.y()))',
    content
)

# 修复 drawRect（如果需要）
content = re.sub(
    r'p\.drawRect\(left_top\.x\(\), left_top\.y\(\), rect_width, rect_height\)',
    r'p.drawRect(int(left_top.x()), int(left_top.y()), int(rect_width), int(rect_height))',
    content
)

with open(canvas_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("修复完成！")
```

