"""路由聚合与注册模块

本模块负责将各个功能模块的 APIRouter 统一挂载到 FastAPI 应用上（类似 Java 中的 WebMvcConfig）：
- /api/user 对应 application.routes.user_api 中的 router_user
- /api/model 对应 application.routes.model_api 中的 router_tongue_analysis

create_app() 在 application/__init__.py 中会调用 register_routes(app) 完成注册。
"""

from .user_api import router_user
from .model_api import router_tongue_analysis
from .extra_api import router_extra
from .pipeline_api import router_pipeline
from .admin_api import router_admin
from .ollama_used import *

def register_routes(app):
    app.include_router(router_user, prefix="/api/user")
    app.include_router(router_tongue_analysis, prefix="/api/model")
    app.include_router(router_extra, prefix="/api/extra")
    app.include_router(router_pipeline, prefix="/api")
    app.include_router(router_admin, prefix="/api")
