# 模型训练指南

本指南将帮助你训练自己的舌象分析模型。

## 📋 目录

1. [数据集准备](#数据集准备)
2. [训练ResNet分类模型](#训练resnet分类模型)
3. [训练YOLOv5检测模型](#训练yolov5检测模型-可选)
4. [模型部署](#模型部署)

---

## 📁 数据集准备

### ResNet分类模型数据集格式

ResNet模型用于4个分类任务，每个任务需要单独准备数据集。

#### 数据集目录结构

```
data/
├── tongue_color/          # 舌色分类（5类）
│   ├── train/
│   │   ├── class0/        # 淡红舌
│   │   ├── class1/        # 红舌
│   │   ├── class2/        # 绛舌
│   │   ├── class3/        # 淡白舌
│   │   └── class4/        # 青紫舌
│   └── val/
│       ├── class0/
│       ├── class1/
│       ├── class2/
│       ├── class3/
│       └── class4/
│
├── tongue_coat_color/     # 苔色分类（3类）
│   ├── train/
│   │   ├── class0/        # 白苔
│   │   ├── class1/        # 黄苔
│   │   └── class2/        # 灰黑苔
│   └── val/
│       ├── class0/
│       ├── class1/
│       └── class2/
│
├── thickness/             # 厚度分类（2类）
│   ├── train/
│   │   ├── class0/        # 薄
│   │   └── class1/        # 厚
│   └── val/
│       ├── class0/
│       └── class1/
│
└── rot_and_greasy/        # 腐腻分类（2类）
    ├── train/
    │   ├── class0/        # 正常
    │   └── class1/        # 腐腻
    └── val/
        ├── class0/
        └── class1/
```

#### 数据要求

- **图像格式**: JPG, PNG, JPEG
- **图像大小**: 建议至少 224x224 像素（训练时会自动调整）
- **数据划分**: 建议训练集:验证集 = 8:2 或 7:3
- **数据平衡**: 尽量保证各类别样本数量相对均衡

#### 数据标注建议

1. **舌色 (tongue_color)**: 
   - class0: 淡红舌（正常）
   - class1: 红舌（热证）
   - class2: 绛舌（热盛）
   - class3: 淡白舌（虚寒）
   - class4: 青紫舌（血瘀）

2. **苔色 (tongue_coat_color)**:
   - class0: 白苔（正常/寒证）
   - class1: 黄苔（热证）
   - class2: 灰黑苔（热极/寒极）

3. **厚度 (thickness)**:
   - class0: 薄
   - class1: 厚

4. **腐腻 (rot_and_greasy)**:
   - class0: 正常
   - class1: 腐腻

---

## 🚀 训练ResNet分类模型

### 快速开始

```bash
# 训练舌色分类模型
python train_resnet.py \
    --task tongue_color \
    --data_path ./data \
    --epochs 50 \
    --batch_size 32 \
    --lr 0.001

# 训练苔色分类模型
python train_resnet.py \
    --task tongue_coat_color \
    --data_path ./data \
    --epochs 50 \
    --batch_size 32

# 训练厚度分类模型
python train_resnet.py \
    --task thickness \
    --data_path ./data \
    --epochs 50 \
    --batch_size 32

# 训练腐腻分类模型
python train_resnet.py \
    --task rot_and_greasy \
    --data_path ./data \
    --epochs 50 \
    --batch_size 32
```

### 训练参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--task` | 任务名称（必需） | - |
| `--data_path` | 数据集根目录（必需） | - |
| `--epochs` | 训练轮数 | 50 |
| `--batch_size` | 批次大小 | 32 |
| `--lr` | 学习率 | 0.001 |
| `--weight_decay` | 权重衰减 | 1e-4 |
| `--num_workers` | 数据加载线程数 | 4 |
| `--save_dir` | 模型保存目录 | ./checkpoints |
| `--resume` | 恢复训练的检查点路径 | None |
| `--device` | 设备 (auto/cpu/cuda) | auto |

### 训练示例

```bash
# 使用GPU训练，自定义参数
python train_resnet.py \
    --task tongue_color \
    --data_path ./data \
    --epochs 100 \
    --batch_size 64 \
    --lr 0.0001 \
    --device cuda \
    --save_dir ./models

# 从检查点恢复训练
python train_resnet.py \
    --task tongue_color \
    --data_path ./data \
    --epochs 100 \
    --resume ./checkpoints/tongue_color_epoch_50.pth
```

### 训练输出

训练过程中会显示：
- 每个epoch的训练损失和准确率
- 验证损失和准确率
- 学习率变化
- 最佳模型会自动保存到 `{save_dir}/{task}_best.pth`

### 模型部署

训练完成后，将最佳模型复制到项目权重目录：

```bash
# 复制训练好的模型权重
cp ./checkpoints/tongue_color_best.pth application/net/weights/tongue_color.pth
cp ./checkpoints/tongue_coat_color_best.pth application/net/weights/tongue_coat_color.pth
cp ./checkpoints/thickness_best.pth application/net/weights/thickness.pth
cp ./checkpoints/rot_and_greasy_best.pth application/net/weights/rot_and_greasy.pth
```

---

## 🎯 训练YOLOv5检测模型

如果你需要训练自己的YOLOv5模型来检测舌头位置，可以使用提供的训练脚本。

### 数据集准备

详细的数据标注指南请查看 `DATA_ANNOTATION_GUIDE.md`

**快速准备**:
1. 使用LabelImg标注舌头位置
2. 按照YOLO格式组织数据
3. 创建数据集配置文件

### 数据集格式

YOLOv5使用YOLO格式标注：

```
yolo_data/
├── images/
│   ├── train/          # 训练图像
│   └── val/            # 验证图像
└── labels/
    ├── train/          # 训练标注（.txt文件）
    └── val/            # 验证标注
```

### 训练命令

```bash
# 使用训练脚本（推荐）
python train_yolov5.py \
    --data data/tongue.yaml \
    --epochs 100 \
    --batch 16

# 或直接使用yolov5命令
yolov5 train \
    --data data/tongue.yaml \
    --weights yolov5s.pt \
    --epochs 100 \
    --img 640 \
    --batch 16
```

### 数据集配置文件

复制示例文件并修改：

```bash
copy data\tongue.yaml.example data\tongue.yaml
```

编辑 `data/tongue.yaml`:
```yaml
path: ./yolo_data
train: images/train
val: images/val
nc: 1  # 类别数（只有舌头一个类别）
names: ['tongue']
```

### 训练参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--data` | 数据集配置文件（必需） | - |
| `--weights` | 预训练权重 | yolov5s.pt |
| `--epochs` | 训练轮数 | 100 |
| `--batch` | 批次大小 | 16 |
| `--img` | 图像尺寸 | 640 |
| `--device` | 设备 | 自动检测 |

### 模型部署

训练完成后，将最佳模型复制到项目：

```bash
copy runs\train\tongue_detection\weights\best.pt application\net\weights\yolov5.pt
```

---

## 💡 训练技巧

### 1. 数据增强

训练脚本已包含数据增强：
- 随机裁剪
- 随机水平翻转
- 颜色抖动
- 随机旋转

### 2. 学习率调整

- 初始学习率建议：0.001
- 如果验证损失不下降，可以降低到 0.0001
- 使用学习率衰减策略（已内置）

### 3. 批次大小

- GPU内存充足：32-64
- GPU内存有限：16-32
- 仅CPU：8-16

### 4. 训练轮数

- 小数据集（<1000张）：50-100轮
- 中等数据集（1000-5000张）：50-80轮
- 大数据集（>5000张）：30-50轮

### 5. 过拟合处理

- 增加数据增强
- 增加权重衰减（weight_decay）
- 使用Dropout（需要修改模型）
- 早停（Early Stopping）

---

## 🔍 常见问题

### Q1: 训练时内存不足怎么办？

**A**: 减小批次大小（batch_size）或图像尺寸。

### Q2: 验证准确率不提升？

**A**: 
- 检查数据集质量和标注准确性
- 尝试降低学习率
- 增加训练轮数
- 检查数据是否平衡

### Q3: 如何评估模型性能？

**A**: 训练脚本会在验证集上自动评估。你也可以单独编写评估脚本。

### Q4: 可以使用预训练权重吗？

**A**: 当前脚本从随机初始化开始训练。如需使用ImageNet预训练权重，需要修改模型加载部分。

---

## 📚 参考资料

- [PyTorch官方文档](https://pytorch.org/docs/stable/index.html)
- [YOLOv5训练教程](https://docs.ultralytics.com/yolov5/tutorials/train_custom_data/)
- [ResNet论文](https://arxiv.org/abs/1512.03385)

---

## 📝 更新日志

- 2024-12-28: 初始版本，支持ResNet50分类模型训练

