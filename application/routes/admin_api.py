"""后台管理 API（Controller 层）

本模块提供管理员专用的管理接口，供 admin/ 前端项目调用：
- 管理员校验（依赖 User.role 字段，role=1 为管理员）
- 用户管理：列表、新增、编辑、删除
- 舌诊记录管理：列表、删除
- 系统统计概览

安全策略：
- 所有接口先过 get_current_admin → 校验 JWT 且 role=1
- 非管理员返回 403
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import csv, io

from ..core.authentication import get_current_user
from ..orm.database import get_db
from ..models.models import User, TongueAnalysis, ChatSession, ChatRecord


router_admin = APIRouter(prefix="/admin", tags=["admin"])


def get_current_admin(
    user=Depends(get_current_user),
):
    """校验当前用户的 role 是否为管理员（1）"""
    if getattr(user, "role", 0) != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可操作")
    return user


# ────────────────────────────────────────
#  工具：CSV 导出辅助
# ────────────────────────────────────────

def csv_response(rows: list[dict], filename: str):
    """生成 CSV 下载响应，支持中文"""
    out = io.StringIO()
    out.write('\ufeff')  # BOM 让 Excel 识别 UTF-8
    if rows:
        writer = csv.DictWriter(out, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        writer = csv.writer(out)
        writer.writerow(["无数据"])
    out.seek(0)
    return StreamingResponse(
        iter([out.getvalue().encode('utf-8-sig')]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=export_{filename}"},
    )


# ────────────────────────────────────────
#  系统概览
# ────────────────────────────────────────

@router_admin.get("/stats")
def get_stats(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    """系统数据统计"""
    return {
        "code": 0,
        "data": {
            "user_count": db.query(func.count(User.id)).scalar(),
            "analysis_count": db.query(func.count(TongueAnalysis.id)).scalar(),
            "session_count": db.query(func.count(ChatSession.id)).scalar(),
            "chat_count": db.query(func.count(ChatRecord.id)).scalar(),
            "success_analysis": db.query(func.count(TongueAnalysis.id)).filter(TongueAnalysis.state == 1).scalar(),
            "failed_analysis": db.query(func.count(TongueAnalysis.id)).filter(TongueAnalysis.state >= 200).scalar(),
        }
    }


@router_admin.get("/stats/user-chats")
def get_user_chat_stats(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """各用户对话数统计（用于柱状图）"""
    rows = (
        db.query(User.id, User.email, func.count(ChatSession.id).label("count"))
        .outerjoin(ChatSession, ChatSession.user_id == User.id)
        .group_by(User.id)
        .order_by(func.count(ChatSession.id).desc())
        .all()
    )
    data = [{"email": r.email, "count": r.count} for r in rows]
    return {"code": 0, "data": data}


# ────────────────────────────────────────
#  舌象特征统计分析
# ────────────────────────────────────────

@router_admin.get("/analysis-stats")
def get_analysis_stats(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """舌象特征统计分析（仅统计成功记录 state=1）"""
    from sqlalchemy import func as f

    base = db.query(TongueAnalysis).filter(TongueAnalysis.state == 1)

    def _dist(col):
        return {r[0]: r[1] for r in base.with_entities(col, f.count(col)).group_by(col).all()}

    return {
        "code": 0,
        "data": {
            "total": base.count(),
            "tongue_color": _dist(TongueAnalysis.tongue_color),
            "coating_color": _dist(TongueAnalysis.coating_color),
            "thickness": _dist(TongueAnalysis.tongue_thickness),
            "rot_greasy": _dist(TongueAnalysis.rot_greasy),
        }
    }


# ────────────────────────────────────────
#  用户管理
# ────────────────────────────────────────

@router_admin.get("/users")
def list_users(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    export: bool = False,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """用户列表（分页 + 搜索邮箱），export=1 时导出全部（忽略分页）"""
    query = db.query(User)
    if keyword:
        query = query.filter(User.email.contains(keyword))
    if export:
        users = query.order_by(User.id.desc()).all()
        rows = [
            {"ID": u.id, "邮箱": u.email, "角色": "管理员" if getattr(u, "role", 0) == 1 else "普通用户"}
            for u in users
        ]
        return csv_response(rows, "users_export.csv")
    total = query.count()
    users = query.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    if export:
        rows = [
            {"ID": u.id, "邮箱": u.email, "角色": "管理员" if getattr(u, "role", 0) == 1 else "普通用户"}
            for u in users
        ]
        return csv_response(rows, f"users_{page}.csv")

    return {
        "code": 0,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": [
                {"id": u.id, "email": u.email, "role": getattr(u, "role", 0)}
                for u in users
            ],
        }
    }


@router_admin.post("/user")
def create_user(
    email: str,
    password: str,
    role: int = 0,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """新增用户"""
    import hashlib
    if db.query(User).filter(User.email == email).first():
        return {"code": 1, "message": "邮箱已存在"}
    user = User(
        email=email,
        password=hashlib.sha256(password.encode("utf-8")).hexdigest(),
        role=role,
    )
    db.add(user)
    db.commit()
    return {"code": 0, "message": "创建成功", "data": {"id": user.id}}


@router_admin.put("/user/{user_id}")
def update_user(
    user_id: int,
    email: Optional[str] = None,
    password: Optional[str] = None,
    role: Optional[int] = None,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """编辑用户"""
    import hashlib
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"code": 1, "message": "用户不存在"}
    if email is not None:
        user.email = email
    if password is not None and password.strip():
        user.password = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if role is not None:
        user.role = role
    db.commit()
    return {"code": 0, "message": "更新成功"}


@router_admin.delete("/user/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """删除用户（同时删除关联的舌诊记录、会话和聊天记录）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"code": 1, "message": "用户不存在"}
    # 级联删除
    for session in db.query(ChatSession).filter(ChatSession.user_id == user_id).all():
        db.query(ChatRecord).filter(ChatRecord.session_id == session.id).delete()
    db.query(ChatSession).filter(ChatSession.user_id == user_id).delete()
    db.query(TongueAnalysis).filter(TongueAnalysis.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"code": 0, "message": "删除成功"}


# ────────────────────────────────────────
#  舌诊记录管理
# ────────────────────────────────────────

@router_admin.get("/records")
def list_records(
    page: int = 1,
    page_size: int = 20,
    user_id: Optional[int] = None,
    state: Optional[int] = None,
    export: bool = False,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """舌诊记录列表（分页 + 筛选），export=1 时导出 CSV"""
    query = db.query(TongueAnalysis, User.email).join(User, TongueAnalysis.user_id == User.id)
    if user_id is not None:
        query = query.filter(TongueAnalysis.user_id == user_id)
    if state is not None:
        if state == 200:
            query = query.filter(TongueAnalysis.state >= 200)
        else:
            query = query.filter(TongueAnalysis.state == state)
    if export:
        records = query.order_by(TongueAnalysis.id.desc()).all()
        state_labels = {1: "成功", 200: "失败", 201: "失败", 202: "失败", 203: "失败"}
        color_labels = {0: "淡白舌", 1: "淡红舌", 2: "红舌", 3: "绛舌", 4: "青紫舌"}
        coating_labels = {0: "白苔", 1: "黄苔", 2: "灰黑苔"}
        thick_labels = {0: "薄", 1: "厚"}
        rot_labels = {0: "正常", 1: "腐腻"}
        rows = []
        for r in records:
            ta = r.TongueAnalysis
            st = state_labels.get(ta.state, str(ta.state))
            rows.append({
                "ID": ta.id,
                "用户邮箱": r.email,
                "状态": f"失败({ta.state})" if ta.state >= 200 else st,
                "舌色": color_labels.get(ta.tongue_color, ""),
                "苔色": coating_labels.get(ta.coating_color, ""),
                "舌体厚薄": thick_labels.get(ta.tongue_thickness, ""),
                "腐腻情况": rot_labels.get(ta.rot_greasy, ""),
            })
        return csv_response(rows, "tongue_records_export.csv")

    total = query.count()
    records = query.order_by(TongueAnalysis.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "code": 0,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": [
                {
                    "id": r.TongueAnalysis.id,
                    "user_id": r.TongueAnalysis.user_id,
                    "email": r.email,
                    "img_src": r.TongueAnalysis.img_src,
                    "state": r.TongueAnalysis.state,
                    "tongue_color": r.TongueAnalysis.tongue_color,
                    "coating_color": r.TongueAnalysis.coating_color,
                    "tongue_thickness": r.TongueAnalysis.tongue_thickness,
                    "rot_greasy": r.TongueAnalysis.rot_greasy,
                }
                for r in records
            ],
        }
    }


@router_admin.delete("/record/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """删除单条舌诊记录"""
    record = db.query(TongueAnalysis).filter(TongueAnalysis.id == record_id).first()
    if not record:
        return {"code": 1, "message": "记录不存在"}
    db.delete(record)
    db.commit()
    return {"code": 0, "message": "删除成功"}


# ────────────────────────────────────────
#  对话管理
# ────────────────────────────────────────

@router_admin.get("/chat-sessions")
def list_chat_sessions(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    user_id: int = None,
    export: bool = False,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """会话列表（分页 + 搜索 + 按用户筛选），export=1 时导出全部（忽略分页）"""
    query = db.query(ChatSession, User.email).join(User, ChatSession.user_id == User.id)
    if keyword:
        query = query.filter(
            User.email.contains(keyword) | ChatSession.tittle.contains(keyword)
        )
    if user_id is not None:
        query = query.filter(ChatSession.user_id == user_id)
    if export:
        sessions = query.order_by(ChatSession.id.desc()).all()
        rows = [
            {"ID": s.ChatSession.id, "用户邮箱": s.email, "会话标题": s.ChatSession.tittle}
            for s in sessions
        ]
        return csv_response(rows, "chat_sessions_export.csv")

    total = query.count()
    sessions = query.order_by(ChatSession.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "code": 0,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": [
                {
                    "id": s.ChatSession.id,
                    "user_id": s.ChatSession.user_id,
                    "email": s.email,
                    "title": s.ChatSession.tittle,
                }
                for s in sessions
            ],
        }
    }


@router_admin.get("/chat-session/{session_id}")
def get_chat_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """获取某条会话的完整对话记录"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        return {"code": 1, "message": "会话不存在"}
    records = (
        db.query(ChatRecord)
        .filter(ChatRecord.session_id == session_id)
        .order_by(ChatRecord.create_at.asc())
        .all()
    )
    role_map = {1: "user", 2: "assistant"}
    return {
        "code": 0,
        "data": {
            "session_id": session_id,
            "user_id": session.user_id,
            "title": session.tittle,
            "records": [
                {
                    "id": r.id,
                    "role": role_map.get(r.role, "unknown"),
                    "content": r.content,
                    "time": r.create_at,
                }
                for r in records
            ],
        }
    }


@router_admin.delete("/chat-session/{session_id}")
def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """删除会话及所有对话记录"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        return {"code": 1, "message": "会话不存在"}
    db.query(ChatRecord).filter(ChatRecord.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return {"code": 0, "message": "删除成功"}
