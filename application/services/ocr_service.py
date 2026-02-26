"""OCR（文字识别）服务

本模块为“报告解读 / 药盒识别”提供 OCR 能力：
- 输入：图片 bytes（或 UploadFile）
- 输出：识别出的文本（按行拼接）

实现选择：
- 使用 easyocr（纯 Python，支持中文，部署相对简单）
- 懒加载 Reader，避免应用启动时加载模型导致慢启动
"""

from __future__ import annotations

from typing import List, Optional


_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        import easyocr
        # 中文 + 英文
        _reader = easyocr.Reader(["ch_sim", "en"], gpu=False)
    return _reader


def ocr_image_bytes(image_bytes: bytes) -> str:
    """
    对图片进行 OCR，返回识别文本。
    """
    reader = _get_reader()
    # detail=0 仅返回文本；paragraph=True 会做简单段落合并
    lines: List[str] = reader.readtext(image_bytes, detail=0, paragraph=True)
    # 去掉空行
    cleaned = [x.strip() for x in lines if str(x).strip()]
    return "\n".join(cleaned)


