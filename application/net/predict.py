"""舌象 AI 推理引擎（YOLOv5 + SAM + ResNet）

本模块封装了舌象识别的完整深度学习流程，主要步骤：
1. 使用 YOLOv5 定位舌头区域（目标检测，得到 bounding box）
2. 使用 SAM(Segment Anything) 对舌头区域做精细分割，得到舌头掩码
3. 将分割后的舌头裁剪出来，送入 ResNet 分类器，得到四个特征：
   - tongue_color：舌色
   - tongue_coat_color：苔色
   - thickness：舌体厚薄
   - rot_and_greasy：腐腻情况
4. 通过回调函数 fun(...) 将结果写入数据库（由 CRUD 层负责）

设计要点：
- 使用单例模式，避免在进程内重复加载大模型权重
- 使用内部 queue + main 循环模拟“推理任务队列”，在 run.py 中以线程启动

业务层不会直接依赖深度学习细节，而是通过 services/tongue_service.py 间接调用。
"""

import os
import queue
import tempfile
import cv2
import torch
from PIL import Image, ImageDraw
import numpy as np
from yolov5 import load
from segment_anything import sam_model_registry,SamPredictor
from application.net.model.resnet import ResNetPredictor
from application.config import settings


# Pipeline 中间结果保存目录（前端 public 下，可直接 URL 访问）
PIPELINE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend", "public", "pipeline"
)
os.makedirs(PIPELINE_DIR, exist_ok=True)


def _save_pipeline_step(record_id, step_name, img_array):
    """保存 pipeline 中间结果图到 frontend/public/pipeline/"""
    import json
    # 保存图片
    filepath = os.path.join(PIPELINE_DIR, f"{record_id}_{step_name}.jpg")
    cv2.imwrite(filepath, cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR))
    # 记录此 record_id 有哪些步骤已保存（方便前端查询）
    meta_path = os.path.join(PIPELINE_DIR, f"{record_id}_meta.json")
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        meta = {"steps": []}
    if step_name not in meta["steps"]:
        meta["steps"].append(step_name)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)



##    yong GPU加速
def _resolve_torch_device():
    mode = getattr(settings, "TORCH_DEVICE", "auto")
    if mode == "cpu":
        return torch.device("cpu")
    if mode == "cuda":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # auto
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


class TonguePredictor:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self,
                 yolo_path='application/net/weights/yolov5.pt',
                 sam_path='application/net/weights/sam_vit_b_01ec64.pth',
                 resnet_path=[
                     'application/net/weights/tongue_color.pth',
                     'application/net/weights/tongue_coat_color.pth',
                     'application/net/weights/thickness.pth',
                     'application/net/weights/rot_and_greasy.pth'
                 ]
                 ):
        if self._initialized:
            return
        self.device = _resolve_torch_device()
        print(f"  ⚙️ TonguePredictor 设备: {self.device.type.upper()} ({self.device})")
        if self.device.type == "cuda":
            print(f"     GPU: {torch.cuda.get_device_name(0)} | 显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        yolo_dev = "cuda:0" if self.device.type == "cuda" else "cpu"
        self.yolo = load(yolo_path, device=yolo_dev)
        self.sam = sam_model_registry["vit_b"](checkpoint=sam_path)
        self.sam.to(self.device)
        # 优化：在初始化时创建SAM Predictor，避免每次推理都创建新实例
        self.sam_predictor = SamPredictor(sam_model=self.sam)
        self.resnet = ResNetPredictor(resnet_path, device=self.device)
        self.queue = queue.Queue()
        TonguePredictor._initialized = True

    def __predict(self, img, record_id, fun):
        import time
        t_start = time.perf_counter()

        predict_img = Image.open(img)
        w, h = predict_img.size
        sep = "=" * 56
        print()
        print(f"{sep}")
        print(f"  🦷 舌象分析推理流水线  #{record_id}")
        print(f"  📐 输入图片: {w}×{h} px")
        print(f"  ⏱  开始时间: {time.strftime('%H:%M:%S')}")
        print(f"{sep}")

        # ── Stage 1: YOLOv5 目标检测 ──
        print()
        print(f"  ┌── [Stage 1/4] YOLOv5 舌体定位 ──────────────")
        t_yolo_start = time.perf_counter()
        self.yolo.eval()
        with torch.no_grad():
            pred = self.yolo(predict_img)
        detections = pred.xyxy[0]
        t_yolo = (time.perf_counter() - t_yolo_start) * 1000

        # 过滤低置信度
        conf_threshold = 0.5
        raw_count = len(detections)
        if len(detections) > 0:
            confidences = detections[:, 4]
            valid_mask = confidences >= conf_threshold
            detections = detections[valid_mask]
        filtered_count = len(detections)
        print(f"  │ 原始检测框: {raw_count} 个 | 过滤后: {filtered_count} 个 (阈={conf_threshold})")
        print(f"  │ YOLOv5 推理耗时: {t_yolo:.1f} ms")

        if len(detections) < 1:
            fun(event_id=record_id,
                tongue_color=None,
                coating_color=None,
                tongue_thickness=None,
                rot_greasy=None,
                code=201)
            print(f"  │ ❌ 未检测到舌头，返回错误码 201")
            print(f"  └──────────────────────────────────────────────")
            print()
            _save_pipeline_step(record_id, "original", np.array(predict_img))
            _save_pipeline_step(record_id, "yolo", np.array(predict_img))
            return

        elif len(detections) > 1:
            confidences = detections[:, 4]
            best_idx = confidences.argmax().item()
            best_detection = detections[best_idx]
            x1, y1, x2, y2 = best_detection[0].item(), best_detection[1].item(), best_detection[2].item(), best_detection[3].item()
            print(f"  │ ⚠️  检测到 {len(detections)} 个候选框，取置信度最高:")
            for i, det in enumerate(detections):
                c = det[4].item()
                mark = " ← 选中" if i == best_idx else ""
                print(f"  │   [{i}] box=({det[0]:.0f},{det[1]:.0f},{det[2]:.0f},{det[3]:.0f}) conf={c:.4f}{mark}")
        else:
            x1, y1, x2, y2 = detections[0][0].item(), detections[0][1].item(), detections[0][2].item(), detections[0][3].item()
            conf_val = detections[0][4].item()
            print(f"  │ ✅ 检测到 1 个目标: box=({x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f})")
            print(f"  │    置信度: {conf_val:.4f}  |  框面积: {int((x2-x1)*(y2-y1))} px²")

        # 转为 int
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        print(f"  └──────────────────────────────────────────────")
        print()

        # 保存原始和 YOLO 可视化
        orig_np = np.array(predict_img)
        _save_pipeline_step(record_id, "original", orig_np)
        yolo_viz = orig_np.copy()
        conf_val = detections[0][4].item() if len(detections) == 1 else confidences.max().item()
        cv2.rectangle(yolo_viz, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(yolo_viz, f"Tongue {conf_val:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        _save_pipeline_step(record_id, "yolo", yolo_viz)

        # ── Stage 2: SAM 分割 ──
        print(f"  ┌── [Stage 2/4] SAM 精细分割 ──────────────────")
        t_sam_start = time.perf_counter()
        with torch.no_grad():
            self.sam_predictor.set_image(np.array(predict_img))
            masks, scores, logits = self.sam_predictor.predict(box=np.array([x1, y1, x2, y2]))
        t_sam = (time.perf_counter() - t_sam_start) * 1000

        print(f"  │ SAM 生成 {len(masks)} 个候选掩码")
        best_mask_idx = int(np.argmax(scores))
        mask_detail = []
        for i, (s, m) in enumerate(zip(scores, masks)):
            px_count = int(m.sum())
            ratio = px_count / (w * h) * 100
            mark = " ⭐" if i == best_mask_idx else ""
            mask_detail.append(f"  │   [{i}] score={s:.4f}  |  掩码像素: {px_count} ({ratio:.1f}%){mark}")
        for line in mask_detail:
            print(line)
        best_mask = masks[best_mask_idx]
        iou_sam_yolo = (best_mask[y1:y2, x1:x2].sum()) / ((y2 - y1) * (x2 - x1))
        print(f"  │ ✅ 选中掩码 #{best_mask_idx}, score={scores[best_mask_idx]:.4f}")
        print(f"  │    SAM 掩码面积 / YOLO 框面积: {iou_sam_yolo:.2%}")
        print(f"  │ SAM 推理耗时: {t_sam:.1f} ms")
        print(f"  └──────────────────────────────────────────────")
        print()

        # ── Stage 3: 裁剪与预处理 ──
        print(f"  ┌── [Stage 3/4] 舌体裁剪 ──────────────────────")
        original_img = np.array(predict_img)
        masked_img = original_img.copy()
        masked_img[~best_mask] = [0, 0, 0]

        # SAM 掩码可视化
        overlay = original_img.copy()
        overlay[best_mask] = [0, 255, 0]
        sam_viz = (original_img * 0.5 + overlay * 0.5).astype(np.uint8)
        contours, _ = cv2.findContours(best_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(sam_viz, contours, -1, (0, 255, 0), 2)
        _save_pipeline_step(record_id, "sam", sam_viz)

        mask_coords = np.where(best_mask)
        if len(mask_coords[0]) > 0:
            min_y, max_y = int(mask_coords[0].min()), int(mask_coords[0].max())
            min_x, max_x = int(mask_coords[1].min()), int(mask_coords[1].max())
            result = Image.fromarray(masked_img).crop((min_x, min_y, max_x, max_y)).convert("RGB")
            crop_h, crop_w = max_y - min_y, max_x - min_x
            print(f"  │ SAM 精确裁剪: ({min_x},{min_y})→({max_x},{max_y})  =  {crop_w}×{crop_h} px")
        else:
            result = Image.fromarray(masked_img).crop((x1, y1, x2, y2)).convert("RGB")
            crop_w, crop_h = x2 - x1, y2 - y1
            print(f"  │ YOLO 后备裁剪: ({x1},{y1})→({x2},{y2})  =  {crop_w}×{crop_h} px")
        result_np = np.array(result)
        _save_pipeline_step(record_id, "crop", result_np)
        print(f"  │ 裁剪区域压缩率: {100 * crop_w * crop_h / (w * h):.1f}%（原图占比）")
        print(f"  └──────────────────────────────────────────────")
        print()

        # ── Stage 4: ResNet 分类 ──
        print(f"  ┌── [Stage 4/4] ResNet50 四维分类 ─────────────")
        t_resnet_start = time.perf_counter()
        result_np = self.resnet.predict(result_np)
        t_resnet = (time.perf_counter() - t_resnet_start) * 1000
        print(f"  │ ResNet50 推理耗时: {t_resnet:.1f} ms")

        label_map = ["舌色", "苔色", "舌体厚薄", "腐腻情况"]
        value_names = [
            ["淡白舌(0)", "淡红舌(1)", "红舌(2)", "绛舌(3)", "青紫舌(4)"],
            ["白苔(0)", "黄苔(1)", "灰黑苔(2)"],
            ["薄(0)", "厚(1)"],
            ["正常(0)", "腐腻(1)"],
        ]
        for i, val in enumerate(result_np):
            name = value_names[i][int(val)]
            print(f"  │   {label_map[i]:8s} → {name}")

        print(f"  └──────────────────────────────────────────────")
        print()

        # ── 汇总 ──
        t_total = (time.perf_counter() - t_start) * 1000
        predict_result = {
            "code": 0,
            'tongue_color': int(result_np[0]),
            'tongue_coat_color': int(result_np[1]),
            'thickness': int(result_np[2]),
            'rot_and_greasy': int(result_np[3])
        }

        print(f"{sep}")
        print(f"  ✅ 分析完成  #{record_id}")
        print(f"  ⏱  总耗时: {t_total:.0f} ms")
        print(f"     ├─ YOLOv5 检测:  {t_yolo:.0f} ms")
        print(f"     ├─ SAM 分割:      {t_sam:.0f} ms")
        print(f"     └─ ResNet 分类:    {t_resnet:.0f} ms")
        print()

        # 清理推理中间变量，释放显存（必须放在所有使用之后）
        fun(event_id=record_id,
            tongue_color=int(result_np[0]),
            coating_color=int(result_np[1]),
            tongue_thickness=int(result_np[2]),
            rot_greasy=int(result_np[3]),
            code=1)

        # 保存 pipeline meta
        _save_pipeline_step(record_id, "features", orig_np)
        import json
        meta_path = os.path.join(PIPELINE_DIR, f"{record_id}_meta.json")
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            meta = {"steps": []}
        meta["features"] = predict_result
        meta["steps"] = list(dict.fromkeys(meta["steps"] + ["features"]))
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # 清理中间变量（放最后）
        del predict_img, orig_np, yolo_viz, sam_viz, masked_img, result_np
        try:
            del detections, masks, scores, logits, best_mask, contours
        except NameError:
            pass
        if self.device.type == "cuda":
            torch.cuda.empty_cache()

        return predict_result

    def predict(self, img, record_id, fun):
        try:
            img.seek(0)
            tmpfile = tempfile.SpooledTemporaryFile()
            content = img.read()
            tmpfile.write(content)
            self.queue.put((tmpfile, record_id, fun))
            img.seek(0)
            return {"code": 0}
        except Exception as e:
            return {"code": 3}

    def main(self):
        while True:
            try:
                # 优化：使用queue.get(timeout=0.1)替代空检查，避免CPU空转
                # 如果队列为空，会等待0.1秒后抛出Empty异常，然后继续循环
                img, record_id, fun = self.queue.get(timeout=0.1)
                try:
                    self.__predict(img, record_id, fun)
                except Exception as e:
                    print(e)
                    fun(event_id=record_id,
                        tongue_color=None,
                        coating_color=None,
                        tongue_thickness=None,
                        rot_greasy=None,
                        code=203)
                finally:
                    img.close()
                    # 清理 GPU 缓存，避免推理后显存持续占用过高
                    if self.device.type == "cuda":
                        torch.cuda.empty_cache()
            except queue.Empty:
                # 队列为空时继续循环，不占用CPU
                continue
