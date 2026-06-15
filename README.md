# 想法
- 本项目是结合codex从重想法到完成
- vibe coding完成
- pyoffer-agent-docs是我的想法结合codex生成的开发文档
# PyOffer Agent

PyOffer Agent is a web app for Python backend and AI Agent interview preparation.

This repository currently contains the backend MVP scaffold:

- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Redis
- Celery
- JWT auth

## Backend

```bash
cd backend
cp .env.example .env
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

Start Celery worker:

```bash
uv run celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

Run migrations:

```bash
uv run alembic upgrade head
```
