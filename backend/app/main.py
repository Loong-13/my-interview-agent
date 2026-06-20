"""后端 API 的 FastAPI 应用入口。"""
# ruff: noqa: E402

import sys
from pathlib import Path

from fastapi import FastAPI

# 兼容在 IDE 中直接运行 `python backend/app/main.py` 的场景。
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers


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


def run() -> None:
    """本地开发启动入口。"""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_env == "local",
        app_dir=str(project_root),
    )


if __name__ == "__main__":
    run()
