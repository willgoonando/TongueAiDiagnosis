"""数据库连接与 Session 管理

本模块相当于 Java 项目中的 DataSource / SessionFactory 配置，主要职责：
- 创建 SQLAlchemy 的 Engine 和 SessionLocal（连接到 SQLite AppDatabase.db）
- 提供 ReusableSession，重写 commit 以在出错时自动回滚
- 提供 get_db / get_db_object 便于在 FastAPI 中通过 Depends 注入 Session

所有 ORM 实体类都会继承这里的 Base。
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

class ReusableSession(Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def commit(self):
        try:
            super().commit()
        except Exception as e:
            self.rollback()
            raise e

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_object():
    return SessionLocal()

engine = create_engine('sqlite:///AppDatabase.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=ReusableSession)
Base = declarative_base()
