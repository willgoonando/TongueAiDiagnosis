from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import register_routes
from .orm.database import engine, Base
from .models import models

def create_app():
    # 初始化数据库表
    Base.metadata.create_all(bind=engine)
    
    app = FastAPI()
    origins = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
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
