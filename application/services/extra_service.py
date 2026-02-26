"""扩展功能业务服务（报告解读 / 药盒识别）

本模块将“场景化 Prompt + OCR + LLM 流式返回 + 会话落库”组合成可复用的业务流程。

设计目标（便于扩展）：
- 每个场景一个 system_prompt（见 application.config.config.Settings）
- 输入可以是纯文本，也可以是图片 OCR 文本 + 用户问题
- 输出统一走 NDJSON 流式 token，前端可实时显示
- 历史记录复用现有 ChatSession / ChatRecord，便于统一查看与复盘
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from application.config import settings
from application.orm import create_new_session, create_new_chat_records
from application.routes.ollama_used import OllamaStreamChatter
from application.services.ocr_service import ocr_image_bytes


@dataclass
class ExtraSession:
    session_id: int
    title: str


def _new_session(db: Session, user_id: int, title: str, first_user_message: str) -> ExtraSession:
    """
    创建 ChatSession 并写入第一条用户消息（role=1）。
    """
    session = create_new_session(db=db, ID=user_id, tittle=title)
    create_new_chat_records(db=db, session_id=session.id, content=first_user_message, role=1)
    return ExtraSession(session_id=session.id, title=title)


def _stream_llm_with_prompt(db: Session, session_id: int, system_prompt: str, user_content: str):
    """
    根据 system_prompt + user_content 走通用 messages 流式接口。
    """
    bot = OllamaStreamChatter(system_prompt=system_prompt)
    # 复用 bot.messages（初始化时已包含 system）
    messages = bot.messages + [{"role": "user", "content": user_content}]
    return bot.chat_stream_messages(messages=messages, db=db, session_id=session_id)


def explain_report_text(db: Session, user_id: int, report_text: str, title: Optional[str] = None):
    """
    报告解读：纯文本输入。
    """
    if not title:
        title = f"[Report] {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    session = _new_session(db=db, user_id=user_id, title=title, first_user_message=report_text)
    return _stream_llm_with_prompt(
        db=db,
        session_id=session.session_id,
        system_prompt=settings.REPORT_SYSTEM_PROMPT,
        user_content=report_text,
    )


def explain_report_image(db: Session, user_id: int, image_file: UploadFile, question: str = "", title: Optional[str] = None):
    """
    报告解读：图片输入 -> OCR -> LLM。
    """
    image_bytes = image_file.file.read()
    ocr_text = ocr_image_bytes(image_bytes)

    user_content = f"以下是报告OCR文本：\n{ocr_text}\n"
    if question.strip():
        user_content += f"\n用户问题：{question.strip()}\n"

    if not title:
        title = f"[Report] {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    session = _new_session(db=db, user_id=user_id, title=title, first_user_message=user_content)
    return _stream_llm_with_prompt(
        db=db,
        session_id=session.session_id,
        system_prompt=settings.REPORT_SYSTEM_PROMPT,
        user_content=user_content,
    )


def explain_drugbox_image(db: Session, user_id: int, image_file: UploadFile, question: str = "", title: Optional[str] = None):
    """
    药盒识别：图片输入 -> OCR -> LLM。
    """
    image_bytes = image_file.file.read()
    ocr_text = ocr_image_bytes(image_bytes)

    user_content = f"以下是药盒/说明书OCR文本：\n{ocr_text}\n"
    if question.strip():
        user_content += f"\n用户问题：{question.strip()}\n"

    if not title:
        title = f"[DrugBox] {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    session = _new_session(db=db, user_id=user_id, title=title, first_user_message=user_content)
    return _stream_llm_with_prompt(
        db=db,
        session_id=session.session_id,
        system_prompt=settings.DRUGBOX_SYSTEM_PROMPT,
        user_content=user_content,
    )


def explain_drugbox_text(db: Session, user_id: int, drug_text: str, question: str = "", title: Optional[str] = None):
    """
    药盒识别：纯文本输入（用户可手动粘贴说明书/药盒文字）。
    """
    user_content = f"以下是用户提供的药盒/说明书文本：\n{drug_text}\n"
    if question.strip():
        user_content += f"\n用户问题：{question.strip()}\n"

    if not title:
        title = f"[DrugBox] {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    session = _new_session(db=db, user_id=user_id, title=title, first_user_message=user_content)
    return _stream_llm_with_prompt(
        db=db,
        session_id=session.session_id,
        system_prompt=settings.DRUGBOX_SYSTEM_PROMPT,
        user_content=user_content,
    )


