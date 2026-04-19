"""
SE: Squeeze-and-Excitation Network

论文: "Squeeze-and-Excitation Networks" (CVPR 2018)
实现: 轻量级通道注意力机制
"""

import torch
import torch.nn as nn


class SE(nn.Module):
    """SE (Squeeze-and-Excitation) 注意力模块
    
    通过全局平均池化和两个全连接层，学习通道间的重要性
    
    Args:
        in_planes: 输入通道数
        ratio: 压缩比例（默认16）
    """
    def __init__(self, in_planes, ratio=16):
        super(SE, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(in_planes, in_planes // ratio, bias=False),
            nn.ReLU(),
            nn.Linear(in_planes // ratio, in_planes, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x):
        b, c, _, _ = x.size()
        # Squeeze: 全局平均池化
        y = self.avg_pool(x).view(b, c)
        # Excitation: 学习通道权重
        y = self.fc(y).view(b, c, 1, 1)
        # Scale: 应用权重
        return x * y



