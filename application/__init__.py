from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routes import register_routes
from .orm.database import engine, Base
from .models import models
from .core import get_current_user
from .models import schemas
import os

# 请求频率限制缓存（用于 /api/get-token）
_token_request_cache = {}

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

    # 挂载 pipeline 中间结果静态文件
    pipeline_static_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend", "public", "pipeline"
    )
    if os.path.exists(pipeline_static_dir):
        app.mount("/pipeline", StaticFiles(directory=pipeline_static_dir), name="pipeline")

    # 添加兼容路由 /api/get-token（前端可能在使用）
    # 这个路由在未登录时返回友好响应，避免产生大量 401 错误日志
    # 添加简单的请求频率限制，减少不必要的请求
    @app.get("/api/get-token")
    def get_token(request: Request):
        """
        获取当前用户的 token（兼容旧版前端）
        注意：这个接口主要用于兼容，实际应该使用 /api/user/info 获取用户信息
        如果未登录，返回友好的提示（200 状态码），避免产生 401 错误日志
        添加了简单的请求频率限制（同一IP 5秒内只处理一次）
        """
        from fastapi import Request
        from typing import Optional
        import time
        
        # 简单的请求频率限制（同一IP 5秒内只处理一次）
        global _token_request_cache
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        if client_ip in _token_request_cache:
            last_request_time = _token_request_cache[client_ip]
            if current_time - last_request_time < 5:  # 5秒内只处理一次
                # 返回缓存响应，减少处理
                return {
                    "code": 401,
                    "message": "请先登录",
                    "data": None
                }
        
        _token_request_cache[client_ip] = current_time
        # 清理过期的缓存（保留最近1分钟的）
        _token_request_cache = {k: v for k, v in _token_request_cache.items() if current_time - v < 60}
        
        # 尝试从请求头获取 token
        try:
            if request:
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    token_str = auth_header.split(" ")[1]
                    # 尝试验证 token
                    try:
                        from .core.authentication import create_access_token
                        from .config import settings
                        from jose import jwt, JWTError
                        from .orm.database import get_db
                        from .orm.crud.auth_user import get_user
                        
                        # 手动验证 token
                        payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=settings.ALGORITHMS)
                        email: str = payload.get("email")
                        if email:
                            db = next(get_db())
                            user = get_user(email=email, db=db)
                            if user:
                                new_token = create_access_token(data={"sub": user.email})
                                return {
                                    "code": 0,
                                    "message": "success",
                                    "data": {
                                        "token": new_token
                                    }
                                }
                    except (JWTError, Exception):
                        pass
        except:
            pass
        
        # 未登录时返回友好提示（200 状态码，避免 401 错误）
        return {
            "code": 401,
            "message": "请先登录",
            "data": None
        }
    
    return app
