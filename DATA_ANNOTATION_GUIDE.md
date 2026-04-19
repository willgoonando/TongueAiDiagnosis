# 数据标注完整指南

本指南将帮助你准备和标注自己的数据集，用于训练舌象分析模型。

## 📋 目录

1. [数据标注工具推荐](#数据标注工具推荐)
2. [YOLOv5检测模型标注](#yolov5检测模型标注)
3. [ResNet分类模型标注](#resnet分类模型标注)
4. [数据格式转换](#数据格式转换)
5. [数据质量检查](#数据质量检查)

---

## 🛠️ 数据标注工具推荐

### 1. **LabelImg** (推荐用于YOLOv5)
- **下载**: https://github.com/tzutalin/labelImg
- **特点**: 免费、开源、支持YOLO格式
- **安装**: 
  ```bash
  pip install labelImg
  labelImg  # 启动
  ```

### 2. **LabelMe** (推荐用于分割和分类)
- **下载**: https://github.com/wkentaro/labelme
- **特点**: 支持多种标注格式
- **安装**:
  ```bash
  pip install labelme
  labelme  # 启动
  ```

### 3. **Roboflow** (在线标注平台)
- **网址**: https://roboflow.com
- **特点**: 在线标注、数据增强、格式转换

### 4. **CVAT** (专业标注工具)
- **网址**: https://cvat.org
- **特点**: 功能强大，适合团队协作

---

## 🎯 YOLOv5检测模型标注

### 标注目标
标注舌头在图像中的位置（边界框）

### 数据集结构

```
yolo_data/
├── images/
│   ├── train/          # 训练图像
│   │   ├── img001.jpg
│   │   ├── img002.jpg
│   │   └── ...
│   └── val/            # 验证图像
│       ├── img101.jpg
│       ├── img102.jpg
│       └── ...
└── labels/
    ├── train/          # 训练标注（与图像同名）
    │   ├── img001.txt
    │   ├── img002.txt
    │   └── ...
    └── val/            # 验证标注
        ├── img101.txt
        ├── img102.txt
        └── ...
```

### 使用LabelImg标注步骤

1. **启动LabelImg**
   ```bash
   labelImg
   ```

2. **设置标注格式**
   - 点击 `View` → 勾选 `Auto Save`
   - 点击 `Change Save Dir` → 选择 `yolo_data/labels/train`
   - 点击 `Open Dir` → 选择 `yolo_data/images/train`
   - 在右侧选择 `YOLO` 格式（不是PascalVOC）

3. **开始标注**
   - 使用 `W` 键创建边界框
   - 选择类别 `tongue`（如果还没有，点击 `Edit` → `Edit Label` 添加）
   - 确保边界框完全包含舌头，不要太大也不要太小
   - 使用 `D` 键切换到下一张图像

4. **标注要点**
   - ✅ 边界框应该紧贴舌头边缘
   - ✅ 包含整个舌头，包括舌尖和舌根
   - ✅ 如果图像中有多个舌头，只标注最清晰的那个
   - ❌ 不要包含太多背景
   - ❌ 不要标注模糊或不完整的舌头

### 标注文件格式

每个图像对应一个 `.txt` 文件，格式如下：

```
class_id center_x center_y width height
```

**示例** (`img001.txt`):
```
0 0.5 0.5 0.3 0.4
```

**说明**:
- `class_id`: 类别ID（0表示舌头）
- `center_x, center_y`: 边界框中心点坐标（归一化，0-1）
- `width, height`: 边界框宽度和高度（归一化，0-1）

**坐标计算**:
```
center_x = (x1 + x2) / 2 / image_width
center_y = (y1 + y2) / 2 / image_height
width = (x2 - x1) / image_width
height = (y2 - y1) / image_height
```

### 创建数据集配置文件

复制示例配置文件并修改：

```bash
copy data\tongue.yaml.example data\tongue.yaml
```

编辑 `data/tongue.yaml`:
```yaml
path: ./yolo_data
train: images/train
val: images/val
nc: 1
names: ['tongue']
```

---

## 🏷️ ResNet分类模型标注

### 标注目标
将已裁剪的舌头图像分类到不同类别

### 数据集结构

```
data/
├── tongue_color/
│   ├── train/
│   │   ├── class0/     # 淡红舌
│   │   ├── class1/     # 红舌
│   │   ├── class2/     # 绛舌
│   │   ├── class3/     # 淡白舌
│   │   └── class4/     # 青紫舌
│   └── val/
│       └── (相同结构)
├── tongue_coat_color/
│   ├── train/
│   │   ├── class0/     # 白苔
│   │   ├── class1/     # 黄苔
│   │   └── class2/     # 灰黑苔
│   └── val/
│       └── (相同结构)
├── thickness/
│   ├── train/
│   │   ├── class0/     # 薄
│   │   └── class1/     # 厚
│   └── val/
│       └── (相同结构)
└── rot_and_greasy/
    ├── train/
    │   ├── class0/     # 正常
    │   └── class1/     # 腐腻
    └── val/
        └── (相同结构)
```

### 标注方法

#### 方法1: 手动分类（推荐）

1. **准备数据**
   - 使用训练好的YOLOv5模型检测并裁剪舌头
   - 或者手动从原图中裁剪舌头区域

2. **分类标注**
   - 根据中医知识判断每个舌头的特征
   - 将图像复制到对应的类别文件夹

3. **使用脚本辅助分类**
   ```python
   # 可以编写脚本批量处理
   # 例如：根据文件名或元数据自动分类
   ```

#### 方法2: 使用标注工具

1. **使用LabelMe**
   - 打开图像
   - 添加分类标签
   - 导出为分类数据集

2. **使用Excel/CSV管理**
   - 创建表格记录每张图像的分类
   - 使用脚本根据表格自动组织文件

### 分类标准参考

#### 舌色 (tongue_color)
- **class0 - 淡红舌**: 淡红色，正常舌色
- **class1 - 红舌**: 红色，主热证
- **class2 - 绛舌**: 深红色，热盛
- **class3 - 淡白舌**: 淡白色，虚寒
- **class4 - 青紫舌**: 青紫色，血瘀

#### 苔色 (tongue_coat_color)
- **class0 - 白苔**: 白色，正常或寒证
- **class1 - 黄苔**: 黄色，热证
- **class2 - 灰黑苔**: 灰黑色，热极或寒极

#### 厚度 (thickness)
- **class0 - 薄**: 舌苔薄，能见舌质
- **class1 - 厚**: 舌苔厚，不能见舌质

#### 腐腻 (rot_and_greasy)
- **class0 - 正常**: 舌苔正常
- **class1 - 腐腻**: 舌苔腐腻

---

## 🔄 数据格式转换

### 从其他格式转换为YOLO格式

如果你使用其他工具标注，可能需要转换格式：

```python
# 示例：从COCO格式转换为YOLO格式
# 可以编写转换脚本
```

### 从检测结果生成分类数据

可以使用训练好的YOLOv5模型自动裁剪舌头，然后手动分类：

```python
# 使用YOLOv5检测并裁剪
# 然后手动分类到不同文件夹
```

---

## ✅ 数据质量检查

### 检查清单

#### YOLOv5数据检查
- [ ] 每个图像都有对应的标注文件
- [ ] 标注文件格式正确（YOLO格式）
- [ ] 坐标值在0-1范围内
- [ ] 边界框不超出图像范围
- [ ] 训练集和验证集比例合理（建议8:2）

#### ResNet数据检查
- [ ] 每个任务都有train和val目录
- [ ] 每个类别文件夹中都有图像
- [ ] 图像格式正确（JPG/PNG）
- [ ] 类别数量正确
- [ ] 数据分布相对均衡

### 使用脚本检查

```bash
# 检查YOLOv5数据集
python check_yolo_dataset.py --data data/tongue.yaml

# 检查ResNet数据集
python check_resnet_dataset.py --data_path ./data
```

---

## 📊 数据量建议

### 最小数据量
- **YOLOv5**: 至少200-300张标注图像
- **ResNet每个任务**: 每个类别至少50-100张图像

### 推荐数据量
- **YOLOv5**: 500-1000张标注图像
- **ResNet每个任务**: 每个类别200-500张图像

### 数据分布
- 尽量保证各类别样本数量相对均衡
- 如果数据不平衡，可以使用数据增强或加权损失

---

## 💡 标注技巧

1. **一致性**: 保持标注标准一致
2. **质量优先**: 宁可少标注，也要保证质量
3. **多样性**: 包含不同角度、光照、背景的图像
4. **验证**: 定期检查标注质量
5. **迭代**: 根据模型表现调整标注策略

---

## 🚀 下一步

完成数据标注后：

1. **训练YOLOv5模型**:
   ```bash
   python train_yolov5.py --data data/tongue.yaml --epochs 100
   ```

2. **训练ResNet模型**:
   ```bash
   python train_resnet.py --task tongue_color --data_path ./data
   ```

3. **部署模型**: 将训练好的模型复制到 `application/net/weights/`

---

## 📚 参考资料

- [LabelImg使用教程](https://github.com/tzutalin/labelImg)
- [YOLOv5训练教程](https://docs.ultralytics.com/yolov5/tutorials/train_custom_data/)
- [中医舌诊标准](参考相关中医文献)








