"""
准备训练数据脚本
检查当前数据结构并给出建议
"""
import os
from pathlib import Path

def check_data_structure():
    print("=" * 60)
    print("检查当前数据结构")
    print("=" * 60)
    
    # 检查images目录
    images_train = Path("images/train")
    images_val = Path("images/val")
    
    if images_train.exists():
        train_imgs = list(images_train.glob("*.jpg")) + list(images_train.glob("*.png"))
        print(f"[OK] 训练图片: {len(train_imgs)} 张 (在 images/train/)")
    else:
        print("[X] 未找到 images/train/ 目录")
        train_imgs = []
    
    if images_val.exists():
        val_imgs = list(images_val.glob("*.jpg")) + list(images_val.glob("*.png"))
        print(f"[OK] 验证图片: {len(val_imgs)} 张 (在 images/val/)")
    else:
        print("[X] 未找到 images/val/ 目录")
        val_imgs = []
    
    # 检查YOLOv5标注
    labels_train = Path("images/labels/train")
    labels_val = Path("images/labels/val")
    
    has_yolo_labels = False
    if labels_train.exists():
        train_labels = list(labels_train.glob("*.txt"))
        print(f"[OK] YOLOv5训练标注: {len(train_labels)} 个文件")
        has_yolo_labels = True
    else:
        print("[X] 未找到 YOLOv5 标注文件 (images/labels/train/)")
    
    if labels_val.exists():
        val_labels = list(labels_val.glob("*.txt"))
        print(f"[OK] YOLOv5验证标注: {len(val_labels)} 个文件")
        has_yolo_labels = True
    else:
        print("[X] 未找到 YOLOv5 标注文件 (images/labels/val/)")
    
    # 检查ResNet分类数据
    data_dir = Path("data")
    has_resnet_data = False
    if data_dir.exists():
        tasks = ['tongue_color', 'tongue_coat_color', 'thickness', 'rot_and_greasy']
        for task in tasks:
            task_dir = data_dir / task / "train"
            if task_dir.exists():
                class_dirs = [d for d in task_dir.iterdir() if d.is_dir()]
                total_imgs = 0
                for class_dir in class_dirs:
                    imgs = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
                    total_imgs += len(imgs)
                if total_imgs > 0:
                    print(f"[OK] {task} 分类数据: {total_imgs} 张图片")
                    has_resnet_data = True
            else:
                print(f"[X] 未找到 {task} 分类数据")
    
    print("\n" + "=" * 60)
    print("训练建议")
    print("=" * 60)
    
    if not has_yolo_labels and not has_resnet_data:
        print("\n当前状态：只有原始图片，没有标注数据")
        print("\n你需要决定训练策略：")
        print("\n【选项1】训练YOLOv5检测模型（需要先标注边界框）")
        print("  1. 使用LabelImg标注舌头位置")
        print("  2. 训练YOLOv5模型")
        print("  3. 使用YOLOv5检测并裁剪舌头")
        print("  4. 将裁剪的舌头图片分类")
        print("  5. 训练ResNet分类模型")
        print("\n【选项2】如果图片已经是裁剪好的舌头图片")
        print("  1. 直接将图片分类到对应类别文件夹")
        print("  2. 训练ResNet分类模型")
        print("  （跳过YOLOv5训练）")
        print("\n请告诉我你的图片类型，我会帮你继续！")
    
    elif has_yolo_labels and not has_resnet_data:
        print("\n[OK] 已有YOLOv5标注数据，可以训练YOLOv5模型")
        print("[X] 缺少ResNet分类数据，需要先分类图片")
    
    elif not has_yolo_labels and has_resnet_data:
        print("\n[X] 缺少YOLOv5标注，但已有ResNet分类数据")
        print("[OK] 可以直接训练ResNet分类模型")
        print("[!] 如果需要训练YOLOv5，需要先标注")
    
    elif has_yolo_labels and has_resnet_data:
        print("\n[OK] 数据准备完整！")
        print("[OK] 可以开始训练所有模型")

if __name__ == "__main__":
    check_data_structure()

