"""
ResNet50 分类模型训练脚本

用于训练舌象分析的4个分类任务：
1. tongue_color（舌色）：5类
2. tongue_coat_color（苔色）：3类
3. thickness（厚度）：2类
4. rot_and_greasy（腐腻）：2类

使用方法：
    python train_resnet.py --task tongue_color --data_path ./data/tongue_color --epochs 50 --batch_size 32
"""

import argparse
import os
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from PIL import Image
from tqdm import tqdm

from application.net.model.resnet import ResNet50


class TongueDataset(Dataset):
    """舌象分类数据集
    
    数据集目录结构：
    data/
    ├── tongue_color/
    │   ├── class0/
    │   ├── class1/
    │   ├── class2/
    │   ├── class3/
    │   └── class4/
    ├── tongue_coat_color/
    │   ├── class0/
    │   ├── class1/
    │   └── class2/
    ...
    """
    
    def __init__(self, root_dir, task_name, split='train', transform=None):
        """
        Args:
            root_dir: 数据集根目录
            task_name: 任务名称 (tongue_color, tongue_coat_color, thickness, rot_and_greasy)
            split: 数据集划分 ('train' 或 'val')
            transform: 图像变换
        """
        self.root_dir = Path(root_dir)
        self.task_dir = self.root_dir / task_name / split
        self.transform = transform
        self.images = []
        self.labels = []
        
        # 获取所有类别文件夹
        class_dirs = sorted([d for d in self.task_dir.iterdir() if d.is_dir()])
        
        if len(class_dirs) == 0:
            raise ValueError(f"在 {self.task_dir} 中未找到类别文件夹！请检查数据集路径。")
        
        # 加载所有图像和标签
        for class_idx, class_dir in enumerate(class_dirs):
            image_files = list(class_dir.glob('*.jpg')) + list(class_dir.glob('*.png')) + \
                         list(class_dir.glob('*.jpeg')) + list(class_dir.glob('*.JPG'))
            
            for img_file in image_files:
                self.images.append(img_file)
                self.labels.append(class_idx)
        
        print(f"加载 {split} 数据集: {len(self.images)} 张图像, {len(class_dirs)} 个类别")
        print(f"类别: {[d.name for d in class_dirs]}")
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        img_path = self.images[idx]
        label = self.labels[idx]
        
        # 加载图像
        try:
            image = Image.open(img_path).convert('RGB')
        except Exception as e:
            print(f"加载图像失败 {img_path}: {e}")
            # 返回一个黑色图像作为占位符
            image = Image.new('RGB', (224, 224), color='black')
        
        if self.transform:
            image = self.transform(image)
        
        return image, label


def get_transforms(augment=True):
    """获取数据增强变换"""
    if augment:
        # 训练时的数据增强
        train_transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.RandomCrop(224),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            transforms.RandomRotation(degrees=15),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.29, 0.22, 0.23], std=[0.34, 0.27, 0.28])
        ])
    else:
        # 验证时只做标准化
        train_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.29, 0.22, 0.23], std=[0.34, 0.27, 0.28])
        ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.29, 0.22, 0.23], std=[0.34, 0.27, 0.28])
    ])
    
    return train_transform, val_transform


def train_epoch(model, dataloader, criterion, optimizer, device, epoch):
    """训练一个epoch"""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(dataloader, desc=f'Epoch {epoch} [Train]')
    for images, labels in pbar:
        images = images.to(device)
        labels = labels.to(device)
        
        # 前向传播
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        # 反向传播
        loss.backward()
        optimizer.step()
        
        # 统计
        running_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
        # 更新进度条
        pbar.set_postfix({
            'loss': f'{running_loss/total:.4f}',
            'acc': f'{100*correct/total:.2f}%'
        })
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100 * correct / total
    return epoch_loss, epoch_acc


def validate(model, dataloader, criterion, device):
    """验证模型"""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        pbar = tqdm(dataloader, desc='[Val]')
        for images, labels in pbar:
            images = images.to(device)
            labels = labels.to(device)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            pbar.set_postfix({
                'loss': f'{running_loss/total:.4f}',
                'acc': f'{100*correct/total:.2f}%'
            })
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100 * correct / total
    return epoch_loss, epoch_acc


def main():
    parser = argparse.ArgumentParser(description='训练ResNet50分类模型')
    parser.add_argument('--task', type=str, required=True,
                        choices=['tongue_color', 'tongue_coat_color', 'thickness', 'rot_and_greasy'],
                        help='训练任务名称')
    parser.add_argument('--data_path', type=str, required=True,
                        help='数据集根目录路径')
    parser.add_argument('--epochs', type=int, default=50,
                        help='训练轮数 (default: 50)')
    parser.add_argument('--batch_size', type=int, default=32,
                        help='批次大小 (default: 32)')
    parser.add_argument('--lr', type=float, default=0.001,
                        help='学习率 (default: 0.001)')
    parser.add_argument('--weight_decay', type=float, default=1e-4,
                        help='权重衰减 (default: 1e-4)')
    parser.add_argument('--num_workers', type=int, default=4,
                        help='数据加载线程数 (default: 4)')
    parser.add_argument('--save_dir', type=str, default='./checkpoints',
                        help='模型保存目录 (default: ./checkpoints)')
    parser.add_argument('--resume', type=str, default=None,
                        help='恢复训练的检查点路径')
    parser.add_argument('--device', type=str, default='auto',
                        help='设备 (auto/cpu/cuda)')
    
    args = parser.parse_args()
    
    # 设置设备
    if args.device == 'auto':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(args.device)
    
    print(f"使用设备: {device}")
    
    # 任务对应的类别数
    task_classes = {
        'tongue_color': 5,
        'tongue_coat_color': 3,
        'thickness': 2,
        'rot_and_greasy': 2
    }
    num_classes = task_classes[args.task]
    
    # 创建保存目录
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载数据集
    train_transform, val_transform = get_transforms(augment=True)
    
    train_dataset = TongueDataset(
        root_dir=args.data_path,
        task_name=args.task,
        split='train',
        transform=train_transform
    )
    
    val_dataset = TongueDataset(
        root_dir=args.data_path,
        task_name=args.task,
        split='val',
        transform=val_transform
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=True if device.type == 'cuda' else False
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=True if device.type == 'cuda' else False
    )
    
    # 创建模型
    model = ResNet50(num_classes=num_classes, if_se=True).to(device)
    
    # 损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5, verbose=True
    )
    
    # 恢复训练
    start_epoch = 0
    best_val_acc = 0.0
    
    if args.resume:
        print(f"从 {args.resume} 恢复训练...")
        checkpoint = torch.load(args.resume, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        best_val_acc = checkpoint.get('best_val_acc', 0.0)
        print(f"恢复训练: epoch {start_epoch}, best_val_acc: {best_val_acc:.2f}%")
    
    # 训练循环
    print(f"\n开始训练 {args.task} 模型...")
    print(f"训练集: {len(train_dataset)} 张图像")
    print(f"验证集: {len(val_dataset)} 张图像")
    print(f"类别数: {num_classes}")
    print(f"训练轮数: {args.epochs}")
    print(f"批次大小: {args.batch_size}")
    print(f"学习率: {args.lr}\n")
    
    for epoch in range(start_epoch, args.epochs):
        # 训练
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, device, epoch
        )
        
        # 验证
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        
        # 学习率调度
        scheduler.step(val_loss)
        
        print(f"\nEpoch {epoch+1}/{args.epochs}:")
        print(f"  Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        print(f"  Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        print(f"  LR: {optimizer.param_groups[0]['lr']:.6f}\n")
        
        # 保存最佳模型
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model_path = save_dir / f'{args.task}_best.pth'
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_val_acc': best_val_acc,
                'num_classes': num_classes,
            }, best_model_path)
            print(f"✓ 保存最佳模型: {best_model_path} (Val Acc: {val_acc:.2f}%)\n")
        
        # 定期保存检查点
        if (epoch + 1) % 10 == 0:
            checkpoint_path = save_dir / f'{args.task}_epoch_{epoch+1}.pth'
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_val_acc': best_val_acc,
                'num_classes': num_classes,
            }, checkpoint_path)
            print(f"✓ 保存检查点: {checkpoint_path}\n")
    
    print(f"\n训练完成！最佳验证准确率: {best_val_acc:.2f}%")
    print(f"最佳模型保存在: {save_dir / f'{args.task}_best.pth'}")


if __name__ == '__main__':
    main()


