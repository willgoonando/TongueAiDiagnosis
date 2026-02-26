"""认证与授权相关工具函数

本模块提供 JWT 相关的核心能力（类似 Java 中的 JwtUtil / SecurityConfig）：
- create_access_token：根据用户信息生成带过期时间的 JWT
- get_current_user：从请求头中的 Bearer Token 解出当前登录用户对象

注意：
- 这里只负责技术层面的“认证”，不包含任何业务逻辑
- 被 routes/user_api.py、routes/model_api.py 等模块通过 Depends 注入使用
"""

from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from typing import Optional, Annotated
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from ..config import settings
from ..orm.crud.auth_user import get_user
from ..orm.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHMS)
    return encoded_jwt

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHMS)
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(email=email, db=db)
    if user is None:
        raise credentials_exception
    return user
