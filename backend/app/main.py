"""后端 API 的 FastAPI 应用入口。"""

from fastapi import FastAPI

from backend.app.api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.core.exceptions import register_exception_handlers


def create_app() -> FastAPI:
    # 把应用创建封装成函数，方便测试时构造独立实例。
    app = FastAPI(title=settings.app_name)
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        # 简单的存活检查接口，供 Docker 或部署探针使用。
        return {"status": "ok"}

    return app


app = create_app()
