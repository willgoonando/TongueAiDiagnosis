"""
性能测试脚本（与论文表5-y 指标口径一致）

用法（在项目根目录 d:\\TD 下）:
  conda activate AiDiagnosis-3.12   # 或你的环境
  python scripts/benchmark_performance.py
  python scripts/benchmark_performance.py --image D:\\path\\to\\tongue.jpg
  python scripts/benchmark_performance.py --runs 5 --ollama-runs 3

说明:
- YOLO+SAM+ResNet：直接调用 TonguePredictor.__predict（需本地权重 application/net/weights/）
- LLM：请求 Ollama /api/chat 流式接口，统计首包延迟与总耗时
- 端到端：上传→首 token 需登录后调 /api/model/session，本脚本用「推理耗时 + LLM 首 token」近似，或你自行用浏览器/Apifox 填表

结果写入 scripts/performance_results.json，并打印 Markdown 表，便于粘贴进论文。
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# 项目根
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def time_cv_pipeline(image_path: Path, runs: int) -> dict:
    """单次完整调用 TonguePredictor._TonguePredictor__predict，不经过 HTTP/队列/数据库。"""
    from tempfile import SpooledTemporaryFile

    from application.net.predict import TonguePredictor

    def noop_write(**kwargs):
        pass

    data = image_path.read_bytes()
    # 预热 1 次：单例首次加载 YOLO/SAM/ResNet 耗时不计入“稳态推理”统计
    _tp = TonguePredictor()
    _tmp = SpooledTemporaryFile(max_size=50 * 1024 * 1024)
    _tmp.write(data)
    _tmp.seek(0)
    try:
        _tp._TonguePredictor__predict(_tmp, 0, noop_write)  # noqa: SLF001
    except Exception:
        pass
    finally:
        _tmp.close()

    times = []
    err = None
    for i in range(runs):
        tp = TonguePredictor()
        tmp = SpooledTemporaryFile(max_size=50 * 1024 * 1024)
        tmp.write(data)
        tmp.seek(0)
        t0 = time.perf_counter()
        try:
            tp._TonguePredictor__predict(tmp, 0, noop_write)  # noqa: SLF001
        except Exception as e:
            err = str(e)
            break
        finally:
            tmp.close()
        t1 = time.perf_counter()
        times.append(t1 - t0)
    if err:
        return {"error": err, "times_s": times}
    return {
        "times_s": times,
        "avg_s": sum(times) / len(times),
        "max_s": max(times),
        "min_s": min(times),
        "runs": len(times),
    }


def _load_settings_class():
    """仅执行 application/config/config.py，不 import application 包（避免依赖 FastAPI 等）。"""
    import importlib.util

    path = ROOT / "application" / "config" / "config.py"
    spec = importlib.util.spec_from_file_location("td_settings_only", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.Settings


def time_ollama_stream(runs: int) -> dict:
    import requests

    Settings = _load_settings_class()
    url = os.environ.get("OLLAMA_PATH", Settings.OLLAMA_PATH)
    model = os.environ.get("LLM_NAME", Settings.LLM_NAME)
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "请用一句话回答：1+1等于几？"}],
        "stream": True,
    }
    if getattr(Settings, "OLLAMA_SEND_THINK_FIELD", True):
        payload["think"] = getattr(Settings, "OLLAMA_THINK", False)
    np = Settings.OLLAMA_NUM_PREDICT
    if np is not None:
        payload["options"] = {"num_predict": min(512, np)}

    first_token_s_list = []
    total_s_list = []

    for _ in range(runs):
        t_req = time.perf_counter()
        first_token_time = None
        try:
            r = requests.post(
                url,
                json=payload,
                stream=True,
                timeout=(30, 600),
            )
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=False):
                if not line:
                    continue
                import json as json_lib

                chunk = json_lib.loads(line.decode("utf-8"))
                msg = chunk.get("message") or {}
                piece = (msg.get("thinking") or "") + (msg.get("content") or "")
                if piece and first_token_time is None:
                    first_token_time = time.perf_counter()
                if chunk.get("done"):
                    break
        except Exception as e:
            return {"error": str(e), "url": url}

        t_end = time.perf_counter()
        first_token_s_list.append(
            (first_token_time - t_req) if first_token_time else (t_end - t_req)
        )
        total_s_list.append(t_end - t_req)

    return {
        "runs": runs,
        "first_token_avg_s": sum(first_token_s_list) / len(first_token_s_list),
        "first_token_max_s": max(first_token_s_list),
        "total_avg_s": sum(total_s_list) / len(total_s_list),
        "total_max_s": max(total_s_list),
        "model": model,
        "url": url,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--image",
        type=Path,
        default=None,
        help="舌象图片路径；不提供则跳过 YOLO+SAM+ResNet 测试",
    )
    parser.add_argument("--runs", type=int, default=5, help="CV 管线重复次数")
    parser.add_argument("--ollama-runs", type=int, default=3, help="Ollama 重复次数")
    parser.add_argument("--skip-ollama", action="store_true")
    parser.add_argument("--skip-cv", action="store_true")
    args = parser.parse_args()

    out: dict = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cwd": str(ROOT),
        "device_note": "TORCH_DEVICE 见 application/config/config.py",
    }

    if not args.skip_cv and args.image:
        if not args.image.is_file():
            print(f"图片不存在: {args.image}", file=sys.stderr)
            return 1
        print(f"运行 CV 管线测试（{args.runs} 次）…")
        out["cv_yolo_sam_resnet"] = time_cv_pipeline(args.image, args.runs)
        if out["cv_yolo_sam_resnet"].get("error"):
            print("CV 测试出错:", out["cv_yolo_sam_resnet"]["error"])
    elif not args.skip_cv and not args.image:
        out["cv_yolo_sam_resnet"] = {
            "skipped": True,
            "reason": "未传 --image，仓库内无默认舌象样本",
        }
        print("跳过 CV：请使用 python scripts/benchmark_performance.py --image <舌象.jpg>")

    if not args.skip_ollama:
        print(f"运行 Ollama 流式测试（{args.ollama_runs} 次）…")
        out["ollama_llm"] = time_ollama_stream(args.ollama_runs)
        if out["ollama_llm"].get("error"):
            print("Ollama 测试失败:", out["ollama_llm"]["error"])
    else:
        out["ollama_llm"] = {"skipped": True}

    out_path = ROOT / "scripts" / "performance_results.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已写入: {out_path}\n")

    # Markdown 表（论文表5-y）
    lines = [
        "| 指标项 | 测试次数 | 平均值（s） | 最大值（s） | 备注 |",
        "|--------|----------|-------------|-------------|------|",
    ]

    cv = out.get("cv_yolo_sam_resnet") or {}
    if cv.get("avg_s") is not None:
        lines.append(
            f"| YOLO+SAM+ResNet 推理耗时 | {cv.get('runs')} | {cv['avg_s']:.3f} | {cv['max_s']:.3f} | 脚本直连 TonguePredictor，不含 HTTP/队列/DB |"
        )
    else:
        lines.append(
            "| YOLO+SAM+ResNet 推理耗时 | — | — | — | 未测（请加 --image） |"
        )

    om = out.get("ollama_llm") or {}
    if om.get("first_token_avg_s") is not None:
        lines.append(
            f"| LLM 首 token 延迟 | {om.get('runs')} | {om['first_token_avg_s']:.3f} | {om['first_token_max_s']:.3f} | Ollama 流式，模型 {om.get('model')} |"
        )
        lines.append(
            f"| LLM 完整回答耗时 | {om.get('runs')} | {om['total_avg_s']:.3f} | {om['total_max_s']:.3f} | 同上 |"
        )
    elif not om.get("skipped"):
        lines.append("| LLM 首 token / 完整耗时 | — | — | — | Ollama 不可用或未启动 |")
    else:
        lines.append("| LLM 首 token / 完整耗时 | — | — | — | 已 --skip-ollama |")

    # 端到端近似：CV 平均 + LLM 首 token 平均（仅当两者都有）
    if cv.get("avg_s") is not None and om.get("first_token_avg_s") is not None:
        approx = cv["avg_s"] + om["first_token_avg_s"]
        lines.append(
            f"| 端到端近似（CV 平均 + LLM 首 token 平均） | 1 | {approx:.3f} | — | 非严格 HTTP 全链路；全链路请用浏览器测 |"
        )

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
