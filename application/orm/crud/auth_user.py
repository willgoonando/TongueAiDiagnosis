"""User 表相关的底层数据库操作（DAO）

本模块只做最基础的 CRUD，不包含业务流程判断，主要函数包括：
- register_user：插入新用户（带 SHA256 加密），若邮箱已存在返回 101
- login_user：校验邮箱 + 密码是否匹配，返回 0/101/102 作为状态码
- get_user：根据邮箱查询单个用户
- get_user_record：根据用户 ID 查询所有 TongueAnalysis 记录

这些函数会被 services/user_service.py 调用，组成完整的业务逻辑。
"""

import hashlib
from sqlalchemy.orm import Session
from ...models import models

def register_user(email: str, password: str, db: Session):
    password = hashlib.sha256(password.encode("utf-8")).hexdigest()  # SHA256加密
    user = models.User(
        email=email,
        password=password
    )  # 创建用户
    if db.query(models.User).filter(models.User.email == email).first():
        # 检查用户名是否存在
        return 101
    db.add(user)
    try:
        db.commit()
        return 0
    except Exception as error:
        db.rollback()
        print(error)
        return 102

def login_user(email: str, password: str, db: Session):
    password = hashlib.sha256(password.encode("utf-8")).hexdigest()  # SHA256加密
    user = db.query(models.User).filter(models.User.email == email).first()  # 检查用户是否存在
    if user:
        if user.password == password:
            return 0
        else:
            return 102  # 密码不匹配
    else:
        return 101  # 其他错误

def get_user(email: str, db: Session):
    return db.query(models.User).filter(models.User.email == email).first()


def authenticate_user(email: str, password: str, db: Session):
    password = hashlib.sha256(password.encode("utf-8")).hexdigest()
    user = get_user(email=email, db=db)
    print(user)
    if not user:
        return False
    if not user.user_password == password:
        return False
    return user

def get_user_record(ID: int, db: Session):
    return db.query(models.TongueAnalysis).filter(models.TongueAnalysis.user_id == ID).all()
