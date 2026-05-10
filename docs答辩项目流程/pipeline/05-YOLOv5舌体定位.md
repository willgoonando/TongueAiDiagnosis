# 05 — YOLOv5 舌体定位

**所在文件**: `application/net/predict.py` 第 115-175 行

## 作用

从原始舌象图片中检测舌头的位置，输出边界框（bounding box）。

## 代码流程

```python
# 第 115 行
self.yolo.eval()
with torch.no_grad():
    pred = self.yolo(predict_img)

# 取出检测结果
detections = pred.xyxy[0]  # shape: (N, 6)
# 每行: [x1, y1, x2, y2, confidence, class]
```

## 过滤策略

```python
conf_threshold = 0.5
if len(detections) > 0:
    confidences = detections[:, 4]
    valid_mask = confidences >= conf_threshold
    detections = detections[valid_mask]
```

过滤掉置信度低于 0.5 的检测结果，保留高置信度的。

## 多舌头处理

```python
if len(detections) > 1:
    # 多个检测框 → 选置信度最高的
    best_idx = confidences.argmax().item()
    best_detection = detections[best_idx]
    x1, y1, x2, y2 = ...
    # 输出日志：选中的框坐标 + 置信度
elif len(detections) == 1:
    # 正常情况
    x1, y1, x2, y2 = ...
```

## 错误处理

| code | 说明 |
|------|------|
| 201 | 未检测到舌头 → 提示用户重新上传 |
| 202 | 不支持（已改为自动选置信度最高） |
| 203 | 其他解析错误 |

## 可视化（新增）

推理后保存 YOLO 检测框图到 pipeline 目录：

```python
yolo_viz = orig_np.copy()
cv2.rectangle(yolo_viz, (x1, y1), (x2, y2), (0, 255, 0), 3)  # 绿色框
cv2.putText(yolo_viz, f"Tongue {conf:.2f}", (x1, y1-10), ...)  # 置信度文字
_save_pipeline_step(record_id, "yolo", yolo_viz)
```

## 模型

- **权重文件**: `application/net/weights/yolov5.pt`
- **训练脚本**: `train_yolov5.py` 和 `train_yolov5_attention.py`
- **数据集**: 1000+ 张标注舌象图片（自己标注）

**你训练了带注意力机制的版本**（`train_yolov5_attention.py`），通过 forward hook 在 YOLOv5 中插入了 CBAM/SE/ECA 注意力模块。这是很多本科项目不会做的工作量。
