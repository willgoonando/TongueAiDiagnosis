# 🔧 修复 LabelImg 画框错误

## ❌ 错误信息

```
TypeError: arguments did not match any overloaded call:
  drawLine(self, x1: int, y1: int, x2: int, y2: int): argument 1 has unexpected type 'float'
```

## 🔍 问题原因

这是 **labelImg 1.8.6** 与 **PyQt5 5.15.11** 的兼容性问题。

- `prev_point.x()` 返回 `float` 类型
- `drawLine()` 需要 `int` 类型参数
- PyQt5 5.15.11 对类型检查更严格

## ✅ 解决方案

### 方案1: 降级 PyQt5（推荐）

```bash
conda activate AiDiagnosis-3.12
pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5-sip
pip install PyQt5==5.15.10 PyQt5-Qt5==5.15.2 PyQt5-sip==12.13.0
```

### 方案2: 使用 labelImg 的修复版本

如果方案1不行，可以尝试：

```bash
conda activate AiDiagnosis-3.12
pip uninstall -y labelImg
pip install labelImg==1.8.7  # 如果有更新版本
```

### 方案3: 手动修复 labelImg 代码（不推荐）

如果需要手动修复，需要修改 labelImg 的 `canvas.py` 文件：

```python
# 在 D:\Anaconda\envs\AiDiagnosis-3.12\Lib\site-packages\libs\canvas.py 第 530 行
# 将：
p.drawLine(self.prev_point.x(), 0, self.prev_point.x(), self.pixmap.height())

# 改为：
p.drawLine(int(self.prev_point.x()), 0, int(self.prev_point.x()), int(self.pixmap.height()))
```

## 🧪 验证修复

修复后，重新启动 labelImg：

```bash
conda activate AiDiagnosis-3.12
labelimg
```

尝试画框，应该不会再出现错误。

## 📝 注意事项

- 修复后，labelImg 应该可以正常使用
- 如果还有其他错误，可能需要检查其他依赖
- 建议在修复前备份当前环境



