# 07 — ResNet50 四维分类

**所在文件**: `application/net/predict.py` 第 243-265 行 + `application/net/model/resnet.py`

## 作用

对 SAM 裁剪后的舌体图像进行四维特征分类，得到中医辨证需要的 4 个基本特征。

## 不是 1 个分类器，是 4 个

```python
# resnet.py 第 81 行
class ResNetPredictor:
    def __init__(self, paths, device):
        self.nets = [
            ResNet50(num_classes=5, if_se=True),  # 舌色：5 类
            ResNet50(num_classes=3, if_se=True),  # 苔色：3 类
            ResNet50(num_classes=2, if_se=True),  # 厚薄：2 类
            ResNet50(num_classes=2, if_se=True),  # 腐腻：2 类
        ]
        # 每个单独加载权重
        for net, path in zip(self.nets, paths):
            net.load_state_dict(torch.load(path, ...))
```

**4 个独立的 ResNet50 网络，各自训练不同分类任务。**

## 四个特征维度

| 索引 | 特征 | 类别数 | 分类结果 |
|------|------|--------|---------|
| 0 | 舌色 | 5 | 淡白舌 / 淡红舌 / 红舌 / 绛舌 / 青紫舌 |
| 1 | 苔色 | 3 | 白苔 / 黄苔 / 灰黑苔 |
| 2 | 舌体厚薄 | 2 | 薄 / 厚 |
| 3 | 腐腻情况 | 2 | 正常 / 腐腻 |

## 推理调用

```python
# predict.py 第 243 行 — 送入裁剪后的舌体
result_np = self.resnet.predict(result_np)
# 返回 [舌色_index, 苔色_index, 厚薄_index, 腐腻_index]
# 例如: [1, 0, 0, 0] → 淡红舌、白苔、薄、正常
```

`resnet.py` 中 `predict()` 方法细节：
```python
def predict(self, img):
    # 1. 转为张量 + 归一化
    img_tensor = transforms.ToTensor()(img).unsqueeze(0).to(self.device)
    img_tensor = self.normalize(img_tensor)  # ImageNet 均值方差
    
    # 2. 4 个网络分别推理
    result = []
    for net in self.nets:
        with torch.no_grad():
            output = net(img_tensor)
            _, predicted = torch.max(output, 1)
            result.append(predicted.item())
    return np.array(result)
```

## 权重文件

| 文件 | 对应分类器 |
|------|-----------|
| `tongue_color.pth` | 舌色分类器（5类） |
| `tongue_coat_color.pth` | 苔色分类器（3类） |
| `thickness.pth` | 厚薄分类器（2类） |
| `rot_and_greasy.pth` | 腐腻分类器（2类） |

## 注意力机制

每个 ResNet50 都开启了 SE 注意力模块（`if_se=True`）：

```python
# resnet.py — SE 模块嵌入 ResNet 的 BasicBlock 中
class SELayer(nn.Module):
    def __init__(self, channel, reduction=16):
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channel, channel // reduction),
            nn.ReLU(inplace=True),
            nn.Linear(channel // reduction, channel),
            nn.Sigmoid()
        )
```

SE 模块让网络学会"关注"重要的特征通道，抑制不重要的通道，提升分类精度。

## 推理时间优化

4 个 ResNet50 的推理可以在 GPU 上并行计算（如果不手动拆开的话），当前实现是串行推理四个网络，也可以改为 batch 推理进一步提速。
