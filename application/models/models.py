"""ORM 实体模型定义

本模块定义了所有与数据库表一一对应的实体类（类似 Java 中的 @Entity）：
- User：用户表，包含 email、password 等
- TongueAnalysis：舌象分析记录表，保存图片路径与模型输出的四个特征
- ChatSession：对话会话表，记录每次诊断会话的基本信息
- ChatRecord：聊天记录表，保存用户与 AI 的每条对话内容

这些类都会继承自 application.orm.database.Base，由 SQLAlchemy 负责映射到 SQLite 数据库。
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..orm.database import Base


class User(Base):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True)  # 自增主键
    email = Column(String(255))
    password = Column(String(255))


class TongueAnalysis(Base):
    __tablename__ = 'TongueAnalysis'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('User.id'))
    img_src = Column(String(255))
    state = Column(Integer)
    tongue_color = Column(Integer)
    coating_color = Column(Integer)
    tongue_thickness = Column(Integer)
    rot_greasy = Column(Integer)
    user = relationship('User')


class ChatSession(Base):
    __tablename__ = "chatSession"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("User.id"))
    tittle = Column(String)
    user = relationship("User")
    chat_records = relationship("ChatRecord")


class ChatRecord(Base):
    __tablename__ = "chatRecord"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chatSession.id"))
    content = Column(String)
    create_at = Column(Integer, nullable=False)
    role = Column(Integer)
    session = relationship("ChatSession")
