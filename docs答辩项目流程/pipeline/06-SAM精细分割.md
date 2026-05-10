# 06 — SAM 精细分割

**所在文件**: `application/net/predict.py` 第 196-220 行

## 作用

在 YOLO 边界框的基础上，用 SAM（Segment Anything）对舌头做像素级分割，得到精确的舌体掩码。

## 为什么需要 SAM？

YOLO 输出的是**矩形框**，但舌头不是矩形的。直接裁剪矩形框会带很多背景（嘴唇、牙齿、皮肤），影响后续分类精度。SAM 能给出**像素级精确的舌体轮廓**。

## 代码流程

```python
# 优化：复用 Predictor 实例，避免每次重建
self.sam_predictor.set_image(np.array(predict_img))

# 基于 YOLO 的 box 做分割
masks, scores, logits = self.sam_predictor.predict(
    box=np.array([x1, y1, x2, y2])
)

# SAM 返回多个候选掩码，选得分最高的
best_mask_idx = np.argmax(scores)
best_mask = masks[best_mask_idx]  # 布尔数组 (H, W)
```

## 关键优化点

### 1. 复用 SAM Predictor（第 67 行）

```python
def __init__(self, ...):
    # 在初始化时创建，不要每次推理都创建
    self.sam_predictor = SamPredictor(sam_model=self.sam)
```

避免每次推理都 `SamPredictor(sam_model)` —— 这个创建过程有额外开销。

### 2. 掩码边界框比 YOLO 框更精确

```python
mask_coords = np.where(best_mask)
if len(mask_coords[0]) > 0:
    min_y, max_y = mask_coords[0].min(), mask_coords[0].max()
    min_x, max_x = mask_coords[1].min(), mask_coords[1].max()
    # 用掩码边界框裁剪（更精确，去除更多背景）
    result = Image.fromarray(masked_img).crop((min_x, min_y, max_x, max_y))
else:
    # 回退到 YOLO 边界框
    result = Image.fromarray(masked_img).crop((x1, y1, x2, y2))
```

YOLO 框可能包含舌头周围的背景；SAM 掩码的边界框则紧贴舌头边缘。

## 掩码处理

```python
# 非掩码区域设为黑色背景
masked_img[~best_mask] = [0, 0, 0]
```

这一步确保送入 ResNet 的只有舌头区域，背景被剔除。

## 可视化（新增）

```python
# 半透明绿色覆盖
overlay[best_mask] = [0, 255, 0]
sam_viz = (original_img * 0.5 + overlay * 0.5).astype(np.uint8)
# 画掩码边界轮廓
cv2.drawContours(sam_viz, contours, -1, (0, 255, 0), 2)
_save_pipeline_step(record_id, "sam", sam_viz)
```

## 模型

- **权重文件**: `application/net/weights/sam_vit_b_01ec64.pth`
- SAM 的 ViT-B 版本（平衡速度与精度）
