"""扩展功能接口（报告解读 / 药盒识别）

该模块挂载到 /api/extra 前缀下，供前端 Examination 子菜单使用。

接口设计：
- POST /api/extra/report/text      文本报告解读（流式返回）
- POST /api/extra/report/image     图片报告解读（OCR + LLM，流式返回）
- POST /api/extra/drugbox/text     药盒/说明书文本解读（流式返回）
- POST /api/extra/drugbox/image    药盒图片识别（OCR + LLM，流式返回）
"""

from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from application.core import get_current_user
from application.models import schemas
from application.orm.database import get_db
from application.services.extra_service import (
    explain_report_text,
    explain_report_image,
    explain_drugbox_text,
    explain_drugbox_image,
)


router_extra = APIRouter()


class ReportTextReq(BaseModel):
    text: str
    title: str | None = None


class DrugTextReq(BaseModel):
    text: str
    question: str | None = ""
    title: str | None = None


class ReportImageReq(BaseModel):
    question: str | None = ""
    title: str | None = None


@router_extra.post("/report/text")
def report_text(
    req: ReportTextReq,
    user: schemas.UserBase = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user:
        return schemas.BaseResponse(code=101, message="can not find user", data=None)
    return explain_report_text(db=db, user_id=user.id, report_text=req.text, title=req.title)


@router_extra.post("/report/image")
def report_image(
    file_data: UploadFile = File(...),
    question: str = "",
    title: str = "",
    user: schemas.UserBase = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user:
        return schemas.BaseResponse(code=101, message="can not find user", data=None)
    return explain_report_image(
        db=db,
        user_id=user.id,
        image_file=file_data,
        question=question or "",
        title=title or None,
    )


@router_extra.post("/drugbox/text")
def drugbox_text(
    req: DrugTextReq,
    user: schemas.UserBase = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user:
        return schemas.BaseResponse(code=101, message="can not find user", data=None)
    return explain_drugbox_text(
        db=db,
        user_id=user.id,
        drug_text=req.text,
        question=req.question or "",
        title=req.title,
    )


@router_extra.post("/drugbox/image")
def drugbox_image(
    file_data: UploadFile = File(...),
    question: str = "",
    title: str = "",
    user: schemas.UserBase = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user:
        return schemas.BaseResponse(code=101, message="can not find user", data=None)
    return explain_drugbox_image(
        db=db,
        user_id=user.id,
        image_file=file_data,
        question=question or "",
        title=title or None,
    )


