"""对话与会话管理业务服务

本模块封装了与聊天记录相关的业务逻辑，包括：
- 创建新的 ChatSession，并写入第一条用户消息
- 调用 LLM（通过 OllamaStreamChatter）获得首条或追加回答（流式）
- 查询某个会话下的全部 ChatRecord
- 查询当前用户的所有会话 ID 列表

对应关系（类比 Java 项目）：
- 这里是 ChatService
- application/routes/ollama_used.py 是 LLM 客户端实现
- application/orm/crud/chat_record.py 是 ChatSession/ChatRecord 的 DAO 层
"""

from typing import List, Dict, Any

from sqlalchemy.orm import Session

from application.models import schemas
from application.orm import (
    get_chat_record,
    get_all_chat_id,
    create_new_session,
    create_new_chat_records,
)
from application.routes.ollama_used import OllamaStreamChatter
from application.config import settings


def create_session_with_first_message(
    user_id: int,
    name: str,
    first_message: str,
    db: Session,
) -> int:
    """
    创建新的对话 Session，并写入第一条用户消息，返回 session_id。
    """
    new_session = create_new_session(ID=user_id, db=db, tittle=name)
    session_new_id = new_session.id
    create_new_chat_records(db=db, content=first_message, session_id=session_new_id, role=1)
    return session_new_id


def stream_first_answer(
    user_input: str,
    feature_text: str,
    user_id: int,
    session_id: int,
    db: Session,
):
    """
    首次上传图片后，调用 LLM 生成第一条回答的流式响应。
    """
    bot = OllamaStreamChatter(system_prompt=settings.SYSTEM_PROMPT)
    return bot.chat_stream_first(user_input, feature_text, user_id, db, session_id)


def append_user_message_and_stream_answer(
    user_id: int,
    session_id: int,
    user_input: str,
    db: Session,
):
    """
    在已有会话中追加一条用户消息，并基于完整上下文调用 LLM，返回流式响应。
    """
    # 先把新消息写入 ChatRecord
    create_new_chat_records(db=db, content=user_input, session_id=session_id, role=1)

    bot = OllamaStreamChatter(system_prompt=settings.SYSTEM_PROMPT)
    return bot.chat_stream_add(user_id, db, session_id)


def get_session_records(user_id: int, session_id: int, db: Session) -> schemas.ChatSessionRecordsResponse:
    """
    获取某个会话的所有聊天记录。
    """
    chat_record = get_chat_record(ID=user_id, sessionid=session_id, db=db)
    if chat_record == 102 or chat_record == 103:
        return schemas.ChatSessionRecordsResponse(
            code=chat_record,
            message="operation failed",
            data={"records": []},
        )

    records: List[schemas.ChatRecordResponse] = []
    for record in chat_record:
        records.append(
            schemas.ChatRecordResponse(
                content=record.content,
                create_at=record.create_at,
                role=record.role,
            )
        )

    data_temp: Dict[str, Any] = {"records": records}
    return schemas.ChatSessionRecordsResponse(
        code=0,
        message="operation success",
        data=data_temp,
    )


def get_session_id_list(user_id: int, db: Session) -> schemas.SessionIdResponse:
    """
    获取当前用户的所有会话 ID 列表。
    """
    chat_id_records = get_all_chat_id(ID=user_id, db=db)
    data_temp: List[schemas.SessionId] = []
    for record in chat_id_records:
        data_temp.append(
            schemas.SessionId(
                session_id=record.id,
                name=record.tittle,
            )
        )

    return schemas.SessionIdResponse(
        code=0,
        message="operation success",
        data=data_temp,
    )


