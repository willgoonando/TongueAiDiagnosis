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

import queue
import tempfile
import torch
from PIL import Image
import numpy as np
from yolov5 import load
from segment_anything import sam_model_registry,SamPredictor
from application.net.model.resnet import ResNetPredictor
from application.config import settings


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
        predict_img = Image.open(img)
        self.yolo.eval()
        print("Tongue positioning")
        with torch.no_grad():
            # YOLOv5 AutoShape 不支持直接传递 conf 参数，先调用模型
            pred = self.yolo(predict_img)
        
        # 获取检测结果，格式: [x1, y1, x2, y2, conf, class]
        detections = pred.xyxy[0]
        
        # 设置置信度阈值，过滤低置信度检测
        conf_threshold = 0.5
        if len(detections) > 0:
            # 过滤低置信度检测
            confidences = detections[:, 4]
            valid_mask = confidences >= conf_threshold
            detections = detections[valid_mask]
        
        if len(detections) < 1:
            fun(event_id=record_id,
                tongue_color=None,
                coating_color=None,
                tongue_thickness=None,
                rot_greasy=None,
                code=201)
            print("The picture is not legal and has no tongue.")
            return
        elif len(detections) > 1:
            # 如果检测到多个框，选择置信度最高的
            confidences = detections[:, 4]  # 获取所有检测的置信度
            best_idx = confidences.argmax().item()  # 找到置信度最高的索引
            print(f"Detected {len(detections)} tongues, using the one with highest confidence: {confidences[best_idx]:.3f}")
            # 使用置信度最高的检测结果
            best_detection = detections[best_idx]
            x1, y1, x2, y2 = best_detection[0].item(), best_detection[1].item(), best_detection[2].item(), best_detection[3].item()
        else:
            # 只有一个检测结果，直接使用
            x1, y1, x2, y2 = detections[0][0].item(), detections[0][1].item(), detections[0][2].item(), detections[0][3].item()
        print("Tongue segmentation")
        with torch.no_grad():
            # 优化：复用已创建的SAM Predictor，避免每次创建新实例
            self.sam_predictor.set_image(np.array(predict_img))
            # SAM 返回多个掩码，选择得分最高的
            masks, scores, logits = self.sam_predictor.predict(box=np.array([x1, y1, x2, y2]))
            best_mask_idx = np.argmax(scores)
            best_mask = masks[best_mask_idx]  # 形状: (H, W)
            
            original_img = np.array(predict_img)
            # 应用掩码：非掩码区域设为黑色背景
            masked_img = original_img.copy()
            masked_img[~best_mask] = [0, 0, 0]
            
            # 使用掩码的精确边界框（比 YOLOv5 边界框更精确）
            mask_coords = np.where(best_mask)
            if len(mask_coords[0]) > 0:
                min_y, max_y = mask_coords[0].min(), mask_coords[0].max()
                min_x, max_x = mask_coords[1].min(), mask_coords[1].max()
                # 使用掩码边界框裁剪（更精确，去除更多背景）
                result = Image.fromarray(masked_img).crop((min_x, min_y, max_x, max_y)).convert("RGB")
            else:
                # 回退到 YOLOv5 边界框
                result = Image.fromarray(masked_img).crop((x1, y1, x2, y2)).convert("RGB")
            result = np.array(result)
        result = self.resnet.predict(result)
        print("Tongue analysis")
        predict_result = {
            "code": 0,
            'tongue_color': result[0],
            'tongue_coat_color': result[1],
            'thickness': result[2],
            'rot_and_greasy': result[3]
        }
        fun(event_id=record_id,
            tongue_color=result[0],
            coating_color=result[1],
            tongue_thickness=result[2],
            rot_greasy=result[3],
            code=1)
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
            except queue.Empty:
                # 队列为空时继续循环，不占用CPU
                continue
