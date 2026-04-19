"""
ECA: Efficient Channel Attention

论文: "ECA-Net: Efficient Channel Attention for Deep Convolutional Neural Networks" (CVPR 2020)
实现: 高效的通道注意力，使用1D卷积替代全连接层
"""

import torch
import torch.nn as nn
import math


class ECA(nn.Module):
    """ECA (Efficient Channel Attention) 注意力模块
    
    使用1D卷积实现通道注意力，比SE更高效
    
    Args:
        in_planes: 输入通道数
        kernel_size: 1D卷积核大小（自动计算，默认None）
    """
    def __init__(self, in_planes, kernel_size=None):
        super(ECA, self).__init__()
        if kernel_size is None:
            # 自适应计算卷积核大小
            kernel_size = int(abs((math.log(in_planes, 2) + 1) / 2))
            kernel_size = kernel_size if kernel_size % 2 else kernel_size + 1
        
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.conv = nn.Conv1d(1, 1, kernel_size=kernel_size, padding=(kernel_size - 1) // 2, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # 全局平均池化
        y = self.avg_pool(x)
        # 1D卷积（通道维度）
        y = self.conv(y.squeeze(-1).transpose(-1, -2)).transpose(-1, -2).unsqueeze(-1)
        # 应用权重
        y = self.sigmoid(y)
        return x * y



