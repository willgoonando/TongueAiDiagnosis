"""
注意力机制模块

包含多种注意力机制实现：
- CBAM: Convolutional Block Attention Module
- SE: Squeeze-and-Excitation
- ECA: Efficient Channel Attention
"""

from .cbam import CBAM, ChannelAttention, SpatialAttention
from .se import SE
from .eca import ECA

__all__ = ['CBAM', 'ChannelAttention', 'SpatialAttention', 'SE', 'ECA']



