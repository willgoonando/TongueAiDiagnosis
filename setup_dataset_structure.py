"""
数据集目录结构生成脚本

自动创建训练所需的数据集目录结构
"""

import os
from pathlib import Path


def create_dataset_structure(base_path='./data'):
    """创建数据集目录结构"""
    base = Path(base_path)
    
    # 定义4个任务及其类别
    tasks = {
        'tongue_color': ['class0', 'class1', 'class2', 'class3', 'class4'],
        'tongue_coat_color': ['class0', 'class1', 'class2'],
        'thickness': ['class0', 'class1'],
        'rot_and_greasy': ['class0', 'class1']
    }
    
    # 创建目录结构
    for task_name, classes in tasks.items():
        for split in ['train', 'val']:
            for class_name in classes:
                dir_path = base / task_name / split / class_name
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"创建目录: {dir_path}")
    
    # 创建README文件
    readme_path = base / 'README.txt'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("""数据集目录结构说明
====================

请将训练图像按照以下规则放入对应目录：

1. 舌色分类 (tongue_color)
   - class0: 淡红舌（正常）
   - class1: 红舌（热证）
   - class2: 绛舌（热盛）
   - class3: 淡白舌（虚寒）
   - class4: 青紫舌（血瘀）

2. 苔色分类 (tongue_coat_color)
   - class0: 白苔（正常/寒证）
   - class1: 黄苔（热证）
   - class2: 灰黑苔（热极/寒极）

3. 厚度分类 (thickness)
   - class0: 薄
   - class1: 厚

4. 腐腻分类 (rot_and_greasy)
   - class0: 正常
   - class1: 腐腻

图像格式要求：
- 支持格式: JPG, PNG, JPEG
- 建议大小: 至少 224x224 像素
- 训练集和验证集建议比例: 8:2 或 7:3

示例：
将一张"红舌"的训练图像放入：
data/tongue_color/train/class1/red_tongue_001.jpg
""")
    
    print(f"\n✓ 数据集目录结构创建完成！")
    print(f"✓ 基础路径: {base.absolute()}")
    print(f"✓ 请查看 {readme_path} 了解详细说明")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='创建数据集目录结构')
    parser.add_argument('--path', type=str, default='./data',
                        help='数据集根目录路径 (default: ./data)')
    args = parser.parse_args()
    
    create_dataset_structure(args.path)

