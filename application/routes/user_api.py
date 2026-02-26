"""用户相关 HTTP 接口（Controller 层）

本模块对应 Java 项目中的 UserController，职责是：
- 暴露 /api/user 下的接口：注册、登录、获取当前用户信息与历史舌诊记录
- 不写具体业务逻辑，全部委托给 application.services.user_service 中的函数

当前主要接口：
- POST /api/user/register   用户注册
- PUT  /api/user/login      用户登录，返回 JWT
- GET  /api/user/info       获取当前登录用户信息
- GET  /api/user/record     获取用户历史舌诊记录
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Annotated

from ..core import get_current_user
from ..models import schemas
from ..orm.database import get_db
from ..services import (
    register_user_service,
    login_user_service,
    get_user_info_service,
    get_user_record_service,
)


router_user = APIRouter()


@router_user.post('/register', response_model=schemas.RegisterResponse)
def register(schema: schemas.UserRegister, db: Session = Depends(get_db)):
    """
    用户注册接口（Controller 层）：
    - 参数校验由 Pydantic (schemas.UserRegister) 完成
    - 业务逻辑委托给 user_service
    """
    return register_user_service(schema=schema, db=db)


@router_user.put('/login', response_model=schemas.LoginResponse)
def login(
    form_data: Annotated[schemas.ExtendedOAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """
    用户登录接口：
    - 调用 user_service 完成校验和 token 生成
    """
    return login_user_service(form_data=form_data, db=db)


@router_user.get('/info', response_model=schemas.InfoResponse)
def info_get(user: schemas.UserBase = Depends(get_current_user)):
    """
    获取当前用户信息：
    - user 由依赖 get_current_user 注入
    """
    return get_user_info_service(user=user)


@router_user.get('/record', response_model=schemas.RecordResponse)
def record_get(
    user: schemas.UserBase = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取当前用户的历史舌诊记录。
    """
    return get_user_record_service(user=user, db=db)

