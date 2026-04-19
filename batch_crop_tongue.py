"""
批量舌头裁剪脚本（YOLOv5 + SAM）

用途：
- 使用已经训练好的 YOLOv5 检测舌头位置
- 使用 SAM 做精细分割
- 将裁剪后的舌头小图保存到 data/cropped_tongues/train 和 data/cropped_tongues/val

输入（默认）：
- images/train/*.jpg|png|jpeg|JPG
- images/val/*.jpg|png|jpeg|JPG

输出：
data/cropped_tongues/
├── train/
└── val/

使用方法：
1. 激活环境：
   conda activate AiDiagnosis-3.12

2. 在项目根目录 D:\\TD 下运行：
   python batch_crop_tongue.py
"""

import os
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

from yolov5 import load
from segment_anything import sam_model_registry, SamPredictor


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def load_models(
    yolo_path: str = "application/net/weights/yolov5.pt",
    sam_path: str = "application/net/weights/sam_vit_b_01ec64.pth",
):
    """
    加载 YOLOv5 和 SAM 模型（和线上推理保持一致）。
    为了稳定和可复现，这里默认使用 CPU；后续如果需要可以再改为自动使用 GPU。
    """
    device = torch.device("cpu")
    print(f"[INFO] 使用设备: {device}")

    print(f"[1/2] 加载 YOLOv5 模型: {yolo_path}")
    yolo = load(yolo_path, device="cpu")
    yolo.eval()

    print(f"[2/2] 加载 SAM 模型: {sam_path}")
    sam = sam_model_registry["vit_b"](checkpoint=sam_path)
    sam_predictor = SamPredictor(sam_model=sam)

    return yolo, sam_predictor, device


def crop_one_image(
    img_path: Path,
    out_dir: Path,
    yolo,
    sam_predictor: SamPredictor,
    conf_threshold: float = 0.5,
):
    """
    对单张图片执行：
    1. YOLOv5 检测舌头框
    2. SAM 精细分割
    3. 使用掩码边界框裁剪舌头区域并保存
    """
    try:
        image = Image.open(img_path).convert("RGB")
    except Exception as e:
        print(f"[WARN] 无法打开图片 {img_path}: {e}")
        return False

    # 1. YOLO 检测
    with torch.no_grad():
        pred = yolo(image)

    detections = pred.xyxy[0]  # [N, 6] -> x1,y1,x2,y2,conf,cls

    if len(detections) > 0:
        confidences = detections[:, 4]
        valid_mask = confidences >= conf_threshold
        detections = detections[valid_mask]

    if len(detections) < 1:
        print(f"[WARN] {img_path} 未检测到舌头，跳过。")
        return False

    if len(detections) > 1:
        # 多个框时，选择置信度最高的
        confidences = detections[:, 4]
        best_idx = confidences.argmax().item()
        best_det = detections[best_idx]
    else:
        best_det = detections[0]

    x1, y1, x2, y2 = (
        best_det[0].item(),
        best_det[1].item(),
        best_det[2].item(),
        best_det[3].item(),
    )

    # 2. SAM 分割
    with torch.no_grad():
        np_img = np.array(image)
        sam_predictor.set_image(np_img)
        masks, scores, logits = sam_predictor.predict(
            box=np.array([x1, y1, x2, y2])
        )
        best_mask_idx = np.argmax(scores)
        best_mask = masks[best_mask_idx]  # (H, W)

        masked_img = np_img.copy()
        masked_img[~best_mask] = [0, 0, 0]

        mask_coords = np.where(best_mask)
        if len(mask_coords[0]) > 0:
            min_y, max_y = mask_coords[0].min(), mask_coords[0].max()
            min_x, max_x = mask_coords[1].min(), mask_coords[1].max()
            crop = Image.fromarray(masked_img).crop(
                (min_x, min_y, max_x, max_y)
            ).convert("RGB")
        else:
            # 掩码异常时退回到 YOLO 框
            crop = Image.fromarray(masked_img).crop(
                (x1, y1, x2, y2)
            ).convert("RGB")

    # 3. 保存裁剪结果
    rel_name = img_path.name  # 保留原文件名
    out_path = out_dir / rel_name
    ensure_dir(out_dir)
    try:
        crop.save(out_path)
    except Exception as e:
        print(f"[WARN] 保存裁剪结果失败 {out_path}: {e}")
        return False

    return True


def batch_process_split(
    split_name: str,
    in_dir: Path,
    out_dir: Path,
    yolo,
    sam_predictor: SamPredictor,
):
    """
    处理一个划分（train 或 val）
    """
    exts = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]
    img_files = []
    for ext in exts:
        img_files.extend(in_dir.glob(ext))

    img_files = sorted(img_files)

    if not img_files:
        print(f"[WARN] 在 {in_dir} 中没有找到图片，跳过 {split_name}。")
        return

    print(f"[INFO] {split_name}: 共 {len(img_files)} 张图片，将输出到 {out_dir}")

    ok = 0
    for img_path in tqdm(img_files, desc=f"{split_name} 裁剪中"):
        if crop_one_image(img_path, out_dir, yolo, sam_predictor):
            ok += 1

    print(f"[DONE] {split_name}: 成功裁剪 {ok}/{len(img_files)} 张图片。")


def main():
    project_root = Path(__file__).resolve().parent

    # 输入目录：和你现在的数据结构保持一致
    train_in = project_root / "images" / "train"
    val_in = project_root / "images" / "val"

    # 输出目录：按照文档约定
    train_out = project_root / "data" / "cropped_tongues" / "train"
    val_out = project_root / "data" / "cropped_tongues" / "val"

    print("[INFO] 批量舌头裁剪开始")
    print(f"[INFO] 训练集输入: {train_in}")
    print(f"[INFO] 验证集输入: {val_in}")
    print(f"[INFO] 训练集输出: {train_out}")
    print(f"[INFO] 验证集输出: {val_out}")

    # 加载模型
    yolo, sam_predictor, device = load_models()

    # 处理 train / val
    if train_in.exists():
        batch_process_split("train", train_in, train_out, yolo, sam_predictor)
    else:
        print(f"[WARN] 训练集目录不存在: {train_in}")

    if val_in.exists():
        batch_process_split("val", val_in, val_out, yolo, sam_predictor)
    else:
        print(f"[WARN] 验证集目录不存在: {val_in}")

    print("[INFO] 全部裁剪完成。")


if __name__ == "__main__":
    main()




