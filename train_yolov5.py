"""
YOLOv5 舌头检测模型训练脚本

用于训练自定义的YOLOv5模型来检测舌头位置

使用方法：
    python train_yolov5.py --data data/tongue.yaml --epochs 100 --batch 16
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='训练YOLOv5舌头检测模型')
    parser.add_argument('--data', type=str, required=True,
                        help='数据集配置文件路径 (YAML格式)')
    parser.add_argument('--weights', type=str, default='yolov5s.pt',
                        help='预训练权重路径 (default: yolov5s.pt)')
    parser.add_argument('--epochs', type=int, default=100,
                        help='训练轮数 (default: 100)')
    parser.add_argument('--batch', type=int, default=16,
                        help='批次大小 (default: 16)')
    parser.add_argument('--img', type=int, default=640,
                        help='图像尺寸 (default: 640)')
    parser.add_argument('--device', type=str, default='',
                        help='设备 (default: 自动检测, 可用: 0,1,2,3 或 cpu)')
    parser.add_argument('--project', type=str, default='runs/train',
                        help='项目保存目录 (default: runs/train)')
    parser.add_argument('--name', type=str, default='tongue_detection',
                        help='实验名称 (default: tongue_detection)')
    parser.add_argument('--resume', type=str, default='',
                        help='恢复训练的检查点路径')
    
    args = parser.parse_args()
    
    # 检查数据集配置文件是否存在
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"错误: 数据集配置文件不存在: {args.data}")
        print("\n请先创建数据集配置文件，参考 data/tongue.yaml.example")
        sys.exit(1)
    
    # 构建训练命令
    cmd = [
        'yolov5', 'train',
        '--data', str(args.data),
        '--weights', args.weights,
        '--epochs', str(args.epochs),
        '--batch', str(args.batch),
        '--img', str(args.img),
        '--project', args.project,
        '--name', args.name,
    ]
    
    if args.device:
        cmd.extend(['--device', args.device])
    
    if args.resume:
        cmd.extend(['--resume', args.resume])
    
    print("=" * 60)
    print("YOLOv5 舌头检测模型训练")
    print("=" * 60)
    print(f"数据集配置: {args.data}")
    print(f"预训练权重: {args.weights}")
    print(f"训练轮数: {args.epochs}")
    print(f"批次大小: {args.batch}")
    print(f"图像尺寸: {args.img}")
    print(f"保存目录: {args.project}/{args.name}")
    print("=" * 60)
    print("\n开始训练...\n")
    
    # 执行训练命令
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("训练完成！")
        print("=" * 60)
        print(f"最佳模型保存在: {args.project}/{args.name}/weights/best.pt")
        print(f"最后模型保存在: {args.project}/{args.name}/weights/last.pt")
        print("\n部署模型:")
        print(f"copy {args.project}/{args.name}/weights/best.pt application/net/weights/yolov5.pt")
    except subprocess.CalledProcessError as e:
        print(f"\n训练失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n错误: 未找到 yolov5 命令")
        print("请确保已安装 yolov5 包: pip install yolov5")
        sys.exit(1)


if __name__ == '__main__':
    main()

