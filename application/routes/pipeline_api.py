"""
Pipeline 中间结果可视化 API

提供接口让前端查询舌象分析的中间步骤结果图片和特征数据。
完全不改动原有的分析逻辑，只读取 predict.py 保存的 pipeline 产物。
"""

import json
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

# pipeline 图片存放目录
PIPELINE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend", "public", "pipeline"
)

router_pipeline = APIRouter()

class PipelineStep(BaseModel):
    step_name: str       # original / yolo / sam / crop / features
    image_url: Optional[str] = None
    description: Optional[str] = None

class PipelineData(BaseModel):
    record_id: int
    steps: List[PipelineStep]
    features: Optional[dict] = None

@router_pipeline.get("/pipeline/{record_id}", response_model=PipelineData)
async def get_pipeline(record_id: int):
    """获取指定 record_id 的 pipeline 中间结果"""
    meta_path = os.path.join(PIPELINE_DIR, f"{record_id}_meta.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail=f"Pipeline data not found for record {record_id}")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    steps = []
    step_info = {
        "original":   {"desc": "① 原始上传图片", "img": True},
        "yolo":       {"desc": "② YOLOv5 舌体定位（目标检测 + 置信度）", "img": True},
        "sam":        {"desc": "③ SAM 精细分割（掩码 + 边界轮廓）", "img": True},
        "crop":       {"desc": "④ 裁剪后的舌体区域（送入 ResNet 分类）", "img": True},
        "features":   {"desc": "⑤ 四维特征分类结果", "img": False},
    }

    for step_name in meta.get("steps", []):
        info = step_info.get(step_name, {"desc": step_name, "img": True})
        step = PipelineStep(
            step_name=step_name,
            description=info["desc"],
            image_url=f"/pipeline/{record_id}_{step_name}.jpg" if info["img"] else None
        )
        steps.append(step)

    return PipelineData(
        record_id=record_id,
        steps=steps,
        features=meta.get("features")
    )
