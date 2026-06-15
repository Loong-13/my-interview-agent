# PyOffer Agent Backend

FastAPI backend scaffold for the PyOffer Agent MVP.

## Stack

- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Redis
- Celery
- JWT auth

## Setup

```bash
cp .env.example .env
uv sync --extra dev
```

## Run API

```bash
uv run uvicorn app.main:app --reload
```

Health check:

```bash
GET http://localhost:8000/health
```

## Run Celery Worker

On Windows local development:

```bash
uv run celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

On Linux:

```bash
uv run celery -A app.workers.celery_app worker --loglevel=info
```

## Database

Run migrations:

```bash
uv run alembic upgrade head
```

## uv Notes On Windows

If `uv run` fails with a cache path or trampoline permission error, use a project-local cache first:

```powershell
$env:UV_CACHE_DIR = ".uv-cache"
uv sync --extra dev
```

If `.venv\Scripts\python.exe` reports `uv trampoline failed to spawn Python child process`, recreate the virtual environment with an accessible Python interpreter:

```powershell
Remove-Item -Recurse -Force .venv
$env:UV_CACHE_DIR = ".uv-cache"
uv python install 3.12
uv sync --extra dev
```

## Current Scope

Implemented:

- Auth routes
- Project CRUD
- Resume upload and parse task
- JD create and analyze task placeholder
- Match report task placeholder
- Question generation task placeholder
- Text interview placeholder flow
- Interview report task placeholder
- Async task status API

The Agent implementations are intentionally stubbed. Replace task placeholders with real calls to:

- ResumeAgent
- JDAnalyzerAgent
- MatchAgent
- QuestionGeneratorAgent
- InterviewerAgent
- EvaluatorAgent
