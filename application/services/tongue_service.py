"""舌象分析业务服务

本模块负责处理“上传舌头图片 → 落盘 → 调用 YOLO + SAM + ResNet 模型 →
将分析结果写回数据库”的完整流程，是整个舌诊链路的核心业务层。

对应关系（类比 Java 项目）：
- 这里是 TongueService（业务逻辑）
- application/net/predict.py 是底层 AI 推理引擎
- application/orm/crud/tongue_analysis.py 是 DAO 层

外部只需要调用 analyse_tongue_image，即可拿到 TongueFeatures 结构体，
不用关心内部具体怎么调用模型和轮询数据库。
"""

import os
import time
from dataclasses import dataclass
from datetime import datetime
from tempfile import SpooledTemporaryFile
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from application.config import Settings
from application.net.predict import TonguePredictor
from application.orm import (
    write_event,
    write_result,
    get_record_by_location,
    get_result,
)


@dataclass
class TongueFeatures:
    code: int
    tongue_color: Optional[int]
    coating_color: Optional[int]
    tongue_thickness: Optional[int]
    rot_greasy: Optional[int]


def save_upload_to_disk(file_data: UploadFile) -> str:
    """
    将前端上传的图片保存到磁盘，返回数据库中使用的相对路径。
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(file_data.filename)[1]
    filename = f"{timestamp}{file_extension}"

    file_location = f"{Settings.IMG_PATH}/{filename}"
    os.makedirs(os.path.dirname(file_location), exist_ok=True)

    contents = file_data.file.read()
    with open(file_location, "wb") as f:
        f.write(contents)

    # 数据库中保存的相对路径
    img_db_path = f"{Settings.IMG_DB_PATH}/{filename}"
    return img_db_path


def analyse_tongue_image(img_file: UploadFile, user_id: int, db: Session) -> TongueFeatures:
    """
    封装舌象分析的完整流程：
    - 写入 TongueAnalysis 事件(state=0)
    - 将任务提交给 TonguePredictor 队列
    - 轮询数据库状态，直到分析结束
    - 返回 TongueFeatures 结构体
    """
    img_db_path = save_upload_to_disk(img_file)

    # 1. 记录事件
    code = write_event(user_id=user_id, img_src=img_db_path, state=0, db=db)
    if code != 0:
        return TongueFeatures(
            code=code,
            tongue_color=None,
            coating_color=None,
            tongue_thickness=None,
            rot_greasy=None,
        )

    # 2. 提交到 TonguePredictor
    record = get_record_by_location(img_db_path, db=db)

    def _analysis(img: SpooledTemporaryFile, record_id: int):
        predictor = TonguePredictor()
        predictor.predict(img=img, record_id=record_id, fun=write_result)

    # 这里直接复用 UploadFile 内部的 file 对象
    _analysis(img=img_file.file, record_id=record.id)

    # 3. 轮询等待结果
    while True:
        result_obj = get_result(img_db_path, db=db)
        if result_obj.state != 0:
            break
        time.sleep(1)

    result_obj = get_result(img_db_path, db=db)

    if result_obj.state != 1:
        # 图片有问题或者分析失败，直接返回错误码
        return TongueFeatures(
            code=result_obj.state,
            tongue_color=None,
            coating_color=None,
            tongue_thickness=None,
            rot_greasy=None,
        )

    return TongueFeatures(
        code=0,
        tongue_color=result_obj.tongue_color,
        coating_color=result_obj.coating_color,
        tongue_thickness=result_obj.tongue_thickness,
        rot_greasy=result_obj.rot_greasy,
    )


