"""舌象分析与对话相关的 HTTP 接口（Controller 层）

本模块对应 Java 项目中的 Controller：
- 提供 /api/model 下的所有接口（在 application/routes/__init__.py 中挂载前缀）
- 自身不直接处理复杂业务，统一委托给 services 层：
  - application.services.tongue_service 负责舌象分析流程
  - application.services.chat_service 负责会话管理与调用 LLM

当前暴露的主要接口：
- POST /api/model/session         上传舌头图片并启动新的诊断会话（首条 AI 回答）
- POST /api/model/session/{id}    在已有会话中继续对话
- GET  /api/model/record/{id}     获取某个会话的历史聊天记录
- GET  /api/model/session         获取当前用户所有会话 ID 列表
"""

from fastapi import APIRouter, Depends, UploadFile, Form, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..core import get_current_user
from ..models import schemas
from ..orm.database import get_db
from ..config import settings
from ..services import (
    TongueFeatures,
    analyse_tongue_image,
    create_session_with_first_message,
    stream_first_answer,
    append_user_message_and_stream_answer,
    get_session_records,
    get_session_id_list,
)

router_tongue_analysis = APIRouter()

feature_map = {
    "Color of the tongue": {
        0: "Pale white tongue",
        1: "Light red tongue",
        2: "Red tongue",
        3: "Crimson tongue",
        4: "Bluish-purple tongue"
    },
    "Color of the tongue coating": {
        0: "White coating",
        1: "Yellow tongue coating",
        2: "Gray-black tongue coating"
    },
    "Thickness of the tongue": {
        0: "Thin",
        1: "Thick"
    },
    "Decay and putrefaction of the tongue": {
        0: "Putrefaction",
        1: "decay"
    }
}

def format_tongue_features(tongue_color,
                           coating_color,
                           tongue_thickness,
                           rot_greasy):
    try:
        features = [
            f"Color of the tongue: {feature_map['Color of the tongue'][tongue_color]}",
            f"Color of the tongue coating: {feature_map['Color of the tongue coating'][coating_color]}",
            f"Thickness of the tongue: {feature_map['Thickness of the tongue'][tongue_thickness]}",
            f"Decay and putrefaction of the tongue: {feature_map['Decay and putrefaction of the tongue'][rot_greasy]}"
        ]
        return "，".join(features)
    except KeyError as e:
        missing_key = int(str(e).split("'")[1])
        return f"错误：检测到无效特征值 {missing_key}，请检查输入范围"

# def format_tongue_features(tongue_color,
#                            coating_color,
#                            tongue_thickness,
#                            rot_greasy):
#     try:
#         features = [
#             f"Color of the tongue: {feature_map['Color of the tongue'][tongue_color]}",
#             f"Color of the tongue coating: {feature_map['Color of the tongue coating'][coating_color]}",
#             f"Thickness of the tongue: {feature_map['Thickness of the tongue'][tongue_thickness]}",
#             f"Decay and putrefaction of the tongue: {feature_map['Decay and putrefaction of the tongue'][rot_greasy]}"
#         ]
#         return "，".join(features)
#     except KeyError as e:
#         # --- 修复开始 ---
#         # 直接使用 str(e) 获取错误的键值，不需要 split
#         return f"错误：检测到无效特征值 {e}，请检查模型输出是否在 feature_map 范围内"
#         # --- 修复结束 ---
#     except Exception as e:
#         # 增加一个通用的错误捕获，防止其他情况崩溃
#         print(f"特征格式化未知错误: {e}")
#         return "特征解析失败"

class UserInput(BaseModel):
    input: str

@router_tongue_analysis.post('/session/{sessionId}')
async def upload(sessionId: int,
                 user_input: UserInput,
                 user: schemas.UserBase = Depends(get_current_user),
                 db: Session = Depends(get_db),
                 ):
    if not user:
        return schemas.BaseModel(
            code=101,
            message="can not find user",
            data=None
        )
    # 交给 chat_service 处理追加消息 + 调用 LLM
    return append_user_message_and_stream_answer(
        user_id=user.id,
        session_id=sessionId,
        user_input=user_input.input,
        db=db,
    )


class inputPicture(BaseModel):
    file_data: UploadFile
    user_input: str
    name: str

@router_tongue_analysis.post('/session')
async def upload(file_data: UploadFile = File(...),
                user_input: str = Form(...),
                name: str = Form(...),
                 user: schemas.UserBase = Depends(get_current_user),
                 db: Session = Depends(get_db)
                 ):
    if not user:
        return schemas.BaseModel(
            code=101,
            message="can not find user",
            data=None
        )

    # 舌象分析统一交给 service
    features: TongueFeatures = analyse_tongue_image(
        img_file=file_data,
        user_id=user.id,
        db=db,
    )

    if features.code != 0:
        return schemas.BaseModel(
            code=features.code,
            message="图片有问题",
            data=None,
        )

    feature_text = format_tongue_features(
        features.tongue_color,
        features.coating_color,
        features.tongue_thickness,
        features.rot_greasy,
    )

    # 创建会话并写入第一条用户消息
    session_new_id = create_session_with_first_message(
        user_id=user.id,
        name=name,
        first_message=user_input,
        db=db,
    )

    # 调用 LLM 流式返回首条回答
    return stream_first_answer(
        user_input=user_input,
        feature_text=feature_text,
        user_id=user.id,
        session_id=session_new_id,
        db=db,
    )

@router_tongue_analysis.get("/record/{sessionid}", response_model=schemas.ChatSessionRecordsResponse)
async def get_chat_records_by_session(sessionid: int,
                                      db: Session = Depends(get_db),
                                      user: schemas.UserBase = Depends(get_current_user)
                                      ):
    if not user:
        return schemas.ChatSessionRecordsResponse(
            code=101,
            message="can not find user",
            data={"records": []}
        )
    return get_session_records(user_id=user.id, session_id=sessionid, db=db)

@router_tongue_analysis.get("/session", response_model=schemas.SessionIdResponse)
async def get_chat_records_id(db: Session = Depends(get_db),
                              user: schemas.UserBase = Depends(get_current_user)):
    if not user:
        return schemas.SessionIdResponse(
            code=101,
            message="can not find user",
            data=[]
        )
    return get_session_id_list(user_id=user.id, db=db)
