"""
预下载 EasyOCR 所需模型到用户目录 ~/.EasyOCR/model，避免首次请求时在服务进程内用 urllib 下载
（urllib 往往不走 Clash 等「系统代理」，易超时）。

用法（在项目根目录、已激活的 conda 环境中）:
  # 若已设置系统环境变量 HTTP_PROXY/HTTPS_PROXY，可直接:
  python scripts/download_easyocr_models.py

  # 或显式指定本地代理（Clash / v2rayN 常见端口 7890、10809 等）:
  python scripts/download_easyocr_models.py --proxy http://127.0.0.1:7890

下载完成后，建议在 application/config/config.py 中将 EASYOCR_DOWNLOAD_ENABLED 设为 False，
避免服务启动后仍尝试联网校验/下载。

注意：easyocr.Reader(['ch_sim','en']) 实际使用的是 **gen2** 单文件 zh_sim_g2.pth，
不是旧版 chinese_sim.pth + latin.pth；若只下了后者，仍会提示下载识别模型。
"""

from __future__ import annotations

import argparse
import os
import sys
import zipfile
from pathlib import Path

import requests

# 与 easyocr.easyocr.Reader(lang_list=['ch_sim','en'], detect_network='craft') 一致：
# - 检测：craft_mlt_25k.pth
# - 识别：ch_sim + en 走 recognition_models['gen2']['zh_sim_g2'] -> zh_sim_g2.pth
MODELS = [
    {
        "url": "https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip",
        "zip_name": "craft_mlt_25k.zip",
        "check_file": "craft_mlt_25k.pth",
    },
    {
        "url": "https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/zh_sim_g2.zip",
        "zip_name": "zh_sim_g2.zip",
        "check_file": "zh_sim_g2.pth",
    },
]


def model_dir() -> Path:
    base = os.environ.get("EASYOCR_MODULE_PATH") or os.environ.get("MODULE_PATH")
    if base:
        return Path(base) / "model"
    return Path.home() / ".EasyOCR" / "model"


def download_one(session: requests.Session, dest_dir: Path, url: str, zip_name: str) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / zip_name
    print(f"下载: {url}")
    with session.get(url, stream=True, timeout=(30, 600)) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
        done = 0
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        pct = min(100, int(done * 100 / total))
                        print(f"\r  进度 {pct}%", end="", flush=True)
    print(f"\n  已保存 {zip_path}")
    print(f"  解压到 {dest_dir} ...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)
    zip_path.unlink(missing_ok=True)
    print("  完成。")


def main() -> int:
    parser = argparse.ArgumentParser(description="下载 EasyOCR 模型（支持 HTTP 代理）")
    parser.add_argument(
        "--proxy",
        default=None,
        help="例如 http://127.0.0.1:7890；会写入本次进程的 HTTP_PROXY/HTTPS_PROXY",
    )
    args = parser.parse_args()
    if args.proxy:
        os.environ["HTTP_PROXY"] = args.proxy
        os.environ["HTTPS_PROXY"] = args.proxy
        print(f"已设置代理: {args.proxy}")

    dest = model_dir()
    print(f"目标目录: {dest}\n")

    session = requests.Session()
    session.trust_env = True

    for item in MODELS:
        marker = dest / item["check_file"]
        if marker.is_file() and marker.stat().st_size > 0:
            print(f"已存在 {item['check_file']}，跳过。")
            continue
        try:
            download_one(session, dest, item["url"], item["zip_name"])
        except requests.RequestException as e:
            print(f"\n失败: {e}", file=sys.stderr)
            print(
                "\n建议：1) 确认代理端口与 Clash「允许局域网」一致；"
                "2) 尝试浏览器能否打开上述 URL；"
                "3) 用手机热点完成下载。",
                file=sys.stderr,
            )
            return 1

    print("\n全部模型就绪。请重启后端再试「报告解读 / 药盒识别」上传图片。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
