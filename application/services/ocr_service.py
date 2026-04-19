"""OCR（文字识别）服务

本模块为“报告解读 / 药盒识别”提供 OCR 能力：
- 输入：图片 bytes（或 UploadFile）
- 输出：识别出的文本（按行拼接）

实现选择：
- 使用 easyocr（纯 Python，支持中文，部署相对简单）
- 懒加载 Reader，避免应用启动时加载模型导致慢启动

lang_list=['ch_sim','en'] 时，EasyOCR 使用检测 craft_mlt_25k.pth + 识别 zh_sim_g2.pth（gen2），
不是旧的 chinese_sim.pth + latin.pth。请用项目内 scripts/download_easyocr_models.py 下载正确文件。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from application.config import settings


class OcrUnavailableError(Exception):
    """EasyOCR 无法完成初始化（常见原因：模型下载超时或本地缺少模型文件）。"""


_reader = None

# 与当前 easyocr 1.7+ 中 Reader(['ch_sim','en'], detect_network='craft') 所需文件一致
_EASYOCR_REQUIRED_FILES = ("craft_mlt_25k.pth", "zh_sim_g2.pth")


def easyocr_model_dir() -> Path:
    base = os.environ.get("EASYOCR_MODULE_PATH") or os.environ.get("MODULE_PATH")
    if base:
        return Path(base) / "model"
    return Path.home() / ".EasyOCR" / "model"


def _check_local_easyocr_models() -> None:
    d = easyocr_model_dir()
    missing = [f for f in _EASYOCR_REQUIRED_FILES if not (d / f).is_file()]
    if not missing:
        return
    raise OcrUnavailableError(
        f"本地缺少 EasyOCR 模型文件（目录 {d}）：{', '.join(missing)}。"
        f"请重新运行「下载EasyOCR模型.bat」或 "
        f"`python scripts/download_easyocr_models.py`（需含 **zh_sim_g2.pth**，不是旧的 chinese_sim）。"
        f"完成后将 config 中 EASYOCR_DOWNLOAD_ENABLED 保持为 False 即可离线使用。"
    )


def _get_reader():
    global _reader
    if _reader is None:
        import urllib.error

        import easyocr

        download = getattr(settings, "EASYOCR_DOWNLOAD_ENABLED", False)
        model_dir = easyocr_model_dir()

        if not download:
            _check_local_easyocr_models()

        try:
            _reader = easyocr.Reader(
                ["ch_sim", "en"],
                gpu=False,
                model_storage_directory=str(model_dir),
                download_enabled=download,
                verbose=False,
            )
        except FileNotFoundError as e:
            raise OcrUnavailableError(
                f"OCR 模型文件不完整：{e}。"
                "请运行 `python scripts/download_easyocr_models.py` 下载 craft + zh_sim_g2。"
            ) from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise OcrUnavailableError(
                "OCR 尝试联网下载模型失败（未走系统代理时常见）。"
                "请用代理执行一次 `python scripts/download_easyocr_models.py --proxy http://127.0.0.1:7890`，"
                "然后将 EASYOCR_DOWNLOAD_ENABLED 设为 False 后重启后端。"
            ) from e
        except Exception as e:
            raise OcrUnavailableError(
                f"OCR 初始化失败：{type(e).__name__}: {e}"
            ) from e
    return _reader


def ocr_image_bytes(image_bytes: bytes) -> str:
    """
    对图片进行 OCR，返回识别文本。
    """
    reader = _get_reader()
    lines: List[str] = reader.readtext(image_bytes, detail=0, paragraph=True)
    cleaned = [x.strip() for x in lines if str(x).strip()]
    return "\n".join(cleaned)
