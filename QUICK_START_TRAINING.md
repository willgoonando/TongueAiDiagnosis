# 🚀 快速开始：用自己的数据训练模型

本指南将帮助你从零开始，使用自己的标注数据训练所有模型。

## 📋 训练流程概览

```
1. 数据标注
   ├── YOLOv5: 标注舌头位置（边界框）
   └── ResNet: 分类已裁剪的舌头图像

2. 数据准备
   ├── 组织数据格式
   └── 检查数据质量

3. 模型训练
   ├── 训练YOLOv5检测模型
   └── 训练ResNet分类模型（4个任务）

4. 模型部署
   └── 替换预训练模型权重
```

---

## 🎯 第一步：数据标注

### YOLOv5检测模型标注

**目标**: 标注舌头在图像中的位置

1. **安装LabelImg**
   ```bash
   pip install labelImg
   labelImg
   ```

2. **标注步骤**
   - 打开 `yolo_data/images/train` 目录
   - 设置保存路径为 `yolo_data/labels/train`
   - 选择YOLO格式（不是PascalVOC）
   - 使用 `W` 键创建边界框，标注舌头位置
   - 类别选择 `tongue`

3. **数据组织**
   ```
   yolo_data/
   ├── images/
   │   ├── train/    # 放入训练图像
   │   └── val/      # 放入验证图像
   └── labels/
       ├── train/    # LabelImg自动保存标注文件
       └── val/
   ```

**详细说明**: 查看 `DATA_ANNOTATION_GUIDE.md`

### ResNet分类模型标注

**目标**: 将已裁剪的舌头图像分类

1. **准备数据**
   - 使用YOLOv5检测并裁剪舌头
   - 或手动从原图中裁剪舌头区域

2. **分类标注**
   - 根据中医知识判断特征
   - 将图像复制到对应类别文件夹

3. **数据组织**
   ```bash
   # 自动创建目录结构
   python setup_dataset_structure.py --path ./data
   ```
   
   然后手动将图像分类到对应文件夹：
   ```
   data/
   ├── tongue_color/train/class0/     # 淡红舌
   ├── tongue_color/train/class1/     # 红舌
   ├── tongue_coat_color/train/class0/ # 白苔
   └── ...
   ```

---

## ✅ 第二步：数据检查

训练前先检查数据格式是否正确：

```bash
# 检查YOLOv5数据集
python check_dataset.py --yolo_data data/tongue.yaml

# 检查ResNet数据集
python check_dataset.py --resnet_data ./data
```

---

## 🏋️ 第三步：模型训练

### 训练YOLOv5检测模型

1. **创建配置文件**
   ```bash
   copy data\tongue.yaml.example data\tongue.yaml
   ```
   编辑 `data/tongue.yaml`，修改数据集路径

2. **开始训练**
   ```bash
   python train_yolov5.py --data data/tongue.yaml --epochs 100 --batch 16
   ```

3. **训练输出**
   - 最佳模型: `runs/train/tongue_detection/weights/best.pt`
   - 训练日志和图表在 `runs/train/tongue_detection/`

### 训练ResNet分类模型

**单个模型训练**:
```bash
# 训练舌色分类
python train_resnet.py --task tongue_color --data_path ./data --epochs 50

# 训练苔色分类
python train_resnet.py --task tongue_coat_color --data_path ./data --epochs 50

# 训练厚度分类
python train_resnet.py --task thickness --data_path ./data --epochs 50

# 训练腐腻分类
python train_resnet.py --task rot_and_greasy --data_path ./data --epochs 50
```

**批量训练所有模型**:
```bash
# Windows
train_all.bat

# Linux/Mac
bash train_all.sh
```

**训练输出**:
- 最佳模型保存在 `./checkpoints/{task}_best.pth`
- 每10个epoch保存一次检查点

---

## 📦 第四步：模型部署

训练完成后，将模型复制到项目权重目录：

### 部署YOLOv5模型
```bash
copy runs\train\tongue_detection\weights\best.pt application\net\weights\yolov5.pt
```

### 部署ResNet模型
```bash
copy .\checkpoints\tongue_color_best.pth application\net\weights\tongue_color.pth
copy .\checkpoints\tongue_coat_color_best.pth application\net\weights\tongue_coat_color.pth
copy .\checkpoints\thickness_best.pth application\net\weights\thickness.pth
copy .\checkpoints\rot_and_greasy_best.pth application\net\weights\rot_and_greasy.pth
```

---

## 📊 训练参数建议

### YOLOv5
- **批次大小**: 16-32（根据GPU内存）
- **图像尺寸**: 640（标准）
- **训练轮数**: 100-200（根据数据量）
- **预训练权重**: yolov5s.pt（推荐）

### ResNet
- **批次大小**: 32（GPU）或 16（CPU）
- **学习率**: 0.001（可调整）
- **训练轮数**: 50-100（根据数据量）

---

## 💡 常见问题

### Q1: 需要多少数据？

**A**: 
- YOLOv5: 至少200-300张，推荐500-1000张
- ResNet每个任务: 每个类别至少50-100张，推荐200-500张

### Q2: 训练时间多长？

**A**: 
- YOLOv5: 取决于数据量和GPU，通常几小时到一天
- ResNet: 每个任务通常1-3小时（GPU）

### Q3: 可以用CPU训练吗？

**A**: 可以，但速度很慢。强烈建议使用GPU。

### Q4: 如何判断模型训练好了？

**A**: 
- 验证准确率不再提升
- 训练损失和验证损失都收敛
- 在测试集上表现良好

### Q5: 训练失败怎么办？

**A**: 
- 检查数据格式是否正确
- 减小批次大小
- 检查GPU内存是否足够
- 查看错误日志

---

## 📚 详细文档

- **数据标注**: `DATA_ANNOTATION_GUIDE.md` - 完整的数据标注指南
- **训练指南**: `TRAINING_GUIDE.md` - 详细的训练参数和技巧
- **模型架构**: 查看 `application/net/model/` 目录

---

## 🎉 完成！

训练完成后，重启应用即可使用你自己训练的模型：

```bash
python run.py
```

祝你训练顺利！如有问题，请查看详细文档或提交Issue。


