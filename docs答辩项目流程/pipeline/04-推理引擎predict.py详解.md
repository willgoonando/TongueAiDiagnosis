# 04 — 推理引擎 `predict.py` 详解

**文件**: `application/net/predict.py`

这是整个系统的 AI 核心，封装了 YOLOv5 + SAM + ResNet 的完整推理流程。

## 🏗️ 架构设计

### 单例模式

```python
class TonguePredictor:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, ...):
        if self._initialized:
            return  # 只初始化一次
        # 加载三个大模型权重...
        self._initialized = True
```

**原因**：YOLO + SAM + ResNet 四个权重文件加起来几百 MB，每次请求重新加载不可行。

### 生产者-消费者队列

```python
class TonguePredictor:
    def __init__(self, ...):
        self.queue = queue.Queue()  # 任务队列

    def predict(self, img, record_id, fun):
        # 生产者：把任务塞进队列，立即返回
        self.queue.put((tmpfile, record_id, fun))
        return {"code": 0}

    def main(self):
        # 消费者：死循环消费队列（在独立线程运行）
        while True:
            img, record_id, fun = self.queue.get(timeout=0.1)
            self.__predict(img, record_id, fun)
```

**启动方式**（`run.py`）：
```python
tonguePredictor = TonguePredictor()
threading.Thread(target=tonguePredictor.main).start()
uvicorn.run(app, host="0.0.0.0", port=5000)
```

## 核心方法 `__predict()` 执行流程

```
__predict(img, record_id, fun)
    │
    ├── 1. Image.open() 加载图片
    │
    ├── 2. YOLOv5 检测 → 获取舌体边界框 (x1,y1,x2,y2)
    │
    ├── 3. SAM 分割 → 获取精确掩码 (best_mask)
    │
    ├── 4. 舌体裁剪 → 用掩码边界框裁剪出舌体
    │
    ├── 5. ResNet50 分类 → 四个特征值
    │
    ├── 6. 回调 fun() 写数据库
    │
    └── 7. (新增) 保存中间结果图到 pipeline 目录
```

## 设备管理

```python
def _resolve_torch_device():
    # 从配置读取：cpu / auto / cuda
    mode = getattr(settings, "TORCH_DEVICE", "auto")
    if mode == "cpu": return torch.device("cpu")
    if mode == "cuda": return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # auto: 有 GPU 用 GPU，没有用 CPU
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

当前配置在 `config.py` 中设定为 `cpu`，可改为 `auto` 在有 GPU 时自动加速。

## ② 新增的 pipeline 图片保存

本次新增的 `_save_pipeline_step()` 函数在每个阶段保存中间结果：

```python
PIPELINE_DIR = os.path.join(项目根, "frontend", "public", "pipeline")

def _save_pipeline_step(record_id, step_name, img_array):
    # 1. 保存图片: {record_id}_{step_name}.jpg
    cv2.imwrite(filepath, cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR))
    
    # 2. 记录步骤名到 meta JSON
    meta["steps"].append(step_name)
    json.dump(meta, meta_path)
```

保存的步骤：
- `original` — 原始上传图片
- `yolo` — YOLO 检测框可视化（绿色框 + 置信度）
- `sam` — SAM 掩码可视化（半透明绿色覆盖 + 边界轮廓）
- `crop` — 裁剪后的舌体区域
- `features` — 四维分类结果（记录到 JSON，不保存图片）
