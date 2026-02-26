from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import register_routes
from .orm.database import engine, Base
from .models import models

def create_app():
    # 初始化数据库表
    Base.metadata.create_all(bind=engine)
    
    app = FastAPI()
    # 前端开发环境端口可能会变化（比如 5173/5174/5175），这里统一放开常用本地端口
    origins = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        "http://127.0.0.1:5175",
        "http://localhost:5175",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_routes(app)
    return app
