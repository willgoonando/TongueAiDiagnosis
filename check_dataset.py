"""
数据集检查脚本

检查YOLOv5和ResNet数据集格式是否正确
"""

import argparse
from pathlib import Path
import yaml


def check_yolo_dataset(data_yaml):
    """检查YOLOv5数据集"""
    print("=" * 60)
    print("检查YOLOv5数据集")
    print("=" * 60)
    
    # 读取配置文件
    with open(data_yaml, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    base_path = Path(data['path'])
    train_path = base_path / data['train']
    val_path = base_path / data['val']
    train_labels = base_path / 'labels' / 'train'
    val_labels = base_path / 'labels' / 'val'
    
    # 检查目录
    errors = []
    if not train_path.exists():
        errors.append(f"训练图像目录不存在: {train_path}")
    if not val_path.exists():
        errors.append(f"验证图像目录不存在: {val_path}")
    if not train_labels.exists():
        errors.append(f"训练标注目录不存在: {train_labels}")
    if not val_labels.exists():
        errors.append(f"验证标注目录不存在: {val_labels}")
    
    if errors:
        print("❌ 发现错误:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    # 统计图像和标注
    train_images = list(train_path.glob('*.jpg')) + list(train_path.glob('*.png'))
    val_images = list(val_path.glob('*.jpg')) + list(val_path.glob('*.png'))
    
    print(f"✓ 训练图像: {len(train_images)} 张")
    print(f"✓ 验证图像: {len(val_images)} 张")
    
    # 检查标注文件
    missing_labels = []
    for img in train_images:
        label_file = train_labels / f"{img.stem}.txt"
        if not label_file.exists():
            missing_labels.append(img.name)
    
    if missing_labels:
        print(f"❌ 发现 {len(missing_labels)} 张训练图像缺少标注文件")
        print("   前10个:", missing_labels[:10])
        return False
    
    print("✓ 所有训练图像都有对应的标注文件")
    
    # 检查标注格式
    format_errors = []
    for label_file in list(train_labels.glob('*.txt'))[:10]:  # 检查前10个
        with open(label_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    format_errors.append(f"{label_file.name}: 格式错误")
                    break
                try:
                    class_id, cx, cy, w, h = map(float, parts)
                    if not (0 <= cx <= 1 and 0 <= cy <= 1 and 0 <= w <= 1 and 0 <= h <= 1):
                        format_errors.append(f"{label_file.name}: 坐标超出范围")
                        break
                except ValueError:
                    format_errors.append(f"{label_file.name}: 无法解析数字")
                    break
    
    if format_errors:
        print("❌ 发现标注格式错误:")
        for error in format_errors[:5]:
            print(f"  - {error}")
        return False
    
    print("✓ 标注格式正确")
    print(f"✓ 类别数: {data['nc']}")
    print(f"✓ 类别名称: {data['names']}")
    print("\n✅ YOLOv5数据集检查通过！")
    return True


def check_resnet_dataset(data_path):
    """检查ResNet数据集"""
    print("=" * 60)
    print("检查ResNet数据集")
    print("=" * 60)
    
    data_path = Path(data_path)
    tasks = ['tongue_color', 'tongue_coat_color', 'thickness', 'rot_and_greasy']
    task_classes = {
        'tongue_color': 5,
        'tongue_coat_color': 3,
        'thickness': 2,
        'rot_and_greasy': 2
    }
    
    all_ok = True
    
    for task in tasks:
        print(f"\n检查任务: {task}")
        task_path = data_path / task
        
        if not task_path.exists():
            print(f"❌ 任务目录不存在: {task_path}")
            all_ok = False
            continue
        
        for split in ['train', 'val']:
            split_path = task_path / split
            if not split_path.exists():
                print(f"❌ {split} 目录不存在: {split_path}")
                all_ok = False
                continue
            
            # 检查类别文件夹
            class_dirs = sorted([d for d in split_path.iterdir() if d.is_dir()])
            expected_classes = task_classes[task]
            
            if len(class_dirs) != expected_classes:
                print(f"❌ {split} 类别数不正确: 期望 {expected_classes}, 实际 {len(class_dirs)}")
                all_ok = False
                continue
            
            # 统计每个类别的图像数
            total_images = 0
            for class_dir in class_dirs:
                images = list(class_dir.glob('*.jpg')) + list(class_dir.glob('*.png')) + \
                        list(class_dir.glob('*.jpeg')) + list(class_dir.glob('*.JPG'))
                total_images += len(images)
                print(f"  {class_dir.name}: {len(images)} 张图像")
            
            print(f"  ✓ {split} 总计: {total_images} 张图像")
    
    if all_ok:
        print("\n✅ ResNet数据集检查通过！")
    else:
        print("\n❌ ResNet数据集检查失败，请修复上述问题")
    
    return all_ok


def main():
    parser = argparse.ArgumentParser(description='检查数据集格式')
    parser.add_argument('--yolo_data', type=str, default=None,
                        help='YOLOv5数据集配置文件路径')
    parser.add_argument('--resnet_data', type=str, default=None,
                        help='ResNet数据集根目录路径')
    
    args = parser.parse_args()
    
    if not args.yolo_data and not args.resnet_data:
        print("请指定要检查的数据集类型:")
        print("  --yolo_data: 检查YOLOv5数据集")
        print("  --resnet_data: 检查ResNet数据集")
        return
    
    if args.yolo_data:
        check_yolo_dataset(args.yolo_data)
    
    if args.resnet_data:
        check_resnet_dataset(args.resnet_data)


if __name__ == '__main__':
    main()

