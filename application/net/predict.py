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
        self.device = torch.device('cpu')
        self.yolo = load(yolo_path, device='cpu')
        self.sam = sam_model_registry["vit_b"](checkpoint=sam_path)
        self.resnet = ResNetPredictor(resnet_path)
        self.queue = queue.Queue()
        TonguePredictor._initialized = True

    def __predict(self, img, record_id, fun):
        predict_img = Image.open(img)
        self.yolo.eval()
        print("Tongue positioning")
        with torch.no_grad():
            pred = self.yolo(predict_img)
        if len(pred.xyxy[0]) < 1:
            fun(event_id=record_id,
                tongue_color=None,
                coating_color=None,
                tongue_thickness=None,
                rot_greasy=None,
                code=201)
            print("The picture is not legal and has no tongue.")
            return
        elif len(pred.xyxy[0]) > 1:
            fun(event_id=record_id,
                tongue_color=None,
                coating_color=None,
                tongue_thickness=None,
                rot_greasy=None,
                code=202)
            print("The picture is not legal. There are too many tongues.")
            return
        print("Tongue segmentation")
        with torch.no_grad():
            x1, y1, x2, y2 = (
                pred.xyxy[0][0, 0].item(), pred.xyxy[0][0, 1].item(), pred.xyxy[0][0, 2].item(),
                pred.xyxy[0][0, 3].item())
            predictor = SamPredictor(sam_model=self.sam)
            predictor.set_image(np.array(predict_img))
            masks, _, _ = predictor.predict(box=np.array([x1, y1, x2, y2]))
            original_img = np.array(predict_img)
            masks = np.transpose(masks, (1,2,0))
            pred = original_img * masks
            result = Image.fromarray(pred).crop((x1, y1, x2, y2)).convert("RGB")
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
            if self.queue.empty():
                continue
            img, record_id, fun = self.queue.get()
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
