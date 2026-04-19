"""
ResNet50 分类模型训练脚本（已修复混淆矩阵累加bug与数据不平衡问题）

用于训练舌象分析的4个分类任务：
1. tongue_color（舌色）：5类
2. tongue_coat_color（苔色）：3类
3. thickness（厚度）：2类
4. rot_and_greasy（腐腻）：2类

使用方法：
    python train_resnet1.py --task thickness --data_path ./data --epochs 50 --batch_size 16 --device auto
"""

import argparse
import os
import time
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from PIL import Image
from tqdm import tqdm

from application.net.model.resnet import ResNet50


class TongueDataset(Dataset):
    """舌象分类数据集"""
    
    def __init__(self, root_dir, task_name, split='train', transform=None):
        self.root_dir = Path(root_dir)
        self.task_dir = self.root_dir / task_name / split
        self.transform = transform
        self.images = []
        self.labels = []
        
        class_dirs = sorted([d for d in self.task_dir.iterdir() if d.is_dir()])
        
        if len(class_dirs) == 0:
            raise ValueError(f"在 {self.task_dir} 中未找到类别文件夹！请检查数据集路径。")
        
        for class_idx, class_dir in enumerate(class_dirs):
            image_files = []
            for p in class_dir.iterdir():
                if p.is_file() and p.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    image_files.append(p)
            
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
        
        try:
            image = Image.open(img_path).convert('RGB')
        except Exception as e:
            print(f"加载图像失败 {img_path}: {e}")
            image = Image.new('RGB', (224, 224), color='black')
        
        if self.transform:
            image = self.transform(image)
        
        return image, label


def get_transforms(augment=True):
    if augment:
        train_transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.RandomCrop(224),
            transforms.RandomHorizontalFlip(p=0.5),
            # 【修复】降低ColorJitter的强度，因为舌象颜色（如苔色、舌色）非常敏感，避免过度失真
            transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.05),
            transforms.RandomRotation(degrees=15),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.29, 0.22, 0.23], std=[0.34, 0.27, 0.28])
        ])
    else:
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
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(dataloader, desc=f'Epoch {epoch} [Train]')
    for images, labels in pbar:
        images = images.to(device)
        labels = labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        loss.backward()
        
        # 【修复】加入梯度裁剪，防止Loss突然出现巨大的尖峰（梯度爆炸）
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
        
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


def validate(model, dataloader, criterion, device, return_preds=False):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    all_preds = []
    all_labels = []
    
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
            
            if return_preds:
                all_preds.extend(predicted.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
            
            pbar.set_postfix({
                'loss': f'{running_loss/total:.4f}',
                'acc': f'{100*correct/total:.2f}%'
            })
    
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100 * correct / total
    
    if return_preds:
        return epoch_loss, epoch_acc, all_preds, all_labels
    else:
        return epoch_loss, epoch_acc


def plot_training_curves(train_losses, val_losses, train_accs, val_accs, task, save_dir='results'):
    os.makedirs(save_dir, exist_ok=True)
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train Loss', linewidth=2)
    plt.plot(val_losses, label='Val Loss', linewidth=2)
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title(f'{task} Loss Curve')
    plt.legend()
    plt.grid(alpha=0.3)

    plt.subplot(1, 2, 2)
    plt.plot(train_accs, label='Train Acc', linewidth=2)
    plt.plot(val_accs, label='Val Acc', linewidth=2)
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.title(f'{task} Accuracy Curve')
    plt.legend()
    plt.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, f'{task}_curves.png'), dpi=300)
    plt.close()


def plot_confusion_matrix(y_true, y_pred, task, num_classes, save_dir='results'):
    os.makedirs(save_dir, exist_ok=True)
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=[f'class{i}' for i in range(num_classes)],
                yticklabels=[f'class{i}' for i in range(num_classes)])
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title(f'{task} Confusion Matrix')
    plt.savefig(os.path.join(save_dir, f'{task}_confusion_matrix.png'), dpi=300)
    plt.close()


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
    # 【修复】默认学习率从 0.001 降低到 0.0001，避免Loss震荡
    parser.add_argument('--lr', type=float, default=0.0001,
                        help='学习率 (default: 0.0001)')
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
    
    if args.device == 'auto':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(args.device)
    
    print(f"使用设备: {device}")
    
    task_classes = {
        'tongue_color': 5,
        'tongue_coat_color': 3,
        'thickness': 2,
        'rot_and_greasy': 2
    }
    num_classes = task_classes[args.task]
    
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
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

    # 【修复】自动计算类别权重以解决数据不平衡问题
    print("\n正在计算类别权重以应对数据不平衡...")
    class_counts = np.bincount(train_dataset.labels, minlength=num_classes)
    total_samples = len(train_dataset.labels)
    # 使用逆类别频率公式计算权重：总样本数 / (类别数 * 该类样本数)
    weights = total_samples / (num_classes * class_counts)
    class_weights = torch.FloatTensor(weights).to(device)
    print(f"训练集各类别样本数: {class_counts}")
    print(f"分配的类别权重 (Class Weights): {class_weights.cpu().numpy()}\n")
    
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
    
    model = ResNet50(num_classes=num_classes, if_se=True).to(device)
    
    # 【修复】将计算好的权重传入 CrossEntropyLoss
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5, verbose=True
    )
    
    start_epoch = 0
    best_val_acc = 0.0
    best_model_path = save_dir / f'{args.task}_best.pth'
    
    if args.resume:
        print(f"从 {args.resume} 恢复训练...")
        checkpoint = torch.load(args.resume, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        best_val_acc = checkpoint.get('best_val_acc', 0.0)
        print(f"恢复训练: epoch {start_epoch}, best_val_acc: {best_val_acc:.2f}%")
    
    print(f"\n开始训练 {args.task} 模型...")
    print(f"训练集: {len(train_dataset)} 张图像")
    print(f"验证集: {len(val_dataset)} 张图像")
    print(f"类别数: {num_classes}")
    print(f"训练轮数: {args.epochs}")
    print(f"批次大小: {args.batch_size}")
    print(f"初始学习率: {args.lr}\n")

    train_losses = []
    val_losses = []
    train_accs = []
    val_accs = []
    
    for epoch in range(start_epoch, args.epochs):
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device, epoch)
        val_loss, val_acc = validate(model, val_loader, criterion, device, return_preds=False)
        
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        train_accs.append(train_acc)
        val_accs.append(val_acc)
        
        scheduler.step(val_loss)
        
        print(f"\nEpoch {epoch+1}/{args.epochs}:")
        print(f"  Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        print(f"  Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        print(f"  LR: {optimizer.param_groups[0]['lr']:.6f}\n")
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_val_acc': best_val_acc,
                'num_classes': num_classes,
            }, best_model_path)
            print(f"✓ 保存最佳模型: {best_model_path} (Val Acc: {val_acc:.2f}%)\n")
        
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

    print("\n============== 用最佳模型进行最终验证 ==============")
    checkpoint = torch.load(best_model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    final_val_loss, final_val_acc, all_y_pred, all_y_true = validate(
        model, val_loader, criterion, device, return_preds=True
    )
    print(f"最佳模型验证准确率: {final_val_acc:.2f}%")
    print("==================================================\n")

    plot_training_curves(train_losses, val_losses, train_accs, val_accs, args.task)
    plot_confusion_matrix(all_y_true, all_y_pred, args.task, num_classes)
    
    print("\n============== 分类指标报告（最佳模型） ==============")
    print(classification_report(all_y_true, all_y_pred, digits=3))
    print("==================================================\n")
    
    print(f"\n训练完成！最佳验证准确率: {best_val_acc:.2f}%")
    print(f"最佳模型保存在: {best_model_path}")
    print(f"训练曲线图已保存到: results/{args.task}_curves.png")
    print(f"混淆矩阵图已保存到: results/{args.task}_confusion_matrix.png")

if __name__ == '__main__':
    main()