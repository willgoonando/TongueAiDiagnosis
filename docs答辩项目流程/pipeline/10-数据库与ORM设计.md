# 10 — 数据库与 ORM 设计

## 数据库：SQLite

文件路径由 SQLAlchemy 引擎管理，默认在项目根目录。

## 表结构

### User 表 — 用户信息

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 自增主键 |
| email | String | 用户邮箱（登录名） |
| password | String | 哈希后的密码 |

### TongueAnalysis 表 — 舌诊分析记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 自增主键 |
| user_id | Integer (FK) | 关联 User |
| img_src | String | 图片保存路径 |
| state | Integer | 0=处理中, 1=完成, 201/202/203=错误码 |
| tongue_color | Integer | 舌色分类结果 (0-4) |
| coating_color | Integer | 苔色分类结果 (0-2) |
| tongue_thickness | Integer | 厚薄分类结果 (0-1) |
| rot_greasy | Integer | 腐腻分类结果 (0-1) |
| create_at | DateTime | 创建时间 |

## ORM 层目录

```
application/orm/
├── database.py           # SQLAlchemy 引擎 + Session 管理
├── crud/
│   ├── auth_user.py      # User 表的 CRUD
│   └── tongue_analysis.py # TongueAnalysis 表的 CRUD
```

### `tongue_analysis.py` 关键操作

```python
def create_record(db, user_id, img_src):
    """创建新记录，state=0"""
    record = TongueAnalysis(
        user_id=user_id,
        img_src=img_src,
        state=0
    )
    db.add(record)
    db.commit()
    return record.id

def update_record(db, record_id, tongue_color, coating_color, 
                  tongue_thickness, rot_greasy, state):
    """推理完成后更新结果"""
    record = db.query(TongueAnalysis).filter_by(id=record_id).first()
    record.tongue_color = tongue_color
    record.coating_color = coating_color
    record.tongue_thickness = tongue_thickness
    record.rot_greasy = rot_greasy
    record.state = state
    db.commit()

def get_record(db, record_id):
    """查询单条记录"""
    return db.query(TongueAnalysis).filter_by(id=record_id).first()

def get_user_records(db, user_id):
    """查询用户的所有记录"""
    return db.query(TongueAnalysis).filter_by(user_id=user_id).all()
```

## SQLAlchemy ORM 模型

```python
# models.py
class TongueAnalysis(Base):
    __tablename__ = 'tongue_analysis'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    img_src = Column(String(255))
    state = Column(Integer, default=0)  # 0: 处理中, 1: 完成
    tongue_color = Column(Integer, nullable=True)
    coating_color = Column(Integer, nullable=True)
    tongue_thickness = Column(Integer, nullable=True)
    rot_greasy = Column(Integer, nullable=True)
    create_at = Column(DateTime, default=datetime.utcnow)
```

## 设计亮点

1. **状态机设计**：state 字段标识推理进度（0→1），Service 层轮询等待
2. **FK 关联**：通过 user_id 关联用户和分析记录
3. **ORM 分离**：CRUD 操作独立成模块，Service 层不直接写 SQL
4. **分层清晰**：Controller → Service → ORM → Database
